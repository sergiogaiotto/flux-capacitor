"""Estado compartilhado do grafo LangGraph."""
from typing import TypedDict, Optional


class SlideDraft(TypedDict, total=False):
    order_index: int
    title: str
    content_md: str
    icon: Optional[str]
    image_keyword: Optional[str]
    transition: str
    notes: Optional[str]


class FluxState(TypedDict, total=False):
    # Inputs
    topic: str
    audience: Optional[str]
    tone: str
    language: str
    theme: str
    num_slides: int

    # Contexto via uploads
    context_text: str            # texto consolidado de docs/pdfs/xlsx/csv
    image_urls: list[dict]       # [{url, filename, alt}]

    # Working memory
    outline: list[dict]
    research: list[dict]
    slides: list[SlideDraft]
    review_notes: list[str]

    # Output
    title: str
    markdown: str
    done: bool
