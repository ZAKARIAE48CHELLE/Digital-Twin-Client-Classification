"""
OSMOS Multi-Agent Supervision Layer — Conflict Detector (Phase 8.4)
===================================================================
Rule-based conflict detection engine evaluating status contradictions,
CLV opportunity vs Churn risk priority clashes, database audit overrides,
persona stability vs churn risk, campaign dispatch readiness, and journey integrity.

Read-Only Guarantee: Pure analytical evaluation. Zero database or DataFrame mutations.
"""

import logging
from typing import Any, Dict, List, Optional
from agents.debate_schemas import AgentConflict

logger = logging.getLogger("OSMOS_CONFLICT_DETECTOR")


def _get_agent_dict(agent_outputs: List[Any]) -> Dict[str, Dict[str, Any]]:
    """Helper to convert agent outputs into dict indexed by agent_id."""
    by_id: Dict[str, Dict[str, Any]] = {}
    for out in agent_outputs or []:
        if isinstance(out, dict):
            aid = out.get("agent_id")
            if aid:
                by_id[aid] = out
        else:
            aid = getattr(out, "agent_id", None)
            if aid:
                by_id[aid] = out.to_dict() if hasattr(out, "to_dict") else dict(out)
    return by_id


def detect_status_conflicts(agent_outputs: List[Any]) -> List[AgentConflict]:
    """Detects severe status contradictions between agents (e.g. Critical vs OK)."""
    conflicts: List[AgentConflict] = []
    by_id = _get_agent_dict(agent_outputs)

    critical_agents = [aid for aid, data in by_id.items() if data.get("status") == "Critical"]
    ok_agents = [aid for aid, data in by_id.items() if data.get("status") == "OK"]

    if critical_agents and ok_agents:
        conflicts.append(
            AgentConflict(
                conflict_id="CONF_STAT_001",
                conflict_type="Status Disagreement",
                agents_involved=critical_agents + ok_agents,
                description=f"Critical status reported by {critical_agents} while {ok_agents} reported OK.",
                severity="High",
                evidence=[f"Critical: {by_id[a].get('agent_name')} ({by_id[a].get('summary')[:40]}...)" for a in critical_agents],
                resolution_suggestion="Prioritize risk investigation for Critical alerts before accepting OK assessments.",
            )
        )
    return conflicts


def detect_priority_conflicts(agent_outputs: List[Any]) -> List[AgentConflict]:
    """Detects CLV opportunity vs Churn risk priority conflicts."""
    conflicts: List[AgentConflict] = []
    by_id = _get_agent_dict(agent_outputs)

    clv_data = by_id.get("clv")
    churn_data = by_id.get("churn")

    if clv_data and churn_data:
        clv_status = clv_data.get("status")
        churn_status = churn_data.get("status")

        has_opp = bool(clv_data.get("opportunities"))
        is_churn_risk = churn_status in {"Warning", "Critical"}

        if has_opp and is_churn_risk:
            conflicts.append(
                AgentConflict(
                    conflict_id="CONF_PRIO_001",
                    conflict_type="Risk vs Opportunity Priority",
                    agents_involved=["clv", "churn"],
                    description="CLV Agent identifies high-value opportunity, but Churn Agent detects elevated churn risk.",
                    severity="Critical" if churn_status == "Critical" else "High",
                    evidence=[
                        f"CLV Opportunity: {clv_data.get('opportunities')[0]}",
                        f"Churn Risk: {churn_data.get('summary')}",
                    ],
                    resolution_suggestion="Execute retention and service recovery FIRST before attempting upsell or expansion.",
                )
            )
    return conflicts


def detect_data_quality_conflicts(agent_outputs: List[Any]) -> List[AgentConflict]:
    """Detects DB audit alerts overriding high agent confidence."""
    conflicts: List[AgentConflict] = []
    by_id = _get_agent_dict(agent_outputs)

    db_data = by_id.get("database_audit")
    if not db_data:
        return conflicts

    db_status = db_data.get("status")
    if db_status in {"Warning", "Critical"}:
        high_conf_agents = [
            aid for aid, d in by_id.items()
            if aid != "database_audit" and d.get("confidence_score", 0.0) >= 0.85 and d.get("status") == "OK"
        ]
        if high_conf_agents:
            conflicts.append(
                AgentConflict(
                    conflict_id="CONF_DATA_001",
                    conflict_type="Data Quality Override",
                    agents_involved=["database_audit"] + high_conf_agents,
                    description=f"Database Audit Agent flagged data integrity issues ({db_status}), yet agents {high_conf_agents} report high confidence OK assessments.",
                    severity="High",
                    evidence=[f"DB Audit Summary: {db_data.get('summary')}"],
                    resolution_suggestion="Lower overall supervision confidence score and perform database audit before presentation.",
                )
            )
    return conflicts


def detect_persona_action_conflicts(agent_outputs: List[Any]) -> List[AgentConflict]:
    """Detects persona stability vs churn risk resolution."""
    conflicts: List[AgentConflict] = []
    by_id = _get_agent_dict(agent_outputs)

    persona_data = by_id.get("persona")
    churn_data = by_id.get("churn")

    if persona_data and churn_data:
        if persona_data.get("status") == "OK" and churn_data.get("status") in {"Warning", "Critical"}:
            conflicts.append(
                AgentConflict(
                    conflict_id="CONF_PERS_001",
                    conflict_type="Persona vs Churn Conflict",
                    agents_involved=["persona", "churn"],
                    description="Persona Agent confirms stable persona alignment, but Churn Agent reports elevated churn risk.",
                    severity="Medium",
                    evidence=[
                        f"Persona: {persona_data.get('summary')}",
                        f"Churn: {churn_data.get('summary')}",
                    ],
                    resolution_suggestion="Maintain persona profile targeting, but tailor retention message specifically to churn trigger.",
                )
            )
    return conflicts


def detect_campaign_readiness_conflicts(agent_outputs: List[Any]) -> List[AgentConflict]:
    """Detects un-contacted churn risk vs missing campaign history."""
    conflicts: List[AgentConflict] = []
    by_id = _get_agent_dict(agent_outputs)

    campaign_data = by_id.get("campaign")
    churn_data = by_id.get("churn")

    if campaign_data and churn_data:
        if churn_data.get("status") in {"Warning", "Critical"} and campaign_data.get("status") in {"Warning", "Critical", "Insufficient Data"}:
            conflicts.append(
                AgentConflict(
                    conflict_id="CONF_CAMP_001",
                    conflict_type="Campaign Readiness Conflict",
                    agents_involved=["campaign", "churn"],
                    description="High churn risk detected for entity, but Campaign Agent reports no recent dispatches or negative campaign responses.",
                    severity="High",
                    evidence=[
                        f"Churn Status: {churn_data.get('status')}",
                        f"Campaign Summary: {campaign_data.get('summary')}",
                    ],
                    resolution_suggestion="Immediately draft a targeted service recovery campaign in the Human Approval Queue.",
                )
            )
    return conflicts


def detect_journey_conflicts(agent_outputs: List[Any]) -> List[AgentConflict]:
    """Detects broken journey stage transitions or missing event references."""
    conflicts: List[AgentConflict] = []
    by_id = _get_agent_dict(agent_outputs)

    journey_data = by_id.get("journey")
    db_data = by_id.get("database_audit")

    if journey_data and db_data:
        if journey_data.get("status") in {"Warning", "Critical"}:
            conflicts.append(
                AgentConflict(
                    conflict_id="CONF_JOURN_001",
                    conflict_type="Journey Integrity Conflict",
                    agents_involved=["journey", "database_audit"],
                    description="Journey Agent reports incomplete stage transitions or missing trigger event references.",
                    severity="Medium",
                    evidence=[f"Journey Summary: {journey_data.get('summary')}"],
                    resolution_suggestion="Audit journey scenario steps and verify trigger event IDs in event_history.",
                )
            )
    return conflicts


def detect_all_conflicts(agent_outputs: List[Any]) -> List[AgentConflict]:
    """Runs all conflict detection routines and aggregates results."""
    all_conflicts: List[AgentConflict] = []
    all_conflicts.extend(detect_status_conflicts(agent_outputs))
    all_conflicts.extend(detect_priority_conflicts(agent_outputs))
    all_conflicts.extend(detect_data_quality_conflicts(agent_outputs))
    all_conflicts.extend(detect_persona_action_conflicts(agent_outputs))
    all_conflicts.extend(detect_campaign_readiness_conflicts(agent_outputs))
    all_conflicts.extend(detect_journey_conflicts(agent_outputs))
    return all_conflicts
