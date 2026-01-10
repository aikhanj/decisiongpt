from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database Configuration
    database_type: str = "sqlite"  # "postgresql" or "sqlite"
    database_url: str = "postgresql+asyncpg://gentleman:gentleman_secret@localhost:5432/gentleman_coach"
    sqlite_path: str = "./data/decisiongpt.db"

    # LLM Provider Configuration
    llm_provider: str = "ollama"  # "openai" or "ollama"

    # OpenAI Configuration (for cloud/BYOK mode)
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-ada-002"

    # Ollama Configuration (for local/offline mode)
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.2"
    ollama_embedding_model: str = "nomic-embed-text"

    # Feature Flags
    use_vector_memory: bool = False

    # CORS
    cors_origins: str = "http://localhost:3000"

    # App Settings
    default_user_id: str = "00000000-0000-0000-0000-000000000001"
    policy_version: str = "v1.0"

    # Redis / Celery Configuration (optional - for web deployment)
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    task_timeout_seconds: int = 300  # 5 minutes max for AI tasks

    # Desktop Mode
    desktop_mode: bool = False  # Set to True for desktop app deployment

    # AI Debug Logging
    ai_debug_logging: bool = False  # Enable detailed AI request/response logging
    log_level: str = "INFO"  # Logging level: DEBUG, INFO, WARNING, ERROR

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def effective_database_url(self) -> str:
        """Return the appropriate database URL based on database_type."""
        if self.database_type == "sqlite":
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
