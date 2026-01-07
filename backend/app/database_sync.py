"""Synchronous database utilities for Celery workers.

Celery workers run synchronously, so we need sync versions of database access.
This module provides utilities for creating sync database sessions.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()


def get_sync_db_url(async_url: str) -> str:
    """Convert async database URL to sync.

    Converts postgresql+asyncpg:// to postgresql://
    """
    return async_url.replace("postgresql+asyncpg://", "postgresql://")


# Create sync engine (lazy initialization)
_sync_engine = None
_SyncSessionLocal = None


def get_sync_engine():
    """Get or create the synchronous database engine."""
    global _sync_engine
    if _sync_engine is None:
        sync_url = get_sync_db_url(settings.database_url)
        _sync_engine = create_engine(
            sync_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _sync_engine


def get_sync_session_factory():
    """Get or create the synchronous session factory."""
    global _SyncSessionLocal
    if _SyncSessionLocal is None:
        _SyncSessionLocal = sessionmaker(
            bind=get_sync_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SyncSessionLocal


@contextmanager
def get_sync_db() -> Generator[Session, None, None]:
    """Context manager that provides a synchronous database session.

    Usage:
        with get_sync_db() as db:
            task = db.query(BackgroundTask).filter(...).first()
    """
    SessionLocal = get_sync_session_factory()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_sync_session() -> Session:
    """Create a new synchronous database session.

    Remember to close it manually when done.

    Usage:
        session = create_sync_session()
        try:
            # ... do work
            session.commit()
        finally:
            session.close()
    """
    SessionLocal = get_sync_session_factory()
    return SessionLocal()
