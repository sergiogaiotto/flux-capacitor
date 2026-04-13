"""Rotas de apresentações."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_api_key
from app.api import schemas
from app.database import repository as repo
from app.services.presentation_service import generate_presentation, rebuild_markdown
from app.services.exporter import build_standalone_html

router = APIRouter(prefix="/presentations", tags=["presentations"])


@router.post("", response_model=schemas.PresentationOut, status_code=201)
async def create(
    payload: schemas.PresentationCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    p = await generate_presentation(
        db,
        topic=payload.topic,
        audience=payload.audience,
        tone=payload.tone,
        language=payload.language,
        theme=payload.theme,
        num_slides=payload.num_slides,
        attachment_ids=payload.attachment_ids,
    )
    return await _load_out(db, p.id)


@router.get("", response_model=list[schemas.PresentationSummary])
async def listing(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    return await repo.list_presentations(db)


@router.get("/{presentation_id}", response_model=schemas.PresentationOut)
async def get_one(
    presentation_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    out = await _load_out(db, presentation_id)
    if not out:
        raise HTTPException(404, "Apresentação não encontrada")
    return out


@router.patch("/{presentation_id}", response_model=schemas.PresentationOut)
async def update(
    presentation_id: str,
    payload: schemas.PresentationUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    p = await repo.update_presentation(
        db, presentation_id, **payload.model_dump(exclude_unset=True)
    )
    if not p:
        raise HTTPException(404, "Apresentação não encontrada")
    return await _load_out(db, presentation_id)


@router.delete("/{presentation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    presentation_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    ok = await repo.delete_presentation(db, presentation_id)
    if not ok:
        raise HTTPException(404, "Apresentação não encontrada")


@router.get("/{presentation_id}/markdown", response_class=PlainTextResponse)
async def get_markdown(
    presentation_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    p = await repo.get_presentation(db, presentation_id)
    if not p:
        raise HTTPException(404, "Não encontrada")
    return p.markdown or ""


@router.get("/{presentation_id}/export/html", response_class=HTMLResponse)
async def export_html(
    presentation_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    """Retorna HTML standalone, pronto para abrir em qualquer browser."""
    p = await repo.get_presentation(db, presentation_id)
    if not p:
        raise HTTPException(404, "Não encontrada")
    html = build_standalone_html(title=p.title, markdown=p.markdown or "")
    return HTMLResponse(content=html)


@router.post("/{presentation_id}/rebuild", response_model=schemas.PresentationOut)
async def rebuild(
    presentation_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    md = await rebuild_markdown(db, presentation_id)
    if not md:
        raise HTTPException(404, "Não encontrada")
    return await _load_out(db, presentation_id)


@router.get("/{presentation_id}/interactions")
async def interactions(
    presentation_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    items = await repo.list_interactions(db, presentation_id=presentation_id)
    return [
        {
            "id": i.id,
            "kind": i.kind,
            "agent": i.agent,
            "latency_ms": i.latency_ms,
            "created_at": i.created_at.isoformat(),
        }
        for i in items
    ]


# ---------- helper ----------
async def _load_out(db: AsyncSession, presentation_id: str) -> schemas.PresentationOut | None:
    p = await repo.get_presentation(db, presentation_id)
    if not p:
        return None
    slides = await repo.list_slides(db, presentation_id)
    return schemas.PresentationOut(
        id=p.id,
        title=p.title,
        topic=p.topic,
        audience=p.audience,
        tone=p.tone,
        language=p.language,
        theme=p.theme,
        status=p.status,
        markdown=p.markdown,
        created_at=p.created_at,
        updated_at=p.updated_at,
        slides=[schemas.SlideOut.model_validate(s) for s in slides],
    )
