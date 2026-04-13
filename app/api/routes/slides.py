"""Rotas de slides - edição granular."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_api_key
from app.api import schemas
from app.database import repository as repo
from app.services.presentation_service import refine_slide, rebuild_markdown

router = APIRouter(prefix="/slides", tags=["slides"])


@router.get("/{slide_id}", response_model=schemas.SlideOut)
async def get_one(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    s = await repo.get_slide(db, slide_id)
    if not s:
        raise HTTPException(404, "Slide não encontrado")
    return s


@router.patch("/{slide_id}", response_model=schemas.SlideOut)
async def update(
    slide_id: str,
    payload: schemas.SlideUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    s = await repo.update_slide(db, slide_id, **payload.model_dump(exclude_unset=True))
    if not s:
        raise HTTPException(404, "Slide não encontrado")
    await rebuild_markdown(db, s.presentation_id)
    return s


@router.post("/{slide_id}/refine", response_model=schemas.SlideOut)
async def refine(
    slide_id: str,
    payload: schemas.SlideRefineIn,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    s = await refine_slide(db, slide_id=slide_id, instruction=payload.instruction)
    if not s:
        raise HTTPException(404, "Slide não encontrado")
    return s


@router.delete("/{slide_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    s = await repo.get_slide(db, slide_id)
    if not s:
        raise HTTPException(404, "Slide não encontrado")
    pid = s.presentation_id
    await repo.delete_slide(db, slide_id)
    await rebuild_markdown(db, pid)


reorder_router = APIRouter(prefix="/presentations", tags=["slides"])


@reorder_router.post("/{presentation_id}/slides", response_model=schemas.SlideOut, status_code=201)
async def add_slide(
    presentation_id: str,
    payload: schemas.SlideCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    """Adiciona um slide novo. Se after_slide_id vier, insere logo após ele."""
    existing = await repo.list_slides(db, presentation_id)
    if payload.after_slide_id:
        ref_idx = next((i for i, s in enumerate(existing) if s.id == payload.after_slide_id), len(existing) - 1)
        insert_at = ref_idx + 1
    else:
        insert_at = len(existing)
    # shift dos slides subsequentes
    for s in existing[insert_at:]:
        await repo.update_slide(db, s.id, order_index=s.order_index + 1)
    # cria o novo
    data = payload.model_dump(exclude={"after_slide_id"})
    data["order_index"] = insert_at
    created = await repo.bulk_create_slides(db, presentation_id=presentation_id, slides=[data])
    await rebuild_markdown(db, presentation_id)
    return created[0]


@reorder_router.post("/{presentation_id}/slides/{slide_id}/duplicate", response_model=schemas.SlideOut, status_code=201)
async def duplicate_slide(
    presentation_id: str,
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    src = await repo.get_slide(db, slide_id)
    if not src or src.presentation_id != presentation_id:
        raise HTTPException(404, "Slide não encontrado")
    existing = await repo.list_slides(db, presentation_id)
    insert_at = src.order_index + 1
    for s in existing[insert_at:]:
        await repo.update_slide(db, s.id, order_index=s.order_index + 1)
    created = await repo.bulk_create_slides(
        db,
        presentation_id=presentation_id,
        slides=[{
            "order_index": insert_at,
            "title": src.title + " (cópia)",
            "content_md": src.content_md,
            "icon": src.icon,
            "image_keyword": src.image_keyword,
            "transition": src.transition,
            "visual_type": src.visual_type,
            "notes": src.notes,
        }],
    )
    await rebuild_markdown(db, presentation_id)
    return created[0]


@reorder_router.post("/{presentation_id}/reorder", response_model=list[schemas.SlideOut])
async def reorder(
    presentation_id: str,
    payload: schemas.SlideReorderIn,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    slides = await repo.reorder_slides(db, presentation_id, payload.ordered_ids)
    await rebuild_markdown(db, presentation_id)
    return slides
