"""Modelos SQLAlchemy - Flux-Capacitor."""
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import uuid


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Presentation(Base):
    __tablename__ = "presentations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tone: Mapped[str] = mapped_column(String(64), default="friendly")
    language: Mapped[str] = mapped_column(String(16), default="pt-BR")
    theme: Mapped[str] = mapped_column(String(64), default="modern-soft")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    slides: Mapped[list["Slide"]] = relationship(
        back_populates="presentation",
        cascade="all, delete-orphan",
        order_by="Slide.order_index",
    )


class Slide(Base):
    __tablename__ = "slides"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    presentation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("presentations.id", ondelete="CASCADE")
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255))
    content_md: Mapped[str] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    image_keyword: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transition: Mapped[str] = mapped_column(String(32), default="fade")
    visual_type: Mapped[str] = mapped_column(String(32), default="prose")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    presentation: Mapped["Presentation"] = relationship(back_populates="slides")


class Interaction(Base):
    """Registro completo de interações com a LLM / agentes / API."""
    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    presentation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    slide_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(64))  # generate | refine | render | api_call
    agent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Prompt(Base):
    """Prompts do sistema editáveis em runtime."""
    __tablename__ = "prompts"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    variables: Mapped[str | None] = mapped_column(String(512), nullable=True)  # csv
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Attachment(Base):
    """Arquivo enviado pelo usuário e usado como contexto/conteúdo da apresentação."""
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    presentation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("presentations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    kind: Mapped[str] = mapped_column(String(16))  # text | image
    storage_path: Mapped[str] = mapped_column(String(512))  # relativo a data/uploads/
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
