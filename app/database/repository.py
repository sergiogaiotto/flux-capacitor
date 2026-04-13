"""Módulo específico de consultas ao SQLite.

Concentra TODO acesso a dados (interações, apresentações, slides, métricas).
"""
from datetime import datetime, timedelta
from typing import Iterable, Optional
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Presentation, Slide, Interaction, ApiKey


# ---------- Presentations ----------
async def create_presentation(session: AsyncSession, **data) -> Presentation:
    p = Presentation(**data)
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


async def get_presentation(session: AsyncSession, presentation_id: str) -> Optional[Presentation]:
    result = await session.execute(
        select(Presentation).where(Presentation.id == presentation_id)
    )
    return result.scalar_one_or_none()


async def list_presentations(session: AsyncSession, limit: int = 50) -> list[Presentation]:
    result = await session.execute(
        select(Presentation).order_by(Presentation.updated_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def update_presentation(session: AsyncSession, presentation_id: str, **data) -> Optional[Presentation]:
    p = await get_presentation(session, presentation_id)
    if not p:
        return None
    for k, v in data.items():
        if hasattr(p, k) and v is not None:
            setattr(p, k, v)
    await session.commit()
    await session.refresh(p)
    return p


async def delete_presentation(session: AsyncSession, presentation_id: str) -> bool:
    p = await get_presentation(session, presentation_id)
    if not p:
        return False
    await session.delete(p)
    await session.commit()
    return True


# ---------- Slides ----------
async def bulk_create_slides(session: AsyncSession, presentation_id: str, slides: Iterable[dict]) -> list[Slide]:
    objs = [Slide(presentation_id=presentation_id, **s) for s in slides]
    session.add_all(objs)
    await session.commit()
    for o in objs:
        await session.refresh(o)
    return objs


async def get_slide(session: AsyncSession, slide_id: str) -> Optional[Slide]:
    r = await session.execute(select(Slide).where(Slide.id == slide_id))
    return r.scalar_one_or_none()


async def list_slides(session: AsyncSession, presentation_id: str) -> list[Slide]:
    r = await session.execute(
        select(Slide)
        .where(Slide.presentation_id == presentation_id)
        .order_by(Slide.order_index)
    )
    return list(r.scalars().all())


async def update_slide(session: AsyncSession, slide_id: str, **data) -> Optional[Slide]:
    s = await get_slide(session, slide_id)
    if not s:
        return None
    for k, v in data.items():
        if hasattr(s, k) and v is not None:
            setattr(s, k, v)
    await session.commit()
    await session.refresh(s)
    return s


async def delete_slide(session: AsyncSession, slide_id: str) -> bool:
    s = await get_slide(session, slide_id)
    if not s:
        return False
    await session.delete(s)
    await session.commit()
    return True


async def reorder_slides(session: AsyncSession, presentation_id: str, ordered_ids: list[str]) -> list[Slide]:
    for idx, sid in enumerate(ordered_ids):
        s = await get_slide(session, sid)
        if s and s.presentation_id == presentation_id:
            s.order_index = idx
    await session.commit()
    return await list_slides(session, presentation_id)


# ---------- Interactions ----------
async def log_interaction(session: AsyncSession, **data) -> Interaction:
    i = Interaction(**data)
    session.add(i)
    await session.commit()
    await session.refresh(i)
    return i


async def list_interactions(
    session: AsyncSession,
    presentation_id: Optional[str] = None,
    kind: Optional[str] = None,
    limit: int = 100,
) -> list[Interaction]:
    q = select(Interaction)
    if presentation_id:
        q = q.where(Interaction.presentation_id == presentation_id)
    if kind:
        q = q.where(Interaction.kind == kind)
    q = q.order_by(Interaction.created_at.desc()).limit(limit)
    r = await session.execute(q)
    return list(r.scalars().all())


async def interaction_stats(session: AsyncSession, days: int = 7) -> dict:
    since = datetime.utcnow() - timedelta(days=days)
    q = (
        select(
            Interaction.kind,
            func.count(Interaction.id),
            func.coalesce(func.sum(Interaction.tokens_in), 0),
            func.coalesce(func.sum(Interaction.tokens_out), 0),
            func.coalesce(func.avg(Interaction.latency_ms), 0),
        )
        .where(Interaction.created_at >= since)
        .group_by(Interaction.kind)
    )
    r = await session.execute(q)
    rows = r.all()
    return {
        "since": since.isoformat(),
        "by_kind": [
            {
                "kind": row[0],
                "count": row[1],
                "tokens_in": int(row[2] or 0),
                "tokens_out": int(row[3] or 0),
                "avg_latency_ms": float(row[4] or 0),
            }
            for row in rows
        ],
    }


# ---------- API Keys ----------
async def is_api_key_valid(session: AsyncSession, key: str) -> bool:
    r = await session.execute(
        select(ApiKey).where(ApiKey.key == key, ApiKey.is_active == True)  # noqa: E712
    )
    return r.scalar_one_or_none() is not None
