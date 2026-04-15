"""LangGraph pipeline definition — 6-node StateGraph with parallel fan-out and QA retry loop."""

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import GraphState
from app.agents.ad_analyzer import ad_analyzer_node
from app.agents.code_modifier import code_modifier_node
from app.agents.copywriter import copywriter_node
from app.agents.cro_strategist import cro_strategist_node
from app.agents.page_scraper import page_scraper_node
from app.agents.qa_verifier import qa_verifier_node


def _should_retry(state: GraphState) -> str:
    """
    Conditional edge after QA Verifier.
    If QA failed and retries remain → loop back to Code Modifier.
    Otherwise → done.
    """
    qa_report = state.get("qa_report") or {}
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if qa_report and not qa_report.get("passed", True) and retry_count < max_retries:
        return "retry"
    return "done"


def build_graph() -> StateGraph:
    """
    Build and compile the 6-agent LangGraph pipeline.

    Topology (with parallel fan-out):

        START ──┬── ad_analyzer  ──┐
                │                  ├── cro_strategist → copywriter → code_modifier → qa_verifier
                └── page_scraper ──┘                                                     │
                                                                                    (retry?) ──→ code_modifier
                                                                                         └──→ END

    ad_analyzer and page_scraper run in PARALLEL (fan-out from START).
    cro_strategist waits for BOTH to complete before starting (fan-in).
    This saves ~10-15 seconds per run since scraping is I/O-bound while
    the ad is being analyzed by Flash.
    """
    graph = StateGraph(GraphState)

    # Register agent nodes
    graph.add_node("ad_analyzer", ad_analyzer_node)
    graph.add_node("page_scraper", page_scraper_node)
    graph.add_node("cro_strategist", cro_strategist_node)
    graph.add_node("copywriter", copywriter_node)
    graph.add_node("code_modifier", code_modifier_node)
    graph.add_node("qa_verifier", qa_verifier_node)

    # ── Fan-out: START → ad_analyzer AND page_scraper (run in parallel) ────
    graph.add_edge(START, "ad_analyzer")
    graph.add_edge(START, "page_scraper")

    # ── Fan-in: both feed into cro_strategist (waits for both to complete) ─
    graph.add_edge("ad_analyzer", "cro_strategist")
    graph.add_edge("page_scraper", "cro_strategist")

    # ── Sequential remainder ───────────────────────────────────────────────
    graph.add_edge("cro_strategist", "copywriter")
    graph.add_edge("copywriter", "code_modifier")
    graph.add_edge("code_modifier", "qa_verifier")

    # ── Conditional retry loop ─────────────────────────────────────────────
    graph.add_conditional_edges(
        "qa_verifier",
        _should_retry,
        {
            "retry": "code_modifier",
            "done": END,
        },
    )

    return graph.compile(checkpointer=MemorySaver())


# Module-level singleton — compiled once, shared across all requests
pipeline_graph = build_graph()
