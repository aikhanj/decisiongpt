#!/usr/bin/env python3
"""
Entry point for Decision Canvas desktop backend.

This script starts the FastAPI backend in desktop mode with:
- SQLite database
- Ollama as default LLM provider
- No Celery/Redis dependencies
"""

import os
import sys

# Set desktop mode environment variables if not already set
os.environ.setdefault("DATABASE_TYPE", "sqlite")
os.environ.setdefault("LLM_PROVIDER", "ollama")
os.environ.setdefault("DESKTOP_MODE", "true")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000,tauri://localhost,http://127.0.0.1:3000")

# Default SQLite path if not specified
if "SQLITE_PATH" not in os.environ:
    # Use app data directory or current directory
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        data_dir = os.path.join(app_data, "DecisionCanvas", "data")
    else:
        data_dir = os.path.expanduser("~/.decisioncanvas/data")

    os.makedirs(data_dir, exist_ok=True)
    os.environ["SQLITE_PATH"] = os.path.join(data_dir, "decisiongpt.db")

print(f"Decision Canvas Desktop Backend")
print(f"================================")
print(f"Database: {os.environ.get('SQLITE_PATH')}")
print(f"LLM Provider: {os.environ.get('LLM_PROVIDER')}")
print(f"Desktop Mode: {os.environ.get('DESKTOP_MODE')}")
print()

# Start the server
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False,  # No reload in production
    )
