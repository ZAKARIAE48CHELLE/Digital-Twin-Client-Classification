"""
OSMOS LangGraph Supervision — Graph Builder (Phase 8.7)
========================================================
Constructs and compiles the LangGraph StateGraph workflow.
"""

import logging
from typing import Any, Optional

from agents.langgraph_supervision.graph_state import SupervisionGraphState
from agents.langgraph_supervision.graph_nodes import (
    build_context_node,
    run_core_agents_node,
    run_operational_agents_node,
    aggregate_results_node,
    debate_node,
    finalize_orchestration_node,
    prepare_approval_actions_node,
    error_handler_node,
)
from agents.langgraph_supervision.graph_router import (
    check_context_errors,
    should_run_debate,
)

logger = logging.getLogger("OSMOS_LANGGRAPH_BUILDER")

_compiled_graph_cache = None


def build_supervision_graph():
    """Builds and compiles the StateGraph for multi-agent supervision."""
    try:
        from langgraph.graph import StateGraph, START, END

        builder = StateGraph(SupervisionGraphState)

        # 1. Add Nodes
        builder.add_node("build_context", build_context_node)
        builder.add_node("run_core_agents", run_core_agents_node)
        builder.add_node("run_operational_agents", run_operational_agents_node)
        builder.add_node("aggregate_results", aggregate_results_node)
        builder.add_node("debate", debate_node)
        builder.add_node("finalize", finalize_orchestration_node)
        builder.add_node("prepare_approval_actions", prepare_approval_actions_node)
        builder.add_node("error_handler", error_handler_node)

        # 2. Add Edges & Conditional Routing
        builder.add_edge(START, "build_context")

        builder.add_conditional_edges(
            "build_context",
            check_context_errors,
            {
                "run_core_agents": "run_core_agents",
                "error_handler": "error_handler",
            },
        )

        builder.add_edge("run_core_agents", "run_operational_agents")
        builder.add_edge("run_operational_agents", "aggregate_results")

        builder.add_conditional_edges(
            "aggregate_results",
            should_run_debate,
            {
                "debate": "debate",
                "finalize": "finalize",
            },
        )

        builder.add_edge("debate", "finalize")
        builder.add_edge("finalize", "prepare_approval_actions")
        builder.add_edge("prepare_approval_actions", END)
        builder.add_edge("error_handler", END)

        compiled = builder.compile()
        logger.info("Successfully compiled LangGraph Multi-Agent Supervision StateGraph.")
        return compiled

    except Exception as e:
        logger.error(f"Failed to build LangGraph StateGraph: {e}")
        return None


def get_compiled_supervision_graph():
    """Returns singleton compiled supervision graph."""
    global _compiled_graph_cache
    if _compiled_graph_cache is None:
        _compiled_graph_cache = build_supervision_graph()
    return _compiled_graph_cache
