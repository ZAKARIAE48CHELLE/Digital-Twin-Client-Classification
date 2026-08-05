"""
OSMOS Multi-Agent Supervision Layer — Debate Engine (Phase 8.4)
===============================================================
Deterministic debate and collaboration engine for multi-agent cross-review,
conflict detection, consensus synthesis, and debate summary formatting.

Read-Only Guarantee: Pure analytical evaluation. Zero database or DataFrame mutations.
"""

import logging
from typing import Any, Dict, List, Optional
from agents.debate_schemas import AgentDebateStatement, DebateOutput
from agents.conflict_detector import detect_all_conflicts
from agents.consensus_builder import build_consensus

logger = logging.getLogger("OSMOS_DEBATE_ENGINE")


def build_agent_statements(agent_outputs: List[Any]) -> List[AgentDebateStatement]:
    """
    Extracts structured debate statements from specialized agent outputs.
    Assigns position, concern level, and proposed action per agent.
    """
    statements: List[AgentDebateStatement] = []

    for idx, out in enumerate(agent_outputs or [], start=1):
        if isinstance(out, dict):
            aid = out.get("agent_id", f"agent_{idx}")
            aname = out.get("agent_name", "Specialized Agent")
            status = out.get("status", "OK")
            summary = out.get("summary", "")
            recs = out.get("recommendations", [])
            ev = out.get("evidence", [])
            conf = float(out.get("confidence_score", 0.80))
        else:
            aid = out.agent_id
            aname = out.agent_name
            status = out.status
            summary = out.summary
            recs = out.recommendations or []
            ev = getattr(out, "evidence", []) or []
            conf = float(out.confidence_score)

        # Map status to concern level
        concern_map = {
            "OK": "Low",
            "Warning": "Medium",
            "Critical": "Critical",
            "Insufficient Data": "Low",
            "Error": "High",
        }
        concern = concern_map.get(status, "Medium")
        prop_action = recs[0] if recs else summary

        ev_strings = [
            f"{item.get('metric_name', '')}: {item.get('value', '')} (Ref: {item.get('threshold', '')})"
            for item in ev if isinstance(item, dict)
        ] if ev else [summary]

        statements.append(
            AgentDebateStatement(
                statement_id=f"STMT_{aid.upper()}",
                agent_id=aid,
                agent_name=aname,
                position=summary,
                supporting_evidence=ev_strings[:3],
                concern_level=concern,
                proposed_action=prop_action,
                confidence_score=conf,
            )
        )

    return statements


def compare_agent_positions(agent_statements: List[AgentDebateStatement]) -> List[Dict[str, Any]]:
    """Returns structured comparison list of agent positions for UI rendering."""
    return [stmt.to_dict() for stmt in agent_statements]


def generate_debate_summary(debate_output: DebateOutput) -> str:
    """Generates a comprehensive human-readable summary of debate results."""
    consensus = debate_output.consensus or {}
    status = consensus.get("consensus_status", "Unknown")
    priority = consensus.get("priority_action", "None")
    conflicts = debate_output.conflicts or []

    summary = (
        f"Agent Debate Evaluation for Entity [{debate_output.entity_id}]: "
        f"Consensus Status: '{status}'. Priority Action: '{priority}'. "
        f"Total Statements: {len(debate_output.agent_statements)}. "
        f"Conflicts Identified: {len(conflicts)}."
    )
    return summary


def run_deterministic_debate(
    agent_outputs: List[Any],
    entity_id: str = "P_DEMO_001",
    context: Any = None,
) -> DebateOutput:
    """
    Main entrypoint for executing deterministic agent debate.
    1. Extracts agent statements
    2. Runs conflict detection
    3. Synthesizes consensus and priority action
    4. Generates debate output
    """
    logger.info(f"Running deterministic agent debate for Entity [{entity_id}] across {len(agent_outputs or [])} agents...")

    statements = build_agent_statements(agent_outputs)
    conflicts = detect_all_conflicts(agent_outputs)
    consensus = build_consensus(agent_outputs, conflicts)

    stmt_dicts = [s.to_dict() for s in statements]
    conflict_dicts = [c.to_dict() for c in conflicts]
    consensus_dict = consensus.to_dict()

    deb_output = DebateOutput(
        entity_id=entity_id,
        debate_mode=True,
        agent_statements=stmt_dicts,
        conflicts=conflict_dicts,
        consensus=consensus_dict,
        final_debate_summary="",
    )

    deb_output.final_debate_summary = generate_debate_summary(deb_output)
    return deb_output


def prepare_llm_debate_payload(debate_output: DebateOutput) -> Dict[str, Any]:
    """
    Structures payload for optional button-triggered LLM debate summary.
    Excludes sensitive PII contact data.
    """
    consensus = debate_output.consensus or {}
    return {
        "entity_id": debate_output.entity_id,
        "consensus_status": consensus.get("consensus_status"),
        "priority_action": consensus.get("priority_action"),
        "reasoning_summary": consensus.get("reasoning_summary"),
        "conflicts": [c.get("description") for c in (debate_output.conflicts or [])],
        "agreed_risks": consensus.get("agreed_risks", []),
        "agreed_opportunities": consensus.get("agreed_opportunities", []),
    }
