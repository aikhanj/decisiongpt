import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.config import get_settings

settings = get_settings()


def _create_engine():
    """Create database engine based on configuration."""
    db_url = settings.effective_database_url

    if settings.database_type == "sqlite":
        # Ensure data directory exists for SQLite
        sqlite_dir = os.path.dirname(settings.sqlite_path)
        if sqlite_dir and not os.path.exists(sqlite_dir):
            os.makedirs(sqlite_dir, exist_ok=True)

        # SQLite-specific configuration
        return create_async_engine(
            db_url,
            echo=False,
            # SQLite requires special handling for async
            connect_args={"check_same_thread": False},
            # Use StaticPool for SQLite to avoid connection issues
            poolclass=StaticPool,
        )
    else:
        # PostgreSQL configuration
        return create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
        )


engine = _create_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def get_db() -> AsyncSession:
    """Dependency that provides a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables (for SQLite/desktop mode)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
