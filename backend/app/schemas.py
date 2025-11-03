"""Pydantic schemas for API request/response validation"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ============ Auth Schemas ============

class TokenRequest(BaseModel):
    """Request to generate JWT token"""
    user_id: str = Field(..., min_length=1, max_length=100)


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


# ============ Article Schemas ============

class ArticleListItem(BaseModel):
    """Article list item (summary view)"""
    id: int
    title: str
    summary: Optional[str] = None
    author: Optional[str] = None
    source_name: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    published_at: datetime

    class Config:
        from_attributes = True


class ArticleDetail(BaseModel):
    """Article detail (full view)"""
    id: int
    title: str
    summary: Optional[str] = None
    author: Optional[str] = None
    source_name: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    published_at: datetime
    content_url: Optional[str] = None
    content_text_excerpt: Optional[str] = None
    ai_analysis: Optional[dict] = None

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    """Paginated article list response"""
    data: List[ArticleListItem]
    pagination: dict  # {total, page, page_size}


# ============ Search Schemas ============

class SearchRequest(BaseModel):
    """Search request"""
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[dict] = None
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    """Search result item"""
    id: int
    article_id: int
    title: str
    snippet: str
    score: float
    published_at: datetime


class SearchResponse(BaseModel):
    """Search results response"""
    results: List[SearchResultItem]
    total: int


# ============ Chat Schemas ============

class ChatRequest(BaseModel):
    """Chat request"""
    question: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[UUID] = None


class ChatSource(BaseModel):
    """Source reference in chat response"""
    id: int
    article_id: int
    title: str
    published_at: datetime
    source_name: str
    url: str
    chunk_index: int
    snippet: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response with sources"""
    conversation_id: UUID
    answer: str
    sources: List[ChatSource]
    latency_ms: Optional[int] = None


# ============ Internal Schemas ============

class AIAnalysisResult(BaseModel):
    """AI analysis result (internal use)"""
    summary: str
    key_points: List[str]
    entities: dict  # {drugs: [], diseases: [], companies: []}


# ============ Admin Schemas ============

class ArticleListQuery(BaseModel):
    """Article list query parameters"""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Page size")
    keyword: Optional[str] = Field(None, description="Search keyword")
    category: Optional[str] = Field(None, description="Category filter")
    content_source: Optional[str] = Field(None, description="Content source: pharnexcloud/wechat")
    from_date: Optional[str] = Field(None, description="From date YYYY-MM-DD")
    to_date: Optional[str] = Field(None, description="To date YYYY-MM-DD")


class ArticleResponse(BaseModel):
    """Article response model"""
    id: int
    title: str
    summary: Optional[str]
    author: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    published_at: datetime
    crawled_at: datetime
    content_source: str
    content_url: Optional[str]
    original_source_url: Optional[str]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArticleDetailResponse(ArticleResponse):
    """Article detail response with full content"""
    content_text: Optional[str]
    wechat_content_text: Optional[str]


class ArticleUpdateRequest(BaseModel):
    """Article update request"""
    title: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class BatchDeleteRequest(BaseModel):
    """Batch delete request"""
    article_ids: List[int] = Field(..., description="Article ID list")


class CrawlerConfigRequest(BaseModel):
    """Crawler config request"""
    pages: int = Field(10, ge=1, le=100, description="Pages to crawl")
    max_articles: Optional[int] = Field(None, ge=1, description="Max articles")
    days_back: Optional[int] = Field(None, ge=1, description="Recent N days")
    from_date: Optional[str] = Field(None, description="From date YYYY-MM-DD")
    to_date: Optional[str] = Field(None, description="To date YYYY-MM-DD")


class CrawlerTaskResponse(BaseModel):
    """Crawler task response"""
    id: int
    config: dict
    status: str
    articles_count: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CrawlerStatusResponse(BaseModel):
    """Crawler status response"""
    is_running: bool
    current_task: Optional[CrawlerTaskResponse]
    progress: Optional[dict]


class OverviewStats(BaseModel):
    """Overview statistics"""
    total_articles: int
    today_articles: int
    week_articles: int
    month_articles: int
    wechat_articles: int
    pharnex_articles: int


class ArticleTrendItem(BaseModel):
    """Article trend item"""
    date: str
    count: int


class SourceDistributionItem(BaseModel):
    """Source distribution item"""
    source: str
    count: int
    percentage: float


class CategoryDistributionItem(BaseModel):
    """Category distribution item"""
    category: str
    count: int
