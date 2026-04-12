"""LangGraph pipeline definition — 6-node StateGraph with QA retry loop."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.ad_analyzer import ad_analyzer_node
from app.agents.code_modifier import code_modifier_node
from app.agents.copywriter import copywriter_node
from app.agents.cro_strategist import cro_strategist_node
from app.agents.page_scraper import page_scraper_node
from app.agents.qa_verifier import qa_verifier_node
from app.models.pipeline import PipelineState


def _should_retry(state: dict) -> str:
    """
    Conditional edge after QA Verifier.
    If QA failed and retries remain → loop back to Code Modifier.
    Otherwise → done.
    """
    qa_report = state.get("qa_report")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if qa_report and not qa_report.get("passed", True) and retry_count < max_retries:
        return "retry"
    return "done"


def build_graph() -> StateGraph:
    """Build and compile the 6-agent LangGraph pipeline."""
    graph = StateGraph(dict)  # Use dict state for LangGraph compatibility

    # Register agent nodes
    graph.add_node("ad_analyzer", ad_analyzer_node)
    graph.add_node("page_scraper", page_scraper_node)
    graph.add_node("cro_strategist", cro_strategist_node)
    graph.add_node("copywriter", copywriter_node)
    graph.add_node("code_modifier", code_modifier_node)
    graph.add_node("qa_verifier", qa_verifier_node)

    # Linear pipeline: ad_analyzer → page_scraper → cro_strategist → copywriter → code_modifier
    graph.set_entry_point("ad_analyzer")
    graph.add_edge("ad_analyzer", "page_scraper")
    graph.add_edge("page_scraper", "cro_strategist")
    graph.add_edge("cro_strategist", "copywriter")
    graph.add_edge("copywriter", "code_modifier")
    graph.add_edge("code_modifier", "qa_verifier")

    # Conditional retry edge: qa_verifier → code_modifier (retry) or END (done)
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
