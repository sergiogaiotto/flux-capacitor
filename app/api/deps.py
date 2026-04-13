"""Dependências compartilhadas FastAPI - auth por API key + session DB."""
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database.connection import AsyncSessionLocal
from app.database import repository as repo


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as s:
        yield s


async def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> str:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key obrigatória no header X-API-Key",
        )
    if not await repo.is_api_key_valid(db, x_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="API key inválida"
        )
    return x_api_key
