"""Serviço de apresentações - orquestra agentes + persistência + logging."""
import time
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.agents.graph import run_pipeline, run_refine_slide
from app.database import repository as repo
from app.database.models import Attachment
from app.services.marp_renderer import build_marp_markdown
from app.config import settings


async def _load_attachment_context(
    session: AsyncSession,
    attachment_ids: list[str],
) -> tuple[str, list[dict], list[Attachment]]:
    """Carrega attachments, retorna (context_text, image_urls, rows)."""
    if not attachment_ids:
        return "", [], []
    rows = (await session.execute(
        select(Attachment).where(Attachment.id.in_(attachment_ids))
    )).scalars().all()

    parts: list[str] = []
    imgs: list[dict] = []
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    for a in rows:
        url = f"{base}/uploads/{a.id}/{a.filename}"
        if a.kind == "image":
            imgs.append({"url": url, "filename": a.filename, "alt": a.filename})
        elif a.extracted_text:
            parts.append(f"### Arquivo: {a.filename}\n{a.extracted_text}")
    return "\n\n".join(parts), imgs, list(rows)


async def generate_presentation(
    session: AsyncSession,
    topic: str,
    audience: Optional[str] = None,
    tone: str = "friendly",
    language: str = "pt-BR",
    theme: str = "modern-soft",
    num_slides: int = 8,
    attachment_ids: list[str] | None = None,
):
    """Executa pipeline, persiste apresentação + slides, loga interação."""
    attachment_ids = attachment_ids or []
    context_text, image_urls, att_rows = await _load_attachment_context(session, attachment_ids)

    t0 = time.time()
    result = await run_pipeline(
        topic=topic,
        audience=audience,
        tone=tone,
        language=language,
        theme=theme,
        num_slides=num_slides,
        context_text=context_text,
        image_urls=image_urls,
    )
    latency = int((time.time() - t0) * 1000)

    title = result.get("title") or topic
    slides = result.get("slides", [])
    markdown = result.get("markdown", "")

    presentation = await repo.create_presentation(
        session,
        title=title,
        topic=topic,
        audience=audience,
        tone=tone,
        language=language,
        theme=theme,
        status="draft",
        markdown=markdown,
        meta={
            "num_slides": num_slides,
            "review_notes": result.get("review_notes", []),
            "attachments": [
                {"id": a.id, "filename": a.filename, "kind": a.kind}
                for a in att_rows
            ],
        },
    )

    # associa attachments à apresentação
    for a in att_rows:
        a.presentation_id = presentation.id
    if att_rows:
        await session.commit()

    await repo.bulk_create_slides(
        session,
        presentation_id=presentation.id,
        slides=[
            {
                "order_index": s.get("order_index", i),
                "title": s.get("title", ""),
                "content_md": s.get("content_md", ""),
                "icon": s.get("icon"),
                "image_keyword": s.get("image_keyword"),
                "transition": s.get("transition", "fade"),
                "visual_type": s.get("visual_type", "prose"),
                "notes": s.get("notes"),
            }
            for i, s in enumerate(slides)
        ],
    )

    await repo.log_interaction(
        session,
        presentation_id=presentation.id,
        kind="generate",
        agent="flux.pipeline",
        prompt=topic,
        response=markdown[:4000],
        latency_ms=latency,
        meta={"num_slides": num_slides, "attachments": len(att_rows)},
    )

    return presentation


async def refine_slide(
    session: AsyncSession,
    slide_id: str,
    instruction: str,
    language: str = "pt-BR",
):
    slide = await repo.get_slide(session, slide_id)
    if not slide:
        return None

    t0 = time.time()
    refined = await run_refine_slide(
        slide_title=slide.title,
        slide_content=slide.content_md,
        instruction=instruction,
        language=language,
    )
    latency = int((time.time() - t0) * 1000)

    updated = await repo.update_slide(
        session,
        slide_id=slide_id,
        title=refined.get("title") or slide.title,
        content_md=refined.get("content_md") or slide.content_md,
        icon=refined.get("icon") or slide.icon,
        image_keyword=refined.get("image_keyword") or slide.image_keyword,
        notes=refined.get("notes") or slide.notes,
    )

    await _rebuild_markdown(session, slide.presentation_id)

    await repo.log_interaction(
        session,
        presentation_id=slide.presentation_id,
        slide_id=slide_id,
        kind="refine",
        agent="flux.refine",
        prompt=instruction,
        response=str(refined)[:4000],
        latency_ms=latency,
    )
    return updated


async def _rebuild_markdown(session: AsyncSession, presentation_id: str) -> str:
    presentation = await repo.get_presentation(session, presentation_id)
    if not presentation:
        return ""
    slides = await repo.list_slides(session, presentation_id)
    md = build_marp_markdown(
        title=presentation.title,
        slides=[
            {
                "order_index": s.order_index,
                "title": s.title,
                "content_md": s.content_md,
                "icon": s.icon,
                "image_keyword": s.image_keyword,
                "transition": s.transition,
                "visual_type": s.visual_type,
                "notes": s.notes,
            }
            for s in slides
        ],
        theme=presentation.theme,
    )
    await repo.update_presentation(session, presentation_id, markdown=md)
    return md


async def rebuild_markdown(session: AsyncSession, presentation_id: str) -> str:
    return await _rebuild_markdown(session, presentation_id)
