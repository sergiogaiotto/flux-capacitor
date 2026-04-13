"""Exporta apresentação para HTML standalone.

Renderiza com @marp-team/marp-core + Mermaid.js (tudo client-side).
Imagens em /uploads/{id}/{filename} são inlined como data URIs em base64.

FIXES aplicados:
- Mermaid com theme: "base" + themeVariables completos + htmlLabels: false
  (sem isso, Mermaid 10 ignora cores customizadas)
- CSS global força visibilidade de texto Mermaid (defense in depth)
- Twemoji img.emoji limitado a 1.1em (evita ícones gigantes)
- Imagens inline com max-height controlado
- Flatten de sections após render (Marp pode envolver em wrapper)
"""
from __future__ import annotations
import base64
import json
import mimetypes
import re
from pathlib import Path
from app.config import settings


def _inline_local_images(markdown: str) -> str:
    """Substitui URLs /uploads/{id}/{filename} por data URIs em base64."""
    upload_root = Path(settings.UPLOAD_DIR)
    public_prefix = settings.PUBLIC_BASE_URL.rstrip("/")
    pattern = re.compile(
        r"(?:" + re.escape(public_prefix) + r")?/uploads/([0-9a-fA-F-]{36})/([^\s\)\]\"']+)"
    )

    def replace(m: re.Match) -> str:
        att_id, filename = m.group(1), m.group(2)
        path = upload_root / att_id / filename
        if not path.exists() or not path.is_file():
            return m.group(0)
        mime, _ = mimetypes.guess_type(filename)
        if not mime or not mime.startswith("image/"):
            return m.group(0)
        try:
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        except Exception:
            return m.group(0)
        return f"data:{mime};base64,{encoded}"

    return pattern.sub(replace, markdown)


def build_standalone_html(title: str, markdown: str) -> str:
    markdown = _inline_local_images(markdown)
    payload = json.dumps(markdown)
    safe_title = (title or "Flux-Capacitor").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{safe_title} · Flux-Capacitor</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&family=Open+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" />
<style>
  :root {{
    --flux-50:#FFF9F2; --flux-100:#FDF4E9; --flux-200:#FDE6CF; --flux-400:#F2A76A;
    --flux-500:#E67E22; --flux-600:#D35400; --flux-ink:#2B2B2B; --flux-soft:#6B7280;
  }}
  html,body {{ margin:0; padding:0; background: linear-gradient(135deg,#FFF9F2,#FDF4E9); font-family:'Quicksand','Open Sans',system-ui,sans-serif; color:var(--flux-ink); }}
  header {{ position:sticky; top:0; z-index:30; display:flex; align-items:center; justify-content:space-between; padding:14px 24px; background:rgba(255,249,242,.92); backdrop-filter:blur(6px); border-bottom:1px solid var(--flux-200); }}
  header .brand {{ display:flex; align-items:center; gap:10px; font-weight:700; }}
  header .brand .logo {{ width:32px;height:32px;border-radius:10px;background:linear-gradient(135deg,var(--flux-400),var(--flux-600)); display:grid;place-items:center; color:white; font-weight:800; }}
  header nav button {{ margin-left:6px; padding:8px 14px; border-radius:12px; border:1px solid var(--flux-200); background:white; font:inherit; font-weight:600; cursor:pointer; color:var(--flux-ink); }}
  header nav button.primary {{ background:linear-gradient(135deg,var(--flux-400),var(--flux-600)); color:white; border-color:transparent; box-shadow:0 8px 24px -10px rgba(230,126,34,.45); }}

  #deck {{ display:flex; flex-direction:column; gap:28px; padding:32px clamp(16px,4vw,48px) 80px; max-width:1280px; margin:0 auto; }}

  /* SLIDES COM PROPORÇÃO FIXA 16:9 — conteúdo escala via container queries */
  #deck > section {{
    width: 100% !important;
    height: auto !important;
    aspect-ratio: 16 / 9 !important;
    max-width: 1280px !important;
    min-width: 0 !important;
    min-height: 0 !important;
    margin: 0 auto !important;
    padding: 3.8% 5% !important;
    border-radius: 18px !important;
    overflow: hidden !important;
    box-shadow: 0 16px 40px -20px rgba(0,0,0,.15) !important;
    border: 1px solid var(--flux-200) !important;
    background: white !important;
    container-type: inline-size;
    /* fonte base escala com largura do container: 1280px -> 24px, 800px -> 15px */
    font-size: clamp(11px, 1.9cqw, 26px) !important;
    line-height: 1.45 !important;
    box-sizing: border-box;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
  }}
  /* Dentro do slide, tudo usa unidades relativas (em) ou % para escalar junto */
  #deck > section > * {{ max-width: 100%; }}
  #deck > section h1 {{ font-size: 2.4em !important; line-height: 1.1 !important; margin: 0 0 .3em 0 !important; }}
  #deck > section h2 {{ font-size: 1.7em !important; line-height: 1.15 !important; margin: 0 0 .35em 0 !important; padding-bottom: .25em !important; border-bottom: 3px solid #FDE6CF !important; }}
  #deck > section h3 {{ font-size: 1.15em !important; margin: .5em 0 .2em !important; }}
  #deck > section p {{ font-size: 1em !important; line-height: 1.55 !important; margin: .3em 0 !important; }}
  #deck > section ul, #deck > section ol {{ margin: .3em 0 !important; padding-left: 1.3em !important; font-size: 1em !important; }}
  #deck > section li {{ margin: .2em 0 !important; }}
  #deck > section table {{ font-size: .82em !important; }}
  #deck > section pre {{ font-size: .72em !important; max-height: 60% !important; }}
  /* slide de capa: override de escala para hero maior */
  #deck > section.cover h1 {{ font-size: 3em !important; }}
  #deck > section.cover p {{ font-size: 1.3em !important; }}

  .hint {{ text-align:center; color:var(--flux-soft); font-size:.85rem; margin-top:-14px; }}

  /* CSS DE PROTEÇÃO — aplicado dentro das sections do Marp (defense in depth) */
  #deck section img.emoji, #deck section .emoji {{
    width: 1.1em !important; height: 1.1em !important;
    display: inline-block !important; vertical-align: -0.15em !important;
    margin: 0 0.08em !important; box-shadow: none !important;
  }}
  #deck section img:not(.emoji):not([class*="bg"]) {{
    max-width: 100% !important; max-height: 55vh !important;
    display: block; margin: .4em auto; border-radius: 8px; object-fit: contain;
  }}
  /* MERMAID — força visibilidade em qualquer contexto */
  #deck section .mermaid {{ display: flex; justify-content: center; align-items: center; margin: .4em 0; max-height: 65%; }}
  #deck section .mermaid svg {{ max-width: 100% !important; max-height: 100% !important; height: auto !important; }}
  #deck section .mermaid text,
  #deck section .mermaid tspan {{
    fill: #2B2B2B !important;
    font-family: 'Quicksand', sans-serif !important;
    font-size: 14px !important;
  }}
  #deck section .mermaid .nodeLabel,
  #deck section .mermaid .edgeLabel,
  #deck section .mermaid foreignObject div,
  #deck section .mermaid foreignObject span,
  #deck section .mermaid foreignObject p {{
    color: #2B2B2B !important; background: transparent !important;
    font-family: 'Quicksand', sans-serif !important;
    font-size: 14px !important; line-height: 1.3 !important;
  }}

  /* MODO APRESENTAÇÃO */
  body.present {{ overflow:hidden; background:#000; }}
  body.present header, body.present .hint {{ display:none !important; }}
  body.present #deck {{ padding:0 !important; max-width:none !important; gap:0 !important; margin:0 !important; display:block !important; height:100vh; width:100vw; }}
  body.present #deck > section {{ display:none !important; border-radius:0 !important; box-shadow:none !important; border:none !important; margin:0 !important; }}
  /* slide ativo ocupa a tela mantendo 16:9; conteúdo continua escalando via cqw */
  body.present #deck > section.active {{
    display: flex !important;
    position: fixed !important;
    top: 50% !important; left: 50% !important;
    transform: translate(-50%, -50%) !important;
    inset: auto !important;
    /* 16:9 contido na viewport: menor entre 100vw e 177.78vh */
    width: min(100vw, 177.78vh) !important;
    height: min(56.25vw, 100vh) !important;
    max-width: none !important;
    aspect-ratio: 16 / 9 !important;
    z-index: 50 !important;
  }}

  .pager {{ position:fixed; bottom:20px; left:50%; transform:translateX(-50%); display:none; gap:8px; background:rgba(0,0,0,.7); padding:10px 14px; border-radius:999px; color:white; font-size:.9rem; z-index:60; align-items:center; }}
  body.present .pager {{ display:flex; }}
  .pager button {{ border:none; background:rgba(255,255,255,.15); color:white; width:34px; height:34px; border-radius:50%; cursor:pointer; font-size:1rem; display:grid; place-items:center; }}
  .pager button:hover {{ background:rgba(255,255,255,.3); }}
  .pager button:disabled {{ opacity:.3; cursor:not-allowed; }}
</style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="logo">⚡</div>
      <div>
        <div style="line-height:1">{safe_title}</div>
        <div style="font-size:.75rem; color:var(--flux-soft); font-weight:500">Flux-Capacitor · friendly-first</div>
      </div>
    </div>
    <nav>
      <button onclick="window.print()">🖨️ Imprimir / PDF</button>
      <button class="primary" onclick="togglePresent()">▶ Apresentar</button>
    </nav>
  </header>

  <div id="deck"></div>
  <p class="hint">No modo apresentação: ← → ou espaço para navegar · ESC para sair</p>

  <div class="pager">
    <button onclick="go(-1)" id="prev-btn">‹</button>
    <span id="pageIndicator">1 / 1</span>
    <button onclick="go(1)" id="next-btn">›</button>
    <button onclick="togglePresent()" title="Sair">✕</button>
  </div>

<script type="module">
  import {{ Marp }} from "https://esm.sh/@marp-team/marp-core@3.9.0";
  import mermaid from "https://esm.sh/mermaid@10.9.0";

  const markdown = {payload};
  const marp = new Marp({{ html: true, math: "katex", inlineSVG: false }});
  const {{ html, css }} = marp.render(markdown);

  // CSS gerado pelo Marp (tema default + estilos do frontmatter)
  const style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  const deck = document.getElementById("deck");
  deck.innerHTML = html;

  // APLANAR: sections devem ser filhas diretas de #deck
  const allSections = Array.from(deck.querySelectorAll("section"));
  if (allSections.length && allSections[0].parentElement !== deck) {{
    deck.innerHTML = "";
    allSections.forEach((s) => deck.appendChild(s));
  }}

  // Primeiro slide sempre é capa (marcação defensiva caso a diretiva _class não tenha sido aplicada)
  const firstSection = deck.querySelector(":scope > section");
  if (firstSection && !firstSection.classList.contains("cover")) {{
    firstSection.classList.add("cover");
  }}

  // Converter <pre><code class="language-mermaid"> em <div class="mermaid">
  deck.querySelectorAll('pre > code.language-mermaid, pre > code[class*="mermaid"]').forEach((code) => {{
    const pre = code.parentElement;
    const wrap = document.createElement("div");
    wrap.className = "mermaid";
    wrap.textContent = code.textContent;
    pre.replaceWith(wrap);
  }});

  // Mermaid: theme "base" + themeVariables + htmlLabels:false (texto via <text> SVG nativo)
  mermaid.initialize({{
    startOnLoad: false,
    theme: "base",
    securityLevel: "loose",
    themeVariables: {{
      primaryColor: "#FFF4E8",
      primaryTextColor: "#2B2B2B",
      primaryBorderColor: "#E67E22",
      lineColor: "#E67E22",
      secondaryColor: "#FDE6CF",
      tertiaryColor: "#FFF9F2",
      background: "#FFFFFF",
      mainBkg: "#FFF4E8",
      secondBkg: "#FDE6CF",
      tertiaryBkg: "#FFF9F2",
      nodeBorder: "#E67E22",
      clusterBkg: "#FDF4E9",
      clusterBorder: "#E67E22",
      defaultLinkColor: "#E67E22",
      titleColor: "#D35400",
      edgeLabelBackground: "#FFF9F2",
      textColor: "#2B2B2B",
      fontFamily: "Quicksand, sans-serif",
      fontSize: "14px"
    }},
    flowchart: {{ curve: "basis", padding: 12, htmlLabels: false, useMaxWidth: true }},
    sequence: {{ useMaxWidth: true }},
    gantt: {{ useMaxWidth: true }},
    mindmap: {{ useMaxWidth: true }}
  }});
  try {{
    await mermaid.run({{ querySelector: "#deck .mermaid" }});
  }} catch (e) {{ console.warn("mermaid:", e); }}

  // -------- modo apresentação --------
  const getSections = () => deck.querySelectorAll(":scope > section");
  let idx = 0;

  function refresh() {{
    const all = getSections();
    all.forEach((s, i) => s.classList.toggle("active", i === idx));
    document.getElementById("pageIndicator").textContent = `${{idx + 1}} / ${{all.length}}`;
    document.getElementById("prev-btn").disabled = idx === 0;
    document.getElementById("next-btn").disabled = idx === all.length - 1;
  }}

  window.go = (delta) => {{
    const all = getSections();
    idx = Math.max(0, Math.min(all.length - 1, idx + delta));
    refresh();
  }};

  window.togglePresent = () => {{
    const entering = !document.body.classList.contains("present");
    document.body.classList.toggle("present", entering);
    if (entering) {{
      idx = 0;
      refresh();
      if (document.documentElement.requestFullscreen) {{
        document.documentElement.requestFullscreen().catch(() => {{}});
      }}
    }} else {{
      if (document.fullscreenElement) document.exitFullscreen().catch(() => {{}});
      getSections().forEach((s) => s.classList.remove("active"));
    }}
  }};

  document.addEventListener("keydown", (e) => {{
    if (!document.body.classList.contains("present")) return;
    if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {{ go(1); e.preventDefault(); }}
    else if (e.key === "ArrowLeft" || e.key === "PageUp") {{ go(-1); e.preventDefault(); }}
    else if (e.key === "Escape") togglePresent();
    else if (e.key === "Home") {{ idx = 0; refresh(); }}
    else if (e.key === "End") {{ idx = getSections().length - 1; refresh(); }}
  }});

  document.addEventListener("fullscreenchange", () => {{
    if (!document.fullscreenElement && document.body.classList.contains("present")) {{
      document.body.classList.remove("present");
      getSections().forEach((s) => s.classList.remove("active"));
    }}
  }});
</script>
</body>
</html>
"""
