"""
OSMOS LangGraph Supervision — Router Logic (Phase 8.7)
======================================================
Conditional edge routing functions checking state flags (errors, debate mode).
"""

import logging
from agents.langgraph_supervision.graph_state import SupervisionGraphState

logger = logging.getLogger("OSMOS_LANGGRAPH_ROUTER")


def check_context_errors(state: SupervisionGraphState) -> str:
    """Routes to error_handler if build_context encountered an error, else proceeds to core agents."""
    if state.get("errors"):
        logger.warning(f"Routing to error handler due to context errors: {state.get('errors')}")
        return "error_handler"
    return "run_core_agents"


def should_run_debate(state: SupervisionGraphState) -> str:
    """Routes to debate node if debate_mode is True, else proceeds directly to finalize."""
    if state.get("debate_mode", True):
        return "debate"
    return "finalize"
