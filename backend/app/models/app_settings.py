"""App Settings model for storing user preferences."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.types import UUIDType


class AppSettings(Base):
    """Stores app-wide settings like LLM provider choice."""

    __tablename__ = "app_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )

    # LLM Provider settings
    llm_provider: Mapped[str] = mapped_column(
        String(50), default="ollama"  # "ollama" or "openai"
    )

    # Ollama settings
    ollama_model: Mapped[str] = mapped_column(
        String(100), default="llama3.2"
    )
    ollama_base_url: Mapped[str] = mapped_column(
        String(255), default="http://localhost:11434/v1"
    )

    # OpenAI settings (API key stored encrypted in production)
    openai_api_key: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    openai_model: Mapped[str] = mapped_column(
        String(100), default="gpt-4o"
    )

    # Setup status
    setup_completed: Mapped[bool] = mapped_column(
        Boolean, default=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
