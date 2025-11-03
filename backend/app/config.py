"""Application configuration management"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/medical_news"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO / S3
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_RAW: str = "medical-news-raw"
    S3_BUCKET_CLEAN: str = "medical-news-clean"
    S3_BUCKET_ATTACHMENTS: str = "medical-news-attachments"

    # OpenAI
    OPENAI_API_KEY: str

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Rate Limiting
    RATE_LIMIT_CHAT: int = 10
    RATE_LIMIT_SEARCH: int = 60
    RATE_LIMIT_ARTICLES: int = 60

    # Environment
    ENVIRONMENT: str = "development"

    # Cleanup
    CLEANUP_DELETED_AFTER_DAYS: int = 30  # 物理删除软删除文章的天数阈值

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string to list"""
        return [origin.strip() for origin in self.API_CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
