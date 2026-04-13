"""Montagem do StateGraph LangGraph - Flux-Capacitor."""
from langgraph.graph import StateGraph, START, END
from app.agents.state import FluxState
from app.agents.nodes import outliner, researcher, writer, stylist, reviewer, finalizer
from app.core.observability import get_langfuse_callback


def build_graph():
    g = StateGraph(FluxState)
    g.add_node("outliner", outliner)
    g.add_node("researcher", researcher)
    g.add_node("writer", writer)
    g.add_node("stylist", stylist)
    g.add_node("reviewer", reviewer)
    g.add_node("finalizer", finalizer)

    g.add_edge(START, "outliner")
    g.add_edge("outliner", "researcher")
    g.add_edge("researcher", "writer")
    g.add_edge("writer", "stylist")
    g.add_edge("stylist", "reviewer")
    g.add_edge("reviewer", "finalizer")
    g.add_edge("finalizer", END)

    return g.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def run_pipeline(
    topic: str,
    audience: str | None = None,
    tone: str = "friendly",
    language: str = "pt-BR",
    theme: str = "modern-soft",
    num_slides: int = 8,
    session_id: str | None = None,
    context_text: str = "",
    image_urls: list[dict] | None = None,
) -> dict:
    graph = get_graph()
    state: FluxState = {
        "topic": topic,
        "audience": audience,
        "tone": tone,
        "language": language,
        "theme": theme,
        "num_slides": num_slides,
        "context_text": context_text,
        "image_urls": image_urls or [],
    }
    config = {}
    cb = get_langfuse_callback(
        trace_name="flux-capacitor.generate",
        session_id=session_id,
        metadata={"topic": topic, "num_slides": num_slides, "has_context": bool(context_text), "n_images": len(image_urls or [])},
    )
    if cb:
        config["callbacks"] = [cb]
    return await graph.ainvoke(state, config=config)


async def run_refine_slide(
    slide_title: str,
    slide_content: str,
    instruction: str,
    language: str = "pt-BR",
    session_id: str | None = None,
) -> dict:
    from langchain_core.messages import SystemMessage, HumanMessage
    from app.core.llm import get_llm
    from app.core.prompts import get_prompt
    from app.agents.nodes import _parse_json

    llm = get_llm(temperature=0.6)
    sys = get_prompt("system.friendly").format(language=language)
    prompt = get_prompt("refine.user").format(
        slide_title=slide_title,
        slide_content=slide_content,
        instruction=instruction,
    )
    cb = get_langfuse_callback(
        trace_name="flux-capacitor.refine-slide",
        session_id=session_id,
        metadata={"instruction": instruction[:80]},
    )
    config = {"callbacks": [cb]} if cb else {}
    resp = await llm.ainvoke(
        [SystemMessage(content=sys), HumanMessage(content=prompt)],
        config=config,
    )
    return _parse_json(resp.content)
