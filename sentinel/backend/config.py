from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

# Resolve .env path relative to THIS file's location (backend/), then go up one level to sentinel/
_ENV_PATH = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    # LLM (required — app cannot function without it)
    groq_api_key: str

    # Neo4j (optional — graph_db.py falls back to in-memory mode when missing)
    neo4j_uri: Optional[str] = None
    neo4j_username: Optional[str] = None
    neo4j_password: Optional[str] = None

    # ChromaDB
    chroma_persist_dir: str = "./data/chromadb"

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    backend_url: str = "http://localhost:8000"

    class Config:
        env_file = str(_ENV_PATH)
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    try:
        return Settings()
    except Exception as e:
        if "groq_api_key" in str(e).lower():
            raise EnvironmentError(
                "GROQ_API_KEY not found. "
                f"Copy sentinel/.env.example to sentinel/.env and fill in your Groq API key.\n"
                f"Expected .env location: {_ENV_PATH}\n"
                f"Original error: {e}"
            )
        raise
