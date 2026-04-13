"""Integração com LangFuse para observabilidade."""
from typing import Optional
from functools import lru_cache
from app.config import settings

try:
    from langfuse import Langfuse
    from langfuse.callback import CallbackHandler
    _LANGFUSE_AVAILABLE = True
except Exception:  # pragma: no cover
    Langfuse = None  # type: ignore
    CallbackHandler = None  # type: ignore
    _LANGFUSE_AVAILABLE = False


@lru_cache
def get_langfuse() -> Optional["Langfuse"]:
    if not settings.LANGFUSE_ENABLED or not _LANGFUSE_AVAILABLE:
        return None
    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        return None
    return Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
    )


def get_langfuse_callback(
    trace_name: str = "flux-capacitor",
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Optional["CallbackHandler"]:
    """Retorna callback handler para LangChain/LangGraph."""
    if not settings.LANGFUSE_ENABLED or not _LANGFUSE_AVAILABLE:
        return None
    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        return None
    return CallbackHandler(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
        trace_name=trace_name,
        session_id=session_id,
        user_id=user_id,
        metadata=metadata or {},
    )
