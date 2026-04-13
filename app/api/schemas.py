"""Schemas Pydantic - Flux-Capacitor API."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ---------- Presentation ----------
class PresentationCreate(BaseModel):
    topic: str = Field(..., min_length=3, max_length=20000)
    audience: Optional[str] = Field(None, max_length=500)
    tone: str = "friendly"
    language: str = "pt-BR"
    theme: str = "modern-soft"
    num_slides: int = Field(8, ge=3, le=30)
    attachment_ids: list[str] = []


class PresentationUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    theme: Optional[str] = None


class SlideOut(BaseModel):
    id: str
    order_index: int
    title: str
    content_md: str
    icon: Optional[str] = None
    image_keyword: Optional[str] = None
    transition: str = "fade"
    notes: Optional[str] = None
    visual_type: Optional[str] = "prose"

    class Config:
        from_attributes = True


class PresentationOut(BaseModel):
    id: str
    title: str
    topic: str
    audience: Optional[str] = None
    tone: str
    language: str
    theme: str
    status: str
    markdown: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    slides: list[SlideOut] = []

    class Config:
        from_attributes = True


class PresentationSummary(BaseModel):
    id: str
    title: str
    topic: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Slides ----------
class SlideCreate(BaseModel):
    title: str = "Novo slide"
    content_md: str = ""
    icon: Optional[str] = "sparkles"
    image_keyword: Optional[str] = None
    transition: str = "fade"
    visual_type: str = "prose"
    notes: Optional[str] = None
    after_slide_id: Optional[str] = None  # inserir após este slide


class SlideUpdate(BaseModel):
    title: Optional[str] = None
    content_md: Optional[str] = None
    icon: Optional[str] = None
    image_keyword: Optional[str] = None
    transition: Optional[str] = None
    notes: Optional[str] = None


class SlideRefineIn(BaseModel):
    instruction: str = Field(..., min_length=3, max_length=1000)


class SlideReorderIn(BaseModel):
    ordered_ids: list[str]


# ---------- Stats ----------
class StatsOut(BaseModel):
    since: str
    by_kind: list[dict]
