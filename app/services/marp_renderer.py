"""Renderizador Marp - Flux-Capacitor.

Layout estável e previsível:
- section flex column com padding e font-size controlados
- Emojis Twemoji forçados a 1em (evita ícones gigantes no Marp Core)
- Imagens inline limitadas por max-height/max-width
- Mermaid com texto visível via CSS !important
- Tabelas com visual profissional
- Ícone: emoji INLINE no título (sem span isolado)
"""
from typing import Iterable
from app.config import settings


MARP_FRONTMATTER = """---
marp: true
theme: default
paginate: true
size: 16:9
math: katex
transition: fade
style: |
  @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&family=Open+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap');
  section {
    font-family: 'Quicksand','Open Sans',system-ui,sans-serif;
    background: linear-gradient(135deg,#FFF9F2 0%,#FDF4E9 100%);
    color: #2B2B2B;
    padding: 48px 64px;
    font-size: 22px;
    line-height: 1.5;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    overflow: hidden;
  }
  section > * { max-width: 100%; }

  /* TWEMOJI / EMOJI IMG — força tamanho inline (bug dos ícones gigantes) */
  section img.emoji,
  section .emoji {
    width: 1.1em !important;
    height: 1.1em !important;
    display: inline-block !important;
    vertical-align: -0.15em !important;
    margin: 0 0.08em !important;
    box-shadow: none !important;
  }
  /* IMAGENS INLINE (não-bg): evita imagem gigante estourando o slide */
  section img:not(.emoji):not([class*="bg"]) {
    max-width: 100% !important;
    max-height: 55vh !important;
    display: block;
    margin: .4em auto;
    border-radius: 8px;
    object-fit: contain;
  }

  section h1 {
    font-weight: 700; color:#D35400; font-size: 2.2em; line-height:1.15;
    margin: 0 0 .35em 0; letter-spacing:-0.01em;
  }
  section h2 {
    font-weight: 700; color:#2B2B2B; font-size: 1.65em; line-height:1.2;
    margin: 0 0 .4em 0; padding-bottom:.3em;
    border-bottom: 3px solid #FDE6CF;
  }
  section h3 { font-weight: 600; color:#D35400; font-size: 1.1em; margin:.6em 0 .2em; }
  section p { font-size: 1em; line-height: 1.6; color:#2B2B2B; margin:.35em 0; }
  section a { color:#D35400; text-decoration:none; border-bottom:1px dotted #E67E22; }
  section strong { color:#D35400; font-weight:700; }
  section em { color:#6B7280; font-style: italic; }
  section ul, section ol { margin:.3em 0 .4em 0; padding-left:1.3em; }
  section li { margin:.25em 0; line-height:1.55; }
  section ul li::marker, section ol li::marker { color:#E67E22; }
  section code {
    background:#FDF0E1; color:#B8530A; padding:2px 7px; border-radius:5px;
    font-family:'JetBrains Mono',monospace; font-size:.85em;
  }
  section pre {
    background:#2B2B2B; color:#F5EFE7; padding:14px 18px; border-radius:10px;
    font-family:'JetBrains Mono',monospace; font-size:.72em; line-height:1.5;
    overflow:auto; margin:.4em 0; max-height:60%;
  }
  section pre code { background:transparent; color:inherit; padding:0; font-size:inherit; }

  /* MERMAID — texto visível mesmo com cascade do Marp */
  section .mermaid {
    display: flex; justify-content: center; align-items: center;
    margin: .4em 0; max-height: 65%;
  }
  section .mermaid svg {
    max-width: 100% !important;
    max-height: 100% !important;
    height: auto !important;
  }
  section .mermaid text,
  section .mermaid tspan {
    fill: #2B2B2B !important;
    font-family: 'Quicksand', sans-serif !important;
    font-size: 14px !important;
  }
  section .mermaid .nodeLabel,
  section .mermaid .edgeLabel,
  section .mermaid foreignObject div,
  section .mermaid foreignObject span,
  section .mermaid foreignObject p {
    color: #2B2B2B !important;
    background: transparent !important;
    font-family: 'Quicksand', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.3 !important;
  }

  /* TABELAS — destaque visual profissional */
  section table {
    border-collapse: separate; border-spacing: 0;
    margin:.5em 0; font-size:.85em; width: 100%;
    background: white; border-radius: 10px; overflow: hidden;
    box-shadow: 0 4px 14px -6px rgba(230,126,34,.25);
  }
  section thead th {
    background: linear-gradient(135deg,#FDE6CF 0%,#F9C99A 100%);
    color:#8B3A00; font-weight:700; text-align:left;
    padding:10px 14px; font-size:.98em; border-bottom:2px solid #E67E22;
  }
  section tbody td {
    padding:9px 14px; border-bottom:1px solid #FDF0E1; vertical-align: top;
  }
  section tbody tr:nth-child(even) td { background:#FFFBF5; }
  section tbody tr:last-child td { border-bottom:none; }
  section tbody tr:hover td { background:#FDF4E9; }

  /* blockquote */
  section blockquote {
    border-left:4px solid #E67E22; padding:10px 18px; color:#4B5563;
    font-style:italic; background:#FFF9F2; border-radius:0 8px 8px 0;
    margin:.5em 0; font-size:1.05em;
  }

  /* CLASSES POR VISUAL_TYPE */
  section.cover {
    background: linear-gradient(135deg,#FDE6CF 0%,#FFF9F2 60%,#FDF4E9 100%);
    text-align:center; justify-content:center; align-items:center;
  }
  section.cover h1 { font-size: 2.8em; color:#D35400; margin-bottom:.3em; }
  section.cover p { font-size: 1.3em; color:#6B7280; }

  section.lead { justify-content:center; text-align:center; }
  section.lead blockquote {
    font-size:1.4em; border:none; background:transparent; color:#2B2B2B;
    font-style:normal; font-weight:500; line-height:1.45; max-width:80%;
    margin:0 auto .5em; padding:0;
  }
  section.lead blockquote::before { content:'\\201C'; color:#E67E22; font-size:2em; vertical-align:-.2em; margin-right:.1em; }

  section.datatable { padding: 36px 48px; font-size:20px; }
  section.datatable h2 { font-size:1.5em; }
  section.datatable table { font-size:.82em; }

  section.formula { justify-content:center; align-items:center; text-align:center; }
  section.formula .katex-display { margin:.4em 0; font-size:1.4em; }

  /* paginação */
  section::after { color:#B5B5B5; font-size:.55em; }
---
"""


def _slide_image_url(keyword: str | None) -> str | None:
    if not keyword:
        return None
    kw = keyword.replace(" ", ",")
    return f"{settings.UNSPLASH_BASE}/1600x900/?{kw}"


# emojis para substituir ícones Lucide (inline no título)
_ICON_EMOJI = {
    "sparkles": "✨", "lightbulb": "💡", "rocket": "🚀", "heart-handshake": "🤝",
    "compass": "🧭", "zap": "⚡", "target": "🎯", "users": "👥",
    "chart-line": "📈", "code": "💻", "brain": "🧠", "message-circle": "💬",
    "book-open": "📖", "check": "✅", "star": "⭐", "map": "🗺️",
    "clock": "⏱️", "shield": "🛡️", "wand-2": "🪄", "play": "▶️",
    "alert-triangle": "⚠️", "scale": "⚖️", "trending-up": "📊", "layers": "📚",
    "settings": "⚙️", "puzzle": "🧩", "flag": "🚩", "milestone": "🏁",
    "info": "ℹ️", "gift": "🎁", "globe": "🌐", "hammer": "🔨",
}


def _render_slide(s: dict, is_cover: bool = False) -> str:
    title = (s.get("title") or "").strip()
    content = (s.get("content_md") or "").strip()
    icon = s.get("icon")
    visual = s.get("visual_type", "prose")
    img_kw = s.get("image_keyword")
    notes = s.get("notes")

    parts: list[str] = []

    cls = None
    if is_cover or visual == "cover":
        cls = "cover"
    elif visual == "quote":
        cls = "lead"
    elif visual == "table":
        cls = "datatable"
    elif visual == "math":
        cls = "formula"
    if cls:
        parts.append(f"<!-- _class: {cls} -->")

    # Background directive apenas para visual_type image; cover não recebe (fica limpa)
    if visual == "image" and img_kw:
        parts.append(f"![bg right:42%]({_slide_image_url(img_kw)})")

    # Título: emoji inline (herda tamanho do H2, evita span gigante)
    emoji = _ICON_EMOJI.get(icon, "") if icon else ""
    if title:
        if is_cover or visual == "cover":
            parts.append(f"# {title}")
        else:
            prefix = f"{emoji} " if emoji else ""
            parts.append(f"## {prefix}{title}")

    if content:
        parts.append(content)

    if notes:
        parts.append(f"<!--\nSpeaker notes: {notes}\n-->")

    return "\n\n".join(parts)


def build_marp_markdown(title: str, slides: Iterable[dict], theme: str = "modern-soft") -> str:
    slides_list = list(slides)
    cover = {
        "title": title,
        "content_md": "_Flux-Capacitor_ · apresentação friendly-first",
        "visual_type": "cover",
    }
    rendered = [_render_slide(cover, is_cover=True)]
    for s in slides_list:
        rendered.append(_render_slide(s))
    body = "\n\n---\n\n".join(rendered)
    return MARP_FRONTMATTER + "\n" + body + "\n"
