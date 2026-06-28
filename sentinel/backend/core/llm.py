from functools import lru_cache
from langchain_groq import ChatGroq
from backend.config import get_settings

@lru_cache()
def get_llm(temperature: float = 0.1) -> ChatGroq:
    settings = get_settings()
    return ChatGroq(
        api_key=settings.groq_api_key,
        model="llama-3.3-70b-versatile",
        temperature=temperature,
    )
