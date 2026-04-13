# ⚡ Flux-Capacitor

**Gerador de Apresentações Friendly-First** — um designer de experiência instrucional que converte uma ideia em texto simples num deck dinâmico, acolhedor e responsivo, pronto para ser exportado via Marp ou Reveal.js.

> Tom conversacional · Tema *Modern Soft* · Lucide icons · placeholders Unsplash · Mobile-friendly

---

## 🧭 Arquitetura

```
flux-capacitor/
├── app/
│   ├── main.py                 # FastAPI + CORS + mount do frontend
│   ├── config.py               # Pydantic Settings (.env)
│   ├── core/
│   │   ├── llm.py              # ChatOpenAI (langchain-openai)
│   │   └── observability.py    # LangFuse callback
│   ├── database/
│   │   ├── models.py           # SQLAlchemy: Presentation, Slide, Interaction, ApiKey
│   │   ├── connection.py       # Engines async + sync, init_db + seed
│   │   └── repository.py       # Módulo específico de consultas
│   ├── agents/
│   │   ├── state.py            # TypedDict do grafo
│   │   ├── nodes.py            # outliner → writer → stylist → reviewer → finalizer
│   │   └── graph.py            # StateGraph LangGraph
│   ├── services/
│   │   ├── marp_renderer.py    # Gera markdown Marp com tema Modern Soft
│   │   └── presentation_service.py
│   ├── api/
│   │   ├── deps.py             # DB session + auth por API Key
│   │   ├── schemas.py          # Pydantic I/O
│   │   └── routes/
│   │       ├── health.py
│   │       ├── presentations.py
│   │       ├── slides.py
│   │       └── stats.py
│   └── templates/
│       └── marp_theme.css      # Tema Modern Soft (Marp CLI)
├── frontend/
│   ├── index.html              # Wizard passo-a-passo (Tailwind CDN)
│   └── assets/
│       ├── app.js              # Lógica da UI
│       └── styles.css
├── data/                       # SQLite (gerado)
├── requirements.txt
├── .env.example
├── run.py
└── README.md
```

**Stack:** Python · FastAPI · LangGraph · OpenAI · LangFuse · SQLite (SQLAlchemy async) · Tailwind · Lucide · Marp

---

## 🎨 Recursos Marp explorados

Os prompts do pipeline instruem a IA a escolher o recurso Marp certo para cada slide. Tipos disponíveis (campo `visual_type`):

| Tipo | Uso | Recurso Marp |
|---|---|---|
| `cover` | Capa com background | `![bg opacity:.25]` |
| `prose` | Texto + ícone | markdown padrão |
| `mermaid` | Fluxos, arquiteturas, timelines | bloco ` ```mermaid ` |
| `math` | Fórmulas em destaque | `$$...$$` (KaTeX) |
| `code` | Blocos de código | ` ```python ` com highlight |
| `table` | Comparações | tabela markdown |
| `image` | Imagem dominante | `![bg right:40%](...)` |
| `quote` | Citação inspiradora | `> ...` com classe `lead` |

## 📦 Export HTML standalone

O endpoint `GET /api/v1/presentations/{id}/export/html` retorna um **HTML único** que:

- Renderiza o deck client-side usando `@marp-team/marp-core` (via esm.sh)
- Processa blocos `mermaid` com mermaid.js
- Renderiza fórmulas com KaTeX
- Tem modo apresentação fullscreen (tecla ▶ / ← → / ESC)
- Botão de impressão/PDF nativo do browser
- **Abre em qualquer lugar** — zero dependência de servidor

```bash
curl -H "X-API-Key: change-me-flux-capacitor-key" \
     http://localhost:8000/api/v1/presentations/<id>/export/html \
     -o deck.html
open deck.html  # ou duplo-clique
```

## 🐳 Docker

```bash
export OPENAI_API_KEY=sk-...
docker compose up -d --build
# http://localhost:8000
```

Persistência em `./data` (SQLite). Healthcheck no `/api/v1/health`.

## 🚀 Setup

```bash
git clone <repo> flux-capacitor && cd flux-capacitor
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edite .env com sua OPENAI_API_KEY e (opcional) credenciais LangFuse
python run.py
```

A aplicação sobe em **http://localhost:8000**:

- `/` — UI do Flux-Capacitor
- `/docs` — Swagger UI
- `/api/v1/health` — health check

### API Key padrão

Seeded no primeiro boot (tabela `api_keys`):

```
change-me-flux-capacitor-key
```

Troque via `.env` (`API_DEFAULT_KEY`) ou insira manualmente no SQLite para ambientes de produção.

---

## 🎨 Exportando com Marp CLI

A cada geração / edição, o markdown completo fica disponível em:

```
GET /api/v1/presentations/{id}/markdown
```

Para exportar HTML / PDF / PPTX:

```bash
npm i -g @marp-team/marp-cli
curl -H "X-API-Key: change-me-flux-capacitor-key" \
     http://localhost:8000/api/v1/presentations/<id>/markdown \
     -o deck.md

marp --theme-set app/templates/marp_theme.css deck.md -o deck.html
marp --theme-set app/templates/marp_theme.css --pdf deck.md -o deck.pdf
marp --theme-set app/templates/marp_theme.css --pptx deck.md -o deck.pptx
```

---

## 🔌 API

Todas as rotas requerem header `X-API-Key`.

### Criar apresentação

```bash
curl -X POST http://localhost:8000/api/v1/presentations \
  -H "X-API-Key: change-me-flux-capacitor-key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Introdução a IA generativa para marketing",
    "audience": "CMOs e diretores",
    "tone": "friendly",
    "language": "pt-BR",
    "num_slides": 8
  }'
```

### Endpoints principais

| Método | Path | Descrição |
|---|---|---|
| `POST` | `/api/v1/presentations` | Gera apresentação (executa o grafo) |
| `GET` | `/api/v1/presentations` | Lista |
| `GET` | `/api/v1/presentations/{id}` | Detalhe com slides |
| `PATCH` | `/api/v1/presentations/{id}` | Atualiza metadados |
| `DELETE` | `/api/v1/presentations/{id}` | Remove |
| `GET` | `/api/v1/presentations/{id}/markdown` | Markdown Marp |
| `POST` | `/api/v1/presentations/{id}/rebuild` | Recompila markdown |
| `POST` | `/api/v1/presentations/{id}/reorder` | Reordena slides |
| `GET` | `/api/v1/presentations/{id}/interactions` | Histórico de chamadas à LLM |
| `GET` | `/api/v1/slides/{id}` | Detalhe |
| `PATCH` | `/api/v1/slides/{id}` | Edita slide |
| `POST` | `/api/v1/slides/{id}/refine` | Refina via IA (instrução livre) |
| `DELETE` | `/api/v1/slides/{id}` | Remove |
| `POST` | `/api/v1/presentations/{id}/slides` | Adiciona slide (opcional `after_slide_id`) |
| `POST` | `/api/v1/presentations/{id}/slides/{slide_id}/duplicate` | Duplica slide |
| `GET` | `/api/v1/stats?days=7` | Métricas de uso |

### Refinar um slide

```bash
curl -X POST http://localhost:8000/api/v1/slides/<slide-id>/refine \
  -H "X-API-Key: change-me-flux-capacitor-key" \
  -H "Content-Type: application/json" \
  -d '{"instruction": "deixe mais curto e inclua uma metáfora de viagem"}'
```

---

## 🧠 Pipeline LangGraph

```
START → outliner → researcher → writer → stylist → reviewer → finalizer → END
```

| Nó | Função |
|---|---|
| `outliner` | Gera estrutura do deck cobrindo os 7 pilares (fundamentos, conceitos, aplicações, orientações, prós/contras, benefícios/desafios, próximos passos) |
| `researcher` | Produz briefing denso por slide: fatos, conceitos com definições, exemplos, prós/contras, insight não-óbvio |
| `writer` | Consome outline + briefing e escreve content_md rico, regras específicas por `visual_type` |
| `stylist` | Suaviza imperativos, injeta respiro visual |
| `reviewer` | Valida densidade (nem vazio, nem denso demais), variedade de `visual_type`, presença de ícones |
| `finalizer` | Compila markdown Marp com front-matter e tema Modern Soft |

Refino individual de slide é um nó isolado (`run_refine_slide`).

## ✏️ System Prompts editáveis

Todos os prompts do pipeline ficam em **`app/core/prompts.py`** (defaults) e são persistidos na tabela `prompts` para edição em runtime. Nenhum reload é necessário — a próxima geração já usa a versão nova.

**Prompts disponíveis:**
- `system.friendly` — system shared (tom + 7 pilares de conteúdo + recursos Marp)
- `outliner.user` — gera outline
- `research.user` — gera briefing denso
- `writer.user` — escreve slides a partir de outline + briefing
- `refine.user` — ajusta slide individual via instrução

**Editar via UI:** clique no ícone de engrenagem no header → selecione o prompt → edite → Salvar. Botão "Restaurar padrão" desfaz a personalização.

**Editar via API:**

```bash
# listar
curl -H "X-API-Key: $KEY" http://localhost:8000/api/v1/prompts

# atualizar
curl -X PATCH -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"content":"..."}' http://localhost:8000/api/v1/prompts/writer.user

# resetar
curl -X POST -H "X-API-Key: $KEY" \
  http://localhost:8000/api/v1/prompts/writer.user/reset
```

Variáveis `{entre chaves}` são obrigatórias e devem ser preservadas na edição.

---

## 📊 Observabilidade

Todas as chamadas LLM são rastreadas no LangFuse quando `LANGFUSE_ENABLED=true`. Habilitando, o pipeline emite spans por nó (outliner, researcher, writer, stylist, reviewer) + um span agregador `flux-capacitor.generate`. Refinos de slide emitem `flux-capacitor.refine-slide`.

Localmente, a tabela `interactions` grava cada chamada com latência, tokens (quando disponíveis) e payload truncado.

## 📎 Anexos de contexto (uploads)

O wizard aceita arquivos que alimentam o pipeline como material de referência. Formatos aceitos:

| Formato | Uso |
|---|---|
| `.md`, `.txt` | Texto lido diretamente |
| `.pdf` | Extração via `pypdf` (até 50 páginas) |
| `.docx` | Parágrafos e tabelas via `python-docx` |
| `.xlsx` | Planilhas via `openpyxl` (até 5 abas × 200 linhas) |
| `.csv` | Detecta delimitador automaticamente |
| `.png` `.jpg` `.jpeg` `.webp` `.gif` | Ficam disponíveis como URLs para o writer usar em slides |

**Fluxo:**
1. Usuário anexa arquivos no Step 1 → `POST /api/v1/uploads` (multipart)
2. Backend extrai texto, armazena em `data/uploads/<att_id>/<filename>` e registra em `attachments`
3. Ao gerar, `POST /api/v1/presentations` recebe `attachment_ids: []`
4. `presentation_service` consolida `context_text` (concatena `extracted_text` dos docs) e `image_urls` (URLs públicas das imagens) e injeta no `FluxState`
5. Os nós `outliner`, `researcher` e `writer` recebem blocos extras no prompt:
   - `CONTEXTO DE REFERÊNCIA:` com o texto extraído — orienta a LLM a ancorar o deck no material
   - `IMAGENS DISPONÍVEIS:` com as URLs exatas para uso em slides `visual_type: image` ou `![bg right:40%](url)`
6. Após a geração, os attachments são associados via `presentation_id` (FK) e citados no `meta.attachments`
7. No export HTML standalone, imagens `/uploads/…` são convertidas para data URIs em base64 → arquivo 100% portátil

**Limites:** 20MB por arquivo; texto truncado em 12.000 caracteres por arquivo antes de ir ao prompt.

**API:**

```bash
# upload
curl -X POST -H "X-API-Key: $KEY" \
  -F "file=@relatorio.pdf" \
  http://localhost:8000/api/v1/uploads
# -> {"id":"...","url":"/uploads/.../relatorio.pdf", ...}

# gerar usando anexos
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"topic":"...", "attachment_ids":["<att_id_1>","<att_id_2>"]}' \
  http://localhost:8000/api/v1/presentations

# deletar
curl -X DELETE -H "X-API-Key: $KEY" \
  http://localhost:8000/api/v1/uploads/<att_id>
```



Se `LANGFUSE_ENABLED=true` e as chaves forem fornecidas, todos os runs do grafo e refinamentos são enviados ao LangFuse com `trace_name`, `session_id` e `metadata` (tópico, nº de slides, instrução).

Além disso, **toda** interação é persistida localmente na tabela `interactions` (SQLite), consultável via `/api/v1/presentations/{id}/interactions` e agregada em `/api/v1/stats`.

---

## 💾 Módulo de consultas

Todo acesso a dados está centralizado em **`app/database/repository.py`**. A API e os serviços nunca escrevem SQL inline — sempre passam por funções puras como:

```python
await repo.create_presentation(session, **data)
await repo.list_slides(session, presentation_id)
await repo.log_interaction(session, kind="refine", ...)
await repo.interaction_stats(session, days=7)
```

---

## 🎨 Identidade visual

Paleta inspirada em **falagaiotto.com.br**:

| Token | Hex | Uso |
|---|---|---|
| `flux-500` | `#E67E22` | Accent primário |
| `flux-600` | `#D35400` | Accent forte |
| `flux-100` | `#FDF4E9` | Background soft |
| `flux-200` | `#FDE6CF` | Bordas / divisores |
| `flux-ink` | `#2B2B2B` | Texto principal |
| `flux-soft` | `#6B7280` | Texto secundário |

Fontes: **Quicksand** (display) + **Open Sans** (body). Bordas arredondadas `2xl`, sombras suaves, gradiente sutil laranja no background.

---

## 🧪 Teste rápido

```bash
# 1. Sobe a app
python run.py

# 2. Em outro terminal — health
curl http://localhost:8000/api/v1/health

# 3. Abre a UI
open http://localhost:8000
```

---

## 🗺️ Roadmap sugerido

- Suporte a Reveal.js (alternativa ao Marp)
- Upload de logo/branding custom
- Export direto para PPTX via LibreOffice headless
- Biblioteca de templates (pitch, aula, workshop)
- Compartilhamento por link público com slug

---

## 📄 Licença

MIT — © 2026 Sergio Gaiotto / Flux-Capacitor
