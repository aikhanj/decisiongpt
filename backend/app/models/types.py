"""Cross-database compatible type definitions.

This module provides type aliases that work with both PostgreSQL and SQLite.
"""

import uuid
from typing import Any

from sqlalchemy import String, Text, TypeDecorator
from sqlalchemy.types import JSON

from app.config import get_settings


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses String(36) for SQLite and UUID for PostgreSQL.
    Stores UUID as string in SQLite, native UUID in PostgreSQL.
    """

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
        return value


def get_uuid_type():
    """Get the appropriate UUID type based on database configuration."""
    settings = get_settings()
    if settings.database_type == "sqlite":
        return GUID()
    else:
        from sqlalchemy.dialects.postgresql import UUID
        return UUID(as_uuid=True)


def get_json_type():
    """Get the appropriate JSON type based on database configuration."""
    settings = get_settings()
    if settings.database_type == "sqlite":
        return JSON()
    else:
        from sqlalchemy.dialects.postgresql import JSONB
        return JSONB()


# Type aliases for use in models
# These will be resolved at import time based on config
_settings = get_settings()

if _settings.database_type == "sqlite":
    # SQLite-compatible types
    UUIDType = GUID()
    JSONType = JSON()
else:
    # PostgreSQL types
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
    UUIDType = PG_UUID(as_uuid=True)
    JSONType = JSONB()
