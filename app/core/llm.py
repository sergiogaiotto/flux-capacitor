"""Wrapper de acesso à LLM (OpenAI) via LangChain."""
from functools import lru_cache
from langchain_openai import ChatOpenAI
from app.config import settings


@lru_cache
def get_llm(temperature: float | None = None) -> ChatOpenAI:
    """Retorna cliente ChatOpenAI configurado."""
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=temperature if temperature is not None else settings.OPENAI_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY,
        timeout=60,
        max_retries=2,
    )
