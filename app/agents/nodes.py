"""Nós do grafo LangGraph - Flux-Capacitor.

Pipeline: outliner -> researcher -> writer -> stylist -> reviewer -> finalizer

Todos os prompts vêm do registry central (`app.core.prompts`) e podem ser
editados em runtime via API/UI sem recompilar.
"""
import json
import re
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm import get_llm
from app.core.prompts import get_prompt
from app.agents.state import FluxState


def _sys(language: str) -> str:
    return get_prompt("system.friendly").format(language=language)


def _context_block(state: FluxState) -> str:
    """Bloco extra com texto extraído de arquivos enviados. Vazio se não houver."""
    ctx = state.get("context_text") or ""
    if not ctx.strip():
        return ""
    return (
        "\n\n---\nCONTEXTO DE REFERÊNCIA (extraído de arquivos enviados pelo usuário). "
        "USE este conteúdo como fonte primária — cite fatos, reutilize termos, respeite "
        "os dados. Se o material for específico (relatório, planilha, manual), ANCORE "
        "a apresentação nele.\n\n"
        f"{ctx}\n---\n"
    )


def _images_block(state: FluxState) -> str:
    """Bloco listando imagens disponíveis para o writer usar em slides."""
    imgs = state.get("image_urls") or []
    if not imgs:
        return ""
    lines = [f"- {i['url']}  ({i.get('filename','')})" for i in imgs]
    return (
        "\n\nIMAGENS DISPONÍVEIS (use EXATAMENTE estas URLs em slides visual_type='image' "
        "ou como `![bg right:40%](url)`; não invente outras URLs):\n" + "\n".join(lines) + "\n"
    )


# ---------- 1. Outliner ----------
def outliner(state: FluxState) -> dict[str, Any]:
    llm = get_llm(temperature=0.5)
    prompt = get_prompt("outliner.user").format(
        topic=state["topic"],
        audience=state.get("audience") or "geral",
        tone=state.get("tone", "friendly"),
        num_slides=state.get("num_slides", 8),
    )
    prompt += _context_block(state) + _images_block(state)
    resp = llm.invoke([
        SystemMessage(content=_sys(state.get("language", "pt-BR"))),
        HumanMessage(content=prompt),
    ])
    data = _parse_json(resp.content)
    return {
        "title": data.get("title", state["topic"]),
        "outline": data.get("slides", []),
    }


# ---------- 2. Researcher ----------
def researcher(state: FluxState) -> dict[str, Any]:
    """Produz briefing denso (fatos, conceitos, exemplos, prós/contras)."""
    llm = get_llm(temperature=0.3)  # baixa temperatura: factualidade
    outline = state.get("outline", [])
    prompt = get_prompt("research.user").format(
        topic=state["topic"],
        audience=state.get("audience") or "geral",
        outline_json=json.dumps(outline, ensure_ascii=False, indent=2),
    )
    prompt += _context_block(state)
    resp = llm.invoke([
        SystemMessage(content=_sys(state.get("language", "pt-BR"))),
        HumanMessage(content=prompt),
    ])
    data = _parse_json(resp.content)
    return {"research": data.get("research", [])}


# ---------- 3. Writer ----------
def writer(state: FluxState) -> dict[str, Any]:
    llm = get_llm(temperature=0.65)
    outline = state.get("outline", [])
    research = state.get("research", [])
    prompt = get_prompt("writer.user").format(
        outline_json=json.dumps(outline, ensure_ascii=False, indent=2),
        research_json=json.dumps(research, ensure_ascii=False, indent=2),
    )
    prompt += _context_block(state) + _images_block(state)
    resp = llm.invoke([
        SystemMessage(content=_sys(state.get("language", "pt-BR"))),
        HumanMessage(content=prompt),
    ])
    data = _parse_json(resp.content)
    slides = data.get("slides", [])
    for i, s in enumerate(slides):
        s.setdefault("order_index", i)
        s.setdefault("transition", "fade")
        s.setdefault("visual_type", "prose")
    return {"slides": slides}


# ---------- 4. Stylist ----------
def stylist(state: FluxState) -> dict[str, Any]:
    slides = state.get("slides", [])
    refined = []
    for s in slides:
        title = _soften_title(s.get("title", ""))
        content = _sanitize_content(s.get("content_md", ""))
        content = _inject_breath(content)
        refined.append({**s, "title": title, "content_md": content})
    return {"slides": refined}


# ---------- 5. Reviewer ----------
def reviewer(state: FluxState) -> dict[str, Any]:
    """Valida densidade, variedade e cobertura dos 7 pilares."""
    notes = []
    slides = state.get("slides", [])
    for s in slides:
        content = s.get("content_md", "")
        plain = re.sub(r"```[\s\S]*?```|\$\$[\s\S]*?\$\$", "", content)
        wc = len(plain.split())
        if wc > 75:
            notes.append(f"Slide {s.get('order_index')} muito denso ({wc} palavras).")
        elif wc < 8 and s.get("visual_type") not in ("cover", "quote", "mermaid", "math", "code", "image"):
            notes.append(f"Slide {s.get('order_index')} muito vazio — enriquecer.")
        if not s.get("icon"):
            notes.append(f"Slide {s.get('order_index')} sem ícone.")
    types = {s.get("visual_type", "prose") for s in slides}
    if len(slides) >= 6 and len(types) < 3:
        notes.append(f"Pouca variedade visual: apenas {types}.")
    return {"review_notes": notes}


# ---------- 6. Finalizer ----------
def finalizer(state: FluxState) -> dict[str, Any]:
    from app.services.marp_renderer import build_marp_markdown
    md = build_marp_markdown(
        title=state.get("title", "Apresentação"),
        slides=state.get("slides", []),
        theme=state.get("theme", "modern-soft"),
    )
    return {"markdown": md, "done": True}


# ---------- helpers ----------
def _parse_json(text: str) -> dict:
    if not text:
        return {}
    m = re.search(r"\{.*\}", text, re.DOTALL)
    raw = m.group(0) if m else text
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raw = raw.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(raw)
        except Exception:
            return {}


_IMPERATIVE_MAP = {
    r"^Saiba\b": "Que tal descobrir",
    r"^Entenda\b": "Vamos entender juntos",
    r"^Aprenda\b": "Topa aprender",
    r"^Veja\b": "Olha só",
    r"^Confira\b": "Dá uma olhada em",
}


def _soften_title(title: str) -> str:
    for pat, rep in _IMPERATIVE_MAP.items():
        title = re.sub(pat, rep, title, flags=re.IGNORECASE)
    return title


def _inject_breath(content: str) -> str:
    if "```" in content or "$$" in content or "|" in content:
        return content.strip()
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    return "\n\n".join(lines)


# Remove tags HTML de ícones/svg e emojis isolados em linha própria (ficam gigantes no Marp)
_ICON_HTML_RE = re.compile(r"<i\s[^>]*(?:data-lucide|lucide-icon|class=\"icon)[^>]*>\s*</i>", re.IGNORECASE)
_SVG_RE = re.compile(r"<svg[\s\S]*?</svg>", re.IGNORECASE)
_EMOJI_ONLY_LINE = re.compile(
    r"^[\s]*[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]+[\s]*$",
    re.MULTILINE,
)


def _sanitize_content(content: str) -> str:
    """Remove lixo visual que o writer possa ter injetado (ícones HTML, emojis soltos)."""
    if not content:
        return ""
    c = _ICON_HTML_RE.sub("", content)
    c = _SVG_RE.sub("", c)
    c = _EMOJI_ONLY_LINE.sub("", c)
    # normaliza linhas vazias múltiplas
    c = re.sub(r"\n{3,}", "\n\n", c)
    return c.strip()
