"""Database initialization script"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine
from app.config import settings


SQL_STATEMENTS = [
    # Create additional indexes
    "CREATE INDEX IF NOT EXISTS idx_articles_published_desc ON articles(published_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_articles_source_category ON articles(source_id, category);",
    "CREATE INDEX IF NOT EXISTS idx_articles_tags_gin ON articles USING GIN(tags);",
    "CREATE INDEX IF NOT EXISTS idx_article_chunks_article ON article_chunks(article_id);",
    "CREATE INDEX IF NOT EXISTS idx_article_chunks_embedding_hnsw ON article_chunks USING hnsw (embedding vector_cosine_ops);",
    "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at DESC);",
    # Insert initial data
    "INSERT INTO sources (name, name_en, base_url) VALUES ('药渡云', 'PharnexCloud', 'https://www.pharnexcloud.com') ON CONFLICT DO NOTHING;",
]


async def init_database():
    """Initialize database: create tables, indexes, and seed data"""
    print("🚀 Initializing database...")

    async with engine.begin() as conn:
        # Step 1: Install pgvector extension FIRST
        print("🔧 Installing pgvector extension...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        # Step 2: Import models and create tables
        from app.models import Base

        print("📋 Creating tables...")
        await conn.run_sync(Base.metadata.create_all)

        # Step 3: Create additional indexes and insert initial data
        print("🔧 Creating additional indexes and inserting initial data...")
        for sql_statement in SQL_STATEMENTS:
            await conn.execute(text(sql_statement))

    print("✅ Database initialization completed!")


async def drop_all_tables():
    """Drop all tables (use with caution!)"""
    confirm = input("⚠️  This will DROP ALL TABLES. Type 'yes' to confirm: ")
    if confirm.lower() != 'yes':
        print("❌ Aborted")
        return

    print("🗑️  Dropping all tables...")
    async with engine.begin() as conn:
        from app.models import Base
        await conn.run_sync(Base.metadata.drop_all)
    print("✅ All tables dropped")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        asyncio.run(drop_all_tables())
    else:
        asyncio.run(init_database())
