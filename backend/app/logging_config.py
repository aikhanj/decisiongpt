"""Centralized logging configuration for DecisionGPT."""

import logging
import sys
from datetime import datetime
from typing import Optional


# Global flag to track if logging is configured
_logging_configured = False


class ReadableFormatter(logging.Formatter):
    """Custom formatter with clean, readable output for console."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name if outputting to terminal
        if sys.stdout.isatty():
            levelname = (
                f"{self.COLORS.get(record.levelname, '')}"
                f"{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        else:
            levelname = record.levelname

        # Format: [TIMESTAMP] [LEVEL] [logger] message
        timestamp = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        base_message = (
            f"[{timestamp}] [{levelname}] [{record.name}] {record.getMessage()}"
        )

        # Add exception if present
        if record.exc_info:
            base_message += f"\n{self.formatException(record.exc_info)}"

        return base_message


def setup_logging():
    """
    Configure logging for the entire application.

    Reads settings from environment and sets up console handler with
    appropriate log level and formatting.
    """
    global _logging_configured

    if _logging_configured:
        return

    # Import here to avoid circular dependency
    from app.config import get_settings

    settings = get_settings()

    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(ReadableFormatter())
    root_logger.addHandler(console_handler)

    # Silence noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    _logging_configured = True

    logging.info(
        f"Logging configured - Level: {settings.log_level.upper()}, "
        f"AI Debug: {settings.ai_debug_logging}"
    )


def sanitize_api_key(api_key: Optional[str]) -> str:
    """
    Redact API key for logging.

    Shows only first 4 and last 4 characters for security.

    Args:
        api_key: The API key to sanitize

    Returns:
        Sanitized key like "sk-pr...xyz9" or "***NONE***"

    Examples:
        >>> sanitize_api_key("sk-proj1234567890abcdef")
        'sk-pr...cdef'
        >>> sanitize_api_key("ollama")
        '***NONE***'
        >>> sanitize_api_key(None)
        '***NONE***'
    """
    if not api_key or api_key == "ollama":
        return "***NONE***"
    if len(api_key) <= 8:
        return "***"
    return f"{api_key[:5]}...{api_key[-4:]}"


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Truncate text for logging with length indicator.

    Args:
        text: The text to truncate
        max_length: Maximum length before truncation (default 200)

    Returns:
        Original text if short enough, or truncated with indicator

    Examples:
        >>> truncate_text("Short text", 200)
        'Short text'
        >>> truncate_text("A" * 300, 200)
        'AAA... [truncated, total: 300 chars]'
    """
    if len(text) <= max_length:
        return text
    return f"{text[:max_length]}... [truncated, total: {len(text)} chars]"
