from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # LLM
    groq_api_key: str

    # Neo4j
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str

    # ChromaDB
    chroma_persist_dir: str = "./data/chromadb"

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    backend_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
