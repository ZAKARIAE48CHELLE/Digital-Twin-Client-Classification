"""
OSMOS LangGraph Supervision — Runner & Entrypoint (Phase 8.7)
=============================================================
High-level execution entrypoint invoking the compiled LangGraph workflow,
converting serializable GraphState into OrchestratorOutput objects.

Constraint 1: Includes automatic fallback to legacy OrchestratorAgent if graph fails.
"""

import logging
from typing import Any, Dict, List, Optional
import pandas as pd

from agents.langgraph_supervision.graph_builder import get_compiled_supervision_graph
from agents.agent_schemas import (
    OrchestratorOutput,
    AgentOutput,
    EvidenceItem,
)
from agents.debate_schemas import DebateOutput, AgentConflict, AgentConsensus
from agents.orchestrator_agent import run_orchestrated_analysis


logger = logging.getLogger("OSMOS_LANGGRAPH_RUNNER")


def convert_graph_state_to_orchestrator_output(state: Dict[str, Any]) -> OrchestratorOutput:
    """Converts serializable SupervisionGraphState dictionary into an OrchestratorOutput object."""
    orch_dict = state.get("orchestrator_output", {})
    entity_id = state.get("entity_id") or orch_dict.get("entity_id", "Unknown")

    # 1. Convert AgentOutputs
    agent_outputs: List[AgentOutput] = []
    for o in state.get("agent_outputs", []):
        agent_outputs.append(
            AgentOutput(
                agent_id=o.get("agent_id", ""),
                agent_name=o.get("agent_name", ""),
                agent_role=o.get("agent_role", ""),
                status=o.get("status", "OK"),
                summary=o.get("summary", ""),
                observations=o.get("observations", []),
                risks=o.get("risks", []),
                opportunities=o.get("opportunities", []),
                recommendations=o.get("recommendations", []),
                confidence_score=float(o.get("confidence_score", 1.0)),
                evidence=o.get("evidence", []),
            )
        )

    # 2. Extract risks & opportunities
    all_risks = []
    all_opps = []
    all_recs = []
    for out in agent_outputs:
        all_risks.extend(out.risks)
        all_opps.extend(out.opportunities)
        all_recs.extend(out.recommendations)

    deb_dict = state.get("debate_output") or orch_dict.get("debate_output")

    return OrchestratorOutput(
        entity_id=entity_id,
        global_status=orch_dict.get("global_status", "OK"),
        final_summary=orch_dict.get("final_summary", "LangGraph multi-agent analysis completed."),
        agent_outputs=agent_outputs,
        consolidated_risks=list(set(all_risks)),
        consolidated_opportunities=list(set(all_opps)),
        final_recommendations=list(set(all_recs)),
        recommended_next_best_action=orch_dict.get("recommended_next_best_action", "Maintain active supervision."),
        debate_output=deb_dict,
        created_at=orch_dict.get("created_at"),
    )


def run_langgraph_supervision(
    entity_id: str,
    df: Optional[pd.DataFrame] = None,
    selected_agents: Optional[List[str]] = None,
    include_knowledge: bool = False,
    debate_mode: bool = True,
) -> OrchestratorOutput:
    """Main entrypoint executing multi-agent supervision via compiled LangGraph StateGraph."""
    str_entity_id = str(entity_id).strip()
    logger.info(f"Executing LangGraph Supervision Workflow for Entity [{str_entity_id}]...")

    graph = get_compiled_supervision_graph()
    if not graph:
        logger.warning(f"LangGraph unavailable. Falling back to legacy OrchestratorAgent for [{str_entity_id}].")
        return run_orchestrated_analysis(
            entity_id=str_entity_id,
            df=df,
            selected_agent_ids=selected_agents,
            include_knowledge=include_knowledge,
            debate_mode=debate_mode,
        )

    try:
        initial_state: Dict[str, Any] = {
            "entity_id": str_entity_id,
            "selected_agents": selected_agents,
            "include_knowledge": include_knowledge,
            "debate_mode": debate_mode,
            "agent_outputs": [],
            "core_agent_outputs": [],
            "operational_agent_outputs": [],
            "errors": [],
            "warnings": [],
        }

        # Invoke StateGraph
        final_state = graph.invoke(initial_state)
        return convert_graph_state_to_orchestrator_output(final_state)

    except Exception as e:
        logger.error(f"LangGraph execution exception for [{str_entity_id}]: {e}. Falling back to legacy orchestrator.")
        return run_orchestrated_analysis(
            entity_id=str_entity_id,
            df=df,
            selected_agent_ids=selected_agents,
            include_knowledge=include_knowledge,
            debate_mode=debate_mode,
        )
