"""
OSMOS LangGraph Supervision — Node Functions (Phase 8.7)
=========================================================
Plain Python node functions wrapping existing OSMOS agent classes and debate modules.

Constraint 2: Wraps existing agents without altering internal logic.
Constraint 3: Pure read-only state updates returning serializable dictionaries.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agents.langgraph_supervision.graph_state import SupervisionGraphState
from agents.context_builder import build_entity_agent_context, AgentContext
from agents.agent_registry import (
    get_agent,
    CORE_AGENT_IDS,
    OPERATIONAL_AGENT_IDS,
    AGENT_REGISTRY,
)

from agents.result_aggregator import (
    aggregate_agent_status,
    choose_next_best_action,
    merge_risks,
    merge_recommendations,
)

from agents.debate_engine import run_deterministic_debate
from agents.orchestrator_agent import OrchestratorAgent



logger = logging.getLogger("OSMOS_LANGGRAPH_NODES")


def _agent_context_to_dict(ctx: AgentContext) -> Dict[str, Any]:
    """Helper to convert AgentContext object to serializable dictionary for LangGraph state."""
    return {
        "entity_id": ctx.entity_id,
        "storage_mode": ctx.storage_mode,
        "latest_digital_twin": ctx.latest_digital_twin,
        "latest_clv": ctx.latest_clv,
        "latest_rfm": ctx.latest_rfm,
        "latest_classification": ctx.latest_classification,
        "latest_segment": ctx.latest_segment,
        "latest_persona": ctx.latest_persona,
        "recent_events": ctx.recent_events,
        "campaign_history": ctx.campaign_history,
        "journey_history": ctx.journey_history,
        "knowledge_results": ctx.knowledge_results,
        "documentation_context": ctx.documentation_context,
        "decision_memory": ctx.decision_memory,
        "previous_agent_runs": ctx.previous_agent_runs,
        "approval_history": ctx.approval_history,
    }


def _dict_to_agent_context(ctx_dict: Dict[str, Any]) -> AgentContext:
    """Helper to re-hydrate AgentContext dataclass from serializable dictionary."""
    return AgentContext(
        entity_id=ctx_dict.get("entity_id", ""),
        storage_mode=ctx_dict.get("storage_mode", "excel"),
        latest_digital_twin=ctx_dict.get("latest_digital_twin", {}),
        latest_clv=ctx_dict.get("latest_clv", {}),
        latest_rfm=ctx_dict.get("latest_rfm", {}),
        latest_classification=ctx_dict.get("latest_classification", {}),
        latest_segment=ctx_dict.get("latest_segment", "Unknown"),
        latest_persona=ctx_dict.get("latest_persona", "Unknown"),
        recent_events=ctx_dict.get("recent_events", []),
        campaign_history=ctx_dict.get("campaign_history", []),
        journey_history=ctx_dict.get("journey_history", []),
        knowledge_results=ctx_dict.get("knowledge_results", []),
        documentation_context=ctx_dict.get("documentation_context", ""),
        decision_memory=ctx_dict.get("decision_memory", []),
        previous_agent_runs=ctx_dict.get("previous_agent_runs", []),
        approval_history=ctx_dict.get("approval_history", []),
    )


def build_context_node(state: SupervisionGraphState) -> Dict[str, Any]:
    """Node 1: Builds serializable AgentContext dictionary."""
    entity_id = state.get("entity_id", "")
    include_knowledge = state.get("include_knowledge", False)

    try:
        ctx_obj = build_entity_agent_context(entity_id=entity_id, include_knowledge=include_knowledge)
        ctx_dict = _agent_context_to_dict(ctx_obj)
        return {
            "context": ctx_dict,
            "storage_mode": ctx_obj.storage_mode,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error in build_context_node for [{entity_id}]: {e}")
        return {
            "errors": state.get("errors", []) + [f"Build context error: {str(e)}"],
        }


def run_core_agents_node(state: SupervisionGraphState) -> Dict[str, Any]:
    """Node 2: Executes selected Core Analytical Agents (Digital Twin, CLV, Churn, Persona)."""
    ctx_dict = state.get("context", {})
    if not ctx_dict:
        return {"errors": state.get("errors", []) + ["Missing context in run_core_agents_node"]}

    ctx_obj = _dict_to_agent_context(ctx_dict)
    selected_agents = state.get("selected_agents") or CORE_AGENT_IDS

    core_outputs: List[Dict[str, Any]] = []
    for agent_id in CORE_AGENT_IDS:
        if selected_agents and agent_id not in selected_agents:
            continue
        agent = get_agent(agent_id)
        if agent:
            try:
                res = agent.safe_analyze(ctx_obj)
                core_outputs.append(res.to_dict())
            except Exception as e:
                logger.error(f"Core agent [{agent_id}] error: {e}")

    existing_outputs = state.get("agent_outputs", [])
    return {
        "core_agent_outputs": core_outputs,
        "agent_outputs": existing_outputs + core_outputs,
    }


def run_operational_agents_node(state: SupervisionGraphState) -> Dict[str, Any]:
    """Node 3: Executes selected Operational Agents (Campaign, Journey, Database Audit, UI/UX)."""
    ctx_dict = state.get("context", {})
    if not ctx_dict:
        return {"errors": state.get("errors", []) + ["Missing context in run_operational_agents_node"]}

    ctx_obj = _dict_to_agent_context(ctx_dict)
    selected_agents = state.get("selected_agents") or list(AGENT_REGISTRY.keys())

    op_outputs: List[Dict[str, Any]] = []
    for agent_id in OPERATIONAL_AGENT_IDS:
        if selected_agents and agent_id not in selected_agents:
            continue
        agent = get_agent(agent_id)
        if agent:
            try:
                res = agent.safe_analyze(ctx_obj)
                op_outputs.append(res.to_dict())
            except Exception as e:
                logger.error(f"Operational agent [{agent_id}] error: {e}")

    existing_outputs = state.get("agent_outputs", [])
    return {
        "operational_agent_outputs": op_outputs,
        "agent_outputs": existing_outputs + op_outputs,
    }


def aggregate_results_node(state: SupervisionGraphState) -> Dict[str, Any]:
    """Node 4: Aggregates agent outputs into preliminary orchestrator summary."""
    agent_outputs = state.get("agent_outputs", [])
    from agents.agent_schemas import AgentOutput

    # Re-hydrate AgentOutput list for helper functions
    fake_outputs = [
        AgentOutput(
            agent_id=o.get("agent_id", ""),
            agent_name=o.get("agent_name", ""),
            status=o.get("status", "OK"),
            summary=o.get("summary", ""),
            findings=o.get("findings", []),
            risks=o.get("risks", []),
            opportunities=o.get("opportunities", []),
            recommendations=o.get("recommendations", []),
            evidence_citations=o.get("evidence_citations", []),
            priority_score=o.get("priority_score", 0.0),
        )
        for o in agent_outputs
    ]

    global_status = aggregate_agent_status(fake_outputs)
    nba = choose_next_best_action(fake_outputs)
    summary = f"Supervision complete for {len(agent_outputs)} active agents with status {global_status}."

    return {
        "orchestrator_output": {
            "global_status": global_status,
            "recommended_next_best_action": nba,
            "final_summary": summary,
            "evidence_traceability": [],
        }
    }


def debate_node(state: SupervisionGraphState) -> Dict[str, Any]:
    """Node 5: Runs deterministic Agent Collaboration & Debate engine if enabled."""
    if not state.get("debate_mode", True):
        return {"debate_output": {}, "conflicts": [], "consensus": {}}

    entity_id = state.get("entity_id", "")
    agent_outputs = state.get("agent_outputs", [])
    ctx_dict = state.get("context", {})
    ctx_obj = _dict_to_agent_context(ctx_dict) if ctx_dict else None

    try:
        deb_report = run_deterministic_debate(
            entity_id=entity_id,
            agent_outputs=agent_outputs,
            context=ctx_obj,
        )
        deb_dict = deb_report.to_dict()
        conflicts = deb_report.conflicts or []
        consensus = deb_report.consensus or {}

        return {
            "debate_output": deb_dict,
            "conflicts": conflicts,
            "consensus": consensus,
        }
    except Exception as e:
        logger.error(f"Debate node error for [{entity_id}]: {e}")
        return {"debate_output": {}, "conflicts": [], "consensus": {}}


def finalize_orchestration_node(state: SupervisionGraphState) -> Dict[str, Any]:
    """Node 6: Finalizes complete orchestrator output dictionary."""
    entity_id = state.get("entity_id", "")
    agent_outputs = state.get("agent_outputs", [])
    debate_output = state.get("debate_output", {})
    consensus = state.get("consensus", {})
    orch_base = state.get("orchestrator_output", {})

    global_status = orch_base.get("global_status", "OK")
    nba = orch_base.get("recommended_next_best_action", "Maintain active supervision.")
    summary = orch_base.get("final_summary", "Multi-agent analysis completed.")

    if consensus and consensus.get("priority_action"):
        nba = consensus.get("priority_action")
        if consensus.get("reasoning_summary"):
            summary += f" [Debate Consensus: {consensus.get('reasoning_summary')}]"

    final_orch = {
        "entity_id": entity_id,
        "global_status": global_status,
        "recommended_next_best_action": nba,
        "final_summary": summary,
        "agent_outputs": agent_outputs,
        "debate_output": debate_output,
        "consensus": consensus,
        "evidence_traceability": orch_base.get("evidence_traceability", []),
        "created_at": state.get("created_at", datetime.now(timezone.utc).isoformat()),
        "storage_mode": state.get("storage_mode", "excel"),
    }

    return {"orchestrator_output": final_orch}


from agents.debate_engine import run_deterministic_debate
from agents.orchestrator_agent import OrchestratorAgent


def prepare_approval_actions_node(state: SupervisionGraphState) -> Dict[str, Any]:
    """Node 7: Prepares pending approval queue actions (read-only, does NOT persist to DB)."""
    orch_output = state.get("orchestrator_output", {})
    agent_outputs = state.get("agent_outputs", [])
    entity_id = state.get("entity_id", "")

    try:
        from agents.agent_schemas import OrchestratorOutput, AgentOutput
        # Temporary re-hydration to use existing helper function
        fake_outputs = [
            AgentOutput(
                agent_id=o.get("agent_id", ""),
                agent_name=o.get("agent_name", ""),
                status=o.get("status", "OK"),
                summary=o.get("summary", ""),
                recommendations=o.get("recommendations", []),
                priority_score=o.get("priority_score", 0.0),
            )
            for o in agent_outputs
        ]
        fake_orch = OrchestratorOutput(
            entity_id=entity_id,
            global_status=orch_output.get("global_status", "OK"),
            recommended_next_best_action=orch_output.get("recommended_next_best_action", ""),
            final_summary=orch_output.get("final_summary", ""),
            agent_outputs=fake_outputs,
        )

        orch_instance = OrchestratorAgent()
        appr_items = orch_instance.prepare_approval_actions(fake_orch)
        return {"approval_actions": appr_items}
    except Exception as e:
        logger.error(f"Prepare approval actions node error: {e}")
        return {"approval_actions": []}


def error_handler_node(state: SupervisionGraphState) -> Dict[str, Any]:
    """Node 8: Fallback node formatting errors safely without crashing."""
    errors = state.get("errors", ["Unknown supervision graph execution error."])
    logger.warning(f"Supervision graph error handler triggered: {errors}")

    return {
        "orchestrator_output": {
            "entity_id": state.get("entity_id", "Unknown"),
            "global_status": "Warning",
            "recommended_next_best_action": "Review system error logs and retry supervision.",
            "final_summary": f"Supervision workflow completed with warnings: {'; '.join(errors)}",
            "agent_outputs": state.get("agent_outputs", []),
            "debate_output": {},
            "consensus": {},
            "evidence_traceability": [],
        }
    }
