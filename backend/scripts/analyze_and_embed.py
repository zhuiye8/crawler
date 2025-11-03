"""AI analysis and embedding generation for articles"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from openai import AsyncOpenAI
from app.database import get_db_context
from app.models import Article, ArticleAIOutput, ArticleChunk
from app.utils.text_splitter import split_text
from app.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def analyze_article(article: Article) -> dict:
    """Generate AI analysis for article"""
    prompt = f"""你是一名熟悉医药行业的资深分析师。请分析以下文章并输出JSON格式结果。

【要求】
1. 用简体中文
2. 仅提取关键信息，不要臆测

【输出JSON】
{{
  "summary": "200字以内的摘要",
  "key_points": ["要点1", "要点2", "要点3"],
  "entities": {{
    "drugs": ["药物名称1", "药物名称2"],
    "diseases": ["疾病名称1"],
    "companies": ["公司名称1"]
  }}
}}

【文章】
标题：{article.title}
正文：{article.content_text[:3000]}
"""

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    content = response.choices[0].message.content
    # Extract JSON from response
    try:
        result = json.loads(content)
    except:
        # Try to extract JSON from markdown code block
        import re
        json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(1))
        else:
            result = {"summary": content[:200], "key_points": [], "entities": {}}

    return result


async def generate_embedding(text: str) -> list:
    """Generate embedding vector for text"""
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


async def process_article(article: Article, db):
    """Process single article: AI analysis + embedding"""
    try:
        print(f"\n🤖 Processing: {article.title}")

        # AI analysis
        ai_result = await analyze_article(article)

        ai_output = ArticleAIOutput(
            article_id=article.id,
            version_no=article.version_no,
            summary=ai_result.get("summary", ""),
            key_points=ai_result.get("key_points", []),
            entities=ai_result.get("entities", {}),
            model_name="gpt-4"
        )
        db.add(ai_output)
        await db.flush()

        # Text splitting
        chunks = split_text(article.content_text, chunk_size=300, overlap=50)
        print(f"  ✂️  Split into {len(chunks)} chunks")

        # Generate embeddings
        for idx, chunk_text in enumerate(chunks):
            print(f"  📊 Embedding chunk {idx+1}/{len(chunks)}")
            embedding = await generate_embedding(chunk_text)

            chunk = ArticleChunk(
                article_id=article.id,
                chunk_index=idx,
                chunk_text=chunk_text,
                embedding=embedding,
                chunk_metadata={
                    "title": article.title,
                    "published_at": str(article.published_at),
                    "category": article.category,
                    "tags": article.tags or []
                }
            )
            db.add(chunk)

        await db.commit()
        print(f"  ✅ Completed")

    except Exception as e:
        print(f"  ❌ Error: {e}")
        await db.rollback()


async def main():
    """Main function"""
    print("🚀 Starting AI analysis and embedding...")

    async with get_db_context() as db:
        # Find articles without AI analysis
        subq = select(ArticleAIOutput.article_id)
        result = await db.execute(
            select(Article)
            .where(~Article.id.in_(subq))
            .limit(100)
        )
        articles = result.scalars().all()

        print(f"📚 Found {len(articles)} articles to process")

        for article in articles:
            await process_article(article, db)
            await asyncio.sleep(1)  # Rate limiting

    print("\n🎉 AI analysis and embedding completed!")


if __name__ == "__main__":
    asyncio.run(main())
