"""Rotas de estatísticas / observabilidade."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_api_key
from app.database import repository as repo

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
async def stats(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    return await repo.interaction_stats(db, days=days)
