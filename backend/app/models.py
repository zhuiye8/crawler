"""SQLAlchemy database models"""

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from app.database import Base
import uuid


class Source(Base):
    """Data source table (e.g., 药渡云, 药智网)"""

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    name_en = Column(String(100))
    base_url = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.now())


class Article(Base):
    """文章主表"""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)  # 文章标题
    summary = Column(Text)  # 文章摘要
    author = Column(String(200))  # 作者/公众号名称
    source_id = Column(Integer, ForeignKey("sources.id"))  # 数据源ID（如：药渡云）
    category = Column(String(100))  # 分类
    tags = Column(JSONB)  # 标签数组
    published_at = Column(TIMESTAMP, nullable=False, index=True)  # 发布时间
    crawled_at = Column(TIMESTAMP, server_default=func.now())  # 爬取时间

    # 内容字段
    content_url = Column(Text)  # 药渡云等平台的文章URL
    content_text = Column(Text)  # 文章纯文本内容
    content_source = Column(String(50), default="pharnexcloud")  # 内容来源标记：pharnexcloud/wechat

    # 微信公众号相关字段（新增）
    original_source_url = Column(Text)  # 微信公众号原文链接
    wechat_content_html = Column(Text)  # 微信文章完整HTML内容（如果爬取成功）
    wechat_content_text = Column(Text)  # 微信文章完整纯文本（如果爬取成功）

    # 系统字段
    canonical_hash = Column(String(64), unique=True, nullable=False, index=True)  # 内容去重哈希
    version_no = Column(Integer, default=1)  # 版本号
    is_deleted = Column(Boolean, default=False)  # 逻辑删除标记
    lang = Column(String(10), default="zh")  # 语言
    created_at = Column(TIMESTAMP, server_default=func.now())  # 创建时间
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())  # 更新时间


class ArticleAIOutput(Base):
    """AI analysis results for articles"""

    __tablename__ = "article_ai_outputs"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    version_no = Column(Integer, nullable=False)
    summary = Column(Text)
    key_points = Column(JSONB)
    entities = Column(JSONB)  # {drugs: [], diseases: [], companies: []}
    model_name = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())


class ArticleChunk(Base):
    """Article chunks with embeddings for vector search"""

    __tablename__ = "article_chunks"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(1536))  # OpenAI text-embedding-3-small dimension
    chunk_metadata = Column(JSONB)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word
    created_at = Column(TIMESTAMP, server_default=func.now())


class ChatSession(Base):
    """Chat session table for multi-turn conversations"""

    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class ChatMessage(Base):
    """Chat message table"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    sources = Column(JSONB)  # Referenced article IDs and chunk indexes
    latency_ms = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)


class CrawlerTask(Base):
    """爬虫任务表"""

    __tablename__ = "crawler_tasks"

    id = Column(Integer, primary_key=True, index=True)
    config = Column(JSONB, nullable=False)  # 爬取配置（pages, max_articles, dates等）
    status = Column(String(20), nullable=False, index=True)  # pending/running/completed/failed
    articles_count = Column(Integer, default=0)  # 爬取文章数
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    error_message = Column(Text)  # 错误信息
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
