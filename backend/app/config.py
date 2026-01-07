from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://gentleman:gentleman_secret@localhost:5432/gentleman_coach"

    # OpenAI Configuration (model names only - API key provided by user via BYOK)
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-ada-002"

    # Feature Flags
    use_vector_memory: bool = False

    # CORS
    cors_origins: str = "http://localhost:3000"

    # App Settings
    default_user_id: str = "00000000-0000-0000-0000-000000000001"
    policy_version: str = "v1.0"

    # Redis / Celery Configuration
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    task_timeout_seconds: int = 300  # 5 minutes max for AI tasks

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
