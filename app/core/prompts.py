"""Registry central de system prompts do Flux-Capacitor.

Os prompts padrão vivem aqui, mas podem ser sobrescritos via persistência
na tabela `prompts`. O pipeline sempre consulta `get_prompt(key)`.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from sqlalchemy.orm import Session
from app.database.connection import sync_engine
from app.database.models import Prompt


@dataclass(frozen=True)
class PromptDef:
    key: str
    label: str
    description: str
    content: str
    variables: tuple[str, ...] = ()


# ---------- DEFAULTS ----------
SYSTEM_FRIENDLY = """Você é um designer de experiência instrucional especializado em \
apresentações dinâmicas, amigáveis e DENSAS em conteúdo, usando Marp. Seu estilo \
é 'Modern Soft': tom conversacional, afirmações relacionáveis, títulos que convidam \
(não impõem), linguagem acessível mas substantiva. Sempre responda em {language}.

PRINCÍPIOS DE CONTEÚDO (obrigatórios em toda apresentação):
Toda apresentação deve cobrir, distribuída entre os slides conforme o tópico exigir:
1. FUNDAMENTOS & CONTEXTO — o que é, de onde vem, por que importa agora
2. CONCEITOS-CHAVE — definições, termos, princípios centrais
3. APLICAÇÕES PRÁTICAS — casos de uso reais, exemplos concretos, setores onde se aplica
4. ORIENTAÇÕES & BOAS PRÁTICAS — como começar, passos, frameworks, metodologias
5. PRÓS & CONTRAS — vantagens e limitações, com honestidade
6. BENEFÍCIOS & DESAFIOS — o que se ganha, o que exige superar
7. PRÓXIMOS PASSOS — CTA, aprofundamento, recursos

Nem todo slide precisa cobrir uma dessas seções, mas o DECK COMO UM TODO precisa \
contemplá-las. Respeite rigorosamente o tópico e o público-alvo.

RECURSOS MARP DISPONÍVEIS (use com critério):
- **Tabelas markdown** — RECURSO PREFERENCIAL para dados, comparações, prós/contras, \
frameworks, critérios, etapas com descrição, benefícios/desafios. Tabelas bem feitas \
organizam informação melhor que parágrafos em 80% dos casos densos.
- Diagramas Mermaid (flowchart, sequenceDiagram, gantt, mindmap) — para processos, \
arquiteturas, linhas do tempo
- Fórmulas KaTeX: inline `$...$`, bloco `$$...$$`
- Blocos de código com linguagem: ```python, ```javascript, ```sql, ```yaml
- Background directives: `![bg right:40%](url)`, `![bg left:30% blur](url)`, `![bg opacity:.25](url)`
- Ênfase: **negrito** para conceitos-chave, *itálico* para nuance, citações com `>`

REGRA DE DENSIDADE: cada slide deve entregar valor real, não ser decorativo. \
Conteúdo substantivo, mas apresentado com espaço em branco e hierarquia visual. \
Limite: ~60 palavras de texto puro por slide (código/diagrama/tabela não contam)."""


OUTLINER_USER = """Tópico: {topic}
Público-alvo: {audience}
Tom: {tone}

Crie um outline de exatamente {num_slides} slides para uma apresentação densa e \
friendly-first que cubra os 7 princípios de conteúdo (fundamentos, conceitos, \
aplicações, orientações, prós/contras, benefícios/desafios, próximos passos) \
distribuídos de forma proporcional ao tópico.

ESTRUTURA RECOMENDADA (adapte ao tópico):
- 1 slide: abertura/hook (cover)
- 1-2 slides: fundamentos e contexto (por que importa agora)
- 2-3 slides: conceitos-chave com definições claras
- 2-3 slides: aplicações práticas e casos de uso
- 1-2 slides: orientações, boas práticas, frameworks
- 1-2 slides: prós/contras ou benefícios/desafios (idealmente em tabela)
- 1 slide: próximos passos / CTA

Para cada slide, defina um 'visual_type' adequado:
- "cover": capa com background grande
- "prose": texto conceitual com ícone (use apenas quando não couber em formato estruturado)
- "mermaid": diagrama de fluxo/processo/arquitetura/mindmap
- "math": fórmula matemática em destaque
- "code": bloco de código
- "table": **PREFERENCIAL** para comparações, prós/contras, benefícios/desafios, frameworks, critérios, etapas com descrição, dados numéricos, tipologias, antes/depois, matrizes, checklists ricos
- "image": slide com imagem dominante (bg left/right)
- "quote": citação inspiradora de especialista ou dado marcante

REGRA DE OURO PARA TABELAS: sempre que o slide envolver 2+ itens comparáveis, \
use "table". Não subestime o poder de uma tabela bem feita — ela organiza \
informação melhor que prose em 80% dos casos densos.

Varie os tipos — um deck bom alterna ritmo. Em um deck de 8+ slides, \
recomenda-se PELO MENOS 2 tabelas.

Retorne JSON estrito:
{{
  "title": "Título principal",
  "slides": [
    {{
      "title": "Pergunta/afirmação amigável",
      "purpose": "qual dos 7 princípios este slide cobre e qual info-chave entrega",
      "visual_type": "prose",
      "icon": "nome-lucide",
      "image_keyword": "palavra-chave unsplash"
    }}
  ]
}}
Ícones Lucide: sparkles, lightbulb, rocket, heart-handshake, compass, zap, target, \
users, chart-line, code, brain, message-circle, book-open, check, star, map, clock, \
shield, wand-2, play, alert-triangle, scale, trending-up, layers, settings, \
puzzle, flag, milestone.
Títulos: perguntas ou afirmações acolhedoras, nunca imperativas."""


RESEARCH_USER = """Você vai produzir um BRIEFING DE CONTEÚDO denso para alimentar a \
escrita dos slides. Não escreva slides ainda — produza fatos, conceitos, exemplos.

Tópico: {topic}
Público-alvo: {audience}
Outline planejado:
{outline_json}

Para cada slide do outline, produza matéria-prima rica que o writer usará:
- 1-3 FATOS/DADOS concretos (números, marcos, estatísticas plausíveis)
- 2-4 CONCEITOS com definições curtas
- 1-2 EXEMPLOS PRÁTICOS reais (empresas, casos, setores)
- quando aplicável: 2-3 PRÓS e 2-3 CONTRAS
- 1 INSIGHT ou nuance menos óbvia

Retorne JSON estrito:
{{
  "research": [
    {{
      "slide_index": 0,
      "facts": ["...", "..."],
      "concepts": [{{"term": "...", "definition": "..."}}],
      "examples": ["..."],
      "pros": ["..."],
      "cons": ["..."],
      "insight": "..."
    }}
  ]
}}
Seja factual e substantivo. Se não souber um dado específico, generalize ("estudos \
recentes indicam...") sem inventar números falsos. Foque em conteúdo que agregue valor."""


WRITER_USER = """Para cada item do outline, escreva o content_md denso e amigável, \
consumindo o briefing de pesquisa.

Regras por visual_type:
- "cover"    -> frase-chave curta + sub-frase provocativa
- "prose"    -> 3-5 linhas substantivas com conceitos do briefing, separadas por \
linha em branco. Use **negrito** em termos-chave. Pode incluir 1 dado/exemplo.
- "mermaid"  -> bloco ```mermaid``` com flowchart/sequenceDiagram/mindmap apropriado \
ao conteúdo + 1 linha de contexto acima OU abaixo
- "math"     -> `$$ ... $$` com a fórmula + 2 linhas explicando significado e aplicação
- "code"     -> ```<linguagem> bloco relevante (até 14 linhas) + 2 linhas de contexto \
explicando o que faz
- "table"    -> **TABELA RICA E SUBSTANTIVA**:
    * 2 a 4 colunas (ideais: 3)
    * 3 a 6 linhas de dados (idealmente 4-5)
    * Cabeçalho em negrito implícito pela sintaxe `| Coluna |`
    * Cada célula com conteúdo significativo — não apenas rótulos vazios
    * Use para prós/contras, frameworks, etapas com descrição, comparações, \
benefícios/desafios, critérios, tipologias, antes/depois, checklists ricos
    * Formato markdown padrão:
      ```
      | Aspecto | Detalhe A | Detalhe B |
      |---|---|---|
      | Linha1 | ... | ... |
      ```
    * + 1 linha curta de intro ANTES da tabela (contextualiza)
    * SEM linha após a tabela (deixa a tabela respirar)
- "image"    -> `![bg right:40%](url)` + 3-4 linhas de texto substantivo (se houver \
imagem disponível na lista de IMAGENS DISPONÍVEIS, use EXATAMENTE a URL fornecida)
- "quote"    -> `> Citação ou dado impactante`  + linha de contexto em itálico

REGRA CRÍTICA — UPGRADE PARA TABELA: se o outline pedir "prose" mas o conteúdo \
envolver 2+ itens comparáveis, listas estruturadas, prós/contras, ou qualquer \
informação que fica mais clara em formato tabular, **MUDE o visual_type para \
"table"** e reorganize o content_md como tabela markdown. Priorize tabelas \
sempre que possível.

REGRAS DE SEGURANÇA VISUAL (NÃO QUEBRAR):
- NUNCA inclua ícones como `<i data-lucide="...">`, `<i class="icon">` ou HTML \
similar no content_md. Ícones já são aplicados automaticamente pelo renderer \
como emoji inline no título.
- NUNCA use emojis soltos em linhas separadas (como `🪄` sozinho numa linha) — \
eles viram imagens gigantes no Marp. Se quiser ênfase visual, use **negrito** \
ou coloque o emoji INLINE no texto (ex.: "A IA **acelera** ⚡ decisões...").
- NÃO insira `![título](url)` para ilustrações decorativas no content_md. Imagens \
aparecem apenas via visual_type: "image" (o renderer cuida do background).
- Para MERMAID, sempre use a sintaxe em bloco de código:
  ```mermaid
  flowchart TD
      A[Nó A] --> B[Nó B]
  ```
  Rótulos de nós devem ser CURTOS (até 3-4 palavras). Evite caracteres especiais \
em rótulos (use espaços e letras/números apenas).

Outline:
{outline_json}

Briefing de pesquisa (use como matéria-prima — cite fatos, incorpore conceitos, \
mencione exemplos):
{research_json}

IMPORTANTE: cada slide deve ENTREGAR VALOR real. Não faça slides vazios ou \
decorativos. Integre os fatos, conceitos e exemplos do briefing naturalmente no texto.

Retorne JSON estrito:
{{
  "slides": [
    {{
      "order_index": 0,
      "title": "...",
      "content_md": "...",
      "icon": "nome-lucide",
      "image_keyword": "palavra-chave unsplash",
      "visual_type": "prose|mermaid|math|code|table|image|quote|cover",
      "transition": "fade",
      "notes": "speaker notes de 2-3 frases com contexto adicional para o apresentador"
    }}
  ]
}}"""


REFINE_USER = """Refine este slide conforme a instrução, mantendo densidade e o \
estilo friendly-first. Se a instrução pedir um formato (mermaid, tabela, código, \
fórmula), adapte o content_md para esse formato usando a sintaxe Marp apropriada.

Título atual: {slide_title}
Conteúdo atual:
{slide_content}

Instrução: {instruction}

Retorne JSON estrito:
{{"title": "...", "content_md": "...", "icon": "...", "image_keyword": "...", "visual_type": "...", "notes": "..."}}"""


DEFAULTS: Dict[str, PromptDef] = {
    "system.friendly": PromptDef(
        key="system.friendly",
        label="System · Friendly-First",
        description="System prompt base compartilhado por todos os nós do grafo. Define tom, princípios de conteúdo (7 pilares) e recursos Marp disponíveis.",
        content=SYSTEM_FRIENDLY,
        variables=("language",),
    ),
    "outliner.user": PromptDef(
        key="outliner.user",
        label="Outliner · User",
        description="Prompt que gera o outline inicial da apresentação, definindo títulos, propósito e visual_type de cada slide.",
        content=OUTLINER_USER,
        variables=("topic", "audience", "tone", "num_slides"),
    ),
    "research.user": PromptDef(
        key="research.user",
        label="Researcher · User",
        description="Prompt que produz o briefing denso (fatos, conceitos, exemplos, prós/contras) que alimenta o writer.",
        content=RESEARCH_USER,
        variables=("topic", "audience", "outline_json"),
    ),
    "writer.user": PromptDef(
        key="writer.user",
        label="Writer · User",
        description="Prompt que consome outline + briefing e escreve o content_md de cada slide com regras específicas por visual_type.",
        content=WRITER_USER,
        variables=("outline_json", "research_json"),
    ),
    "refine.user": PromptDef(
        key="refine.user",
        label="Refine · User",
        description="Prompt usado ao pedir ajuste slide-a-slide pela interface (botão 'Pedir ajuste à IA').",
        content=REFINE_USER,
        variables=("slide_title", "slide_content", "instruction"),
    ),
}


# ---------- ACESSO ----------
def seed_defaults() -> None:
    """Popula a tabela com os prompts padrão (idempotente)."""
    with Session(sync_engine) as s:
        for d in DEFAULTS.values():
            existing = s.get(Prompt, d.key)
            if existing is None:
                s.add(Prompt(
                    key=d.key,
                    label=d.label,
                    description=d.description,
                    content=d.content,
                    variables=",".join(d.variables),
                ))
        s.commit()


def get_prompt(key: str) -> str:
    """Retorna o conteúdo atual do prompt (DB se existir, senão default)."""
    with Session(sync_engine) as s:
        row = s.get(Prompt, key)
        if row:
            return row.content
    return DEFAULTS[key].content


def set_prompt(key: str, content: str) -> None:
    if key not in DEFAULTS:
        raise KeyError(f"prompt desconhecido: {key}")
    with Session(sync_engine) as s:
        row = s.get(Prompt, key)
        if row:
            row.content = content
        else:
            d = DEFAULTS[key]
            s.add(Prompt(
                key=d.key, label=d.label, description=d.description,
                content=content, variables=",".join(d.variables),
            ))
        s.commit()


def reset_prompt(key: str) -> str:
    if key not in DEFAULTS:
        raise KeyError(f"prompt desconhecido: {key}")
    d = DEFAULTS[key]
    set_prompt(key, d.content)
    return d.content


def list_prompts() -> list[dict]:
    """Lista prompts com conteúdo efetivo atual."""
    out = []
    with Session(sync_engine) as s:
        for d in DEFAULTS.values():
            row = s.get(Prompt, d.key)
            out.append({
                "key": d.key,
                "label": d.label,
                "description": d.description,
                "content": row.content if row else d.content,
                "variables": list(d.variables),
                "is_default": row is None or row.content == d.content,
                "updated_at": row.updated_at.isoformat() if row else None,
            })
    return out
