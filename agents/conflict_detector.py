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


# Agent Domain Definitions
CUSTOMER_INTELLIGENCE_DOMAINS = {"digital_twin", "clv", "churn", "persona"}
OPERATIONAL_SUPERVISION_DOMAINS = {"campaign", "journey", "database_audit", "ui_ux"}


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
    """
    Detects status contradictions WITHIN THE SAME DOMAIN only.
    Cross-domain status differences (e.g. Journey OK vs Churn Critical) are NOT treated as conflicts.
    """
    conflicts: List[AgentConflict] = []
    by_id = _get_agent_dict(agent_outputs)

    # 1. Customer Intelligence Domain Status Contradictions
    ci_critical = [aid for aid, data in by_id.items() if aid in CUSTOMER_INTELLIGENCE_DOMAINS and data.get("status") == "Critical"]
    ci_ok = [aid for aid, data in by_id.items() if aid in CUSTOMER_INTELLIGENCE_DOMAINS and data.get("status") == "OK"]

    if ci_critical and ci_ok:
        conflicts.append(
            AgentConflict(
                conflict_id="CONF_STAT_CI_001",
                conflict_type="Customer Intelligence Status Disagreement",
                agents_involved=ci_critical + ci_ok,
                description=f"Customer Intelligence domain status contradiction: Critical reported by {ci_critical} while {ci_ok} reported OK.",
                severity="High",
                evidence=[f"{by_id[a].get('agent_name')}: {by_id[a].get('summary')}" for a in ci_critical + ci_ok],
                resolution_suggestion="Prioritize risk investigation for Critical customer intelligence alerts before accepting OK assessments.",
            )
        )

    # 2. Operational Supervision Domain Status Contradictions
    op_critical = [aid for aid, data in by_id.items() if aid in OPERATIONAL_SUPERVISION_DOMAINS and data.get("status") == "Critical"]
    op_ok = [aid for aid, data in by_id.items() if aid in OPERATIONAL_SUPERVISION_DOMAINS and data.get("status") == "OK"]

    if op_critical and op_ok:
        conflicts.append(
            AgentConflict(
                conflict_id="CONF_STAT_OP_001",
                conflict_type="Operational Supervision Status Disagreement",
                agents_involved=op_critical + op_ok,
                description=f"Operational Supervision domain status contradiction: Critical reported by {op_critical} while {op_ok} reported OK.",
                severity="High",
                evidence=[f"{by_id[a].get('agent_name')}: {by_id[a].get('summary')}" for a in op_critical + op_ok],
                resolution_suggestion="Resolve operational supervision failures before approving operational dispatches.",
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
    """Detects DB audit alerts overriding high agent confidence when data reliability is affected."""
    conflicts: List[AgentConflict] = []
    by_id = _get_agent_dict(agent_outputs)

    db_data = by_id.get("database_audit")
    if not db_data:
        return conflicts

    db_status = db_data.get("status")
    if db_status == "Critical" or (db_status == "Warning" and any("orphaned" in r.lower() or "missing" in r.lower() for r in db_data.get("risks", []))):
        high_conf_agents = [
            aid for aid, d in by_id.items()
            if aid != "database_audit" and d.get("confidence_score", 0.0) >= 0.85 and d.get("status") == "OK"
        ]
        if high_conf_agents:
            conflicts.append(
                AgentConflict(
                    conflict_id="CONF_DATA_001",
                    conflict_type="Database Audit Override",
                    agents_involved=["database_audit"] + high_conf_agents,
                    description=f"Database Audit Agent flagged data integrity issues ({db_status}), yet agents {high_conf_agents} report high confidence OK assessments.",
                    severity="Critical" if db_status == "Critical" else "High",
                    evidence=[f"DB Audit Summary: {db_data.get('summary')}"],
                    resolution_suggestion="Lower overall supervision confidence score and perform database audit before presentation.",
                )
            )
    return conflicts


def detect_persona_action_conflicts(agent_outputs: List[Any]) -> List[AgentConflict]:
    """Detects persona mapping issues (segment exists but stable persona is None)."""
    conflicts: List[AgentConflict] = []
    by_id = _get_agent_dict(agent_outputs)

    persona_data = by_id.get("persona")
    churn_data = by_id.get("churn")

    if persona_data:
        p_summary = persona_data.get("summary", "")
        p_risks = persona_data.get("risks", [])
        has_mapping_issue = any("persona mapping incomplete" in r.lower() or "returned none" in r.lower() for r in p_risks) or "none" in p_summary.lower()

        if has_mapping_issue:
            churn_critical = churn_data and churn_data.get("status") == "Critical"
            conflicts.append(
                AgentConflict(
                    conflict_id="CONF_PERS_MAP_001",
                    conflict_type="Persona Mapping Issue",
                    agents_involved=["persona"] + (["churn"] if churn_data else []),
                    description="Segment has no resolved stable persona.",
                    severity="High" if churn_critical else "Medium",
                    evidence=[
                        f"Persona Summary: {p_summary}",
                        f"Persona Risks: {', '.join(p_risks)}",
                    ],
                    resolution_suggestion="Check persona_library for segment mapping and rerun segment-first persona resolution.",
                )
            )
    return conflicts


def detect_campaign_readiness_conflicts(agent_outputs: List[Any]) -> List[AgentConflict]:
    """Detects Customer Risk + Campaign Gap (critical churn risk but 0 dispatches or no campaign action)."""
    conflicts: List[AgentConflict] = []
    by_id = _get_agent_dict(agent_outputs)

    campaign_data = by_id.get("campaign")
    churn_data = by_id.get("churn")

    if churn_data:
        churn_status = churn_data.get("status")
        if churn_status in {"Warning", "Critical"}:
            no_campaign = False
            if not campaign_data:
                no_campaign = True
            else:
                camp_sum = campaign_data.get("summary", "").lower()
                camp_risks = [r.lower() for r in campaign_data.get("risks", [])]
                if "zero campaign" in camp_sum or "no campaign" in camp_sum or any("zero campaign" in r or "no campaign" in r for r in camp_risks):
                    no_campaign = True
                elif campaign_data.get("status") in {"Warning", "Critical", "Insufficient Data"}:
                    no_campaign = True

            if no_campaign:
                conflicts.append(
                    AgentConflict(
                        conflict_id="CONF_CAMP_GAP_001",
                        conflict_type="Customer Risk + Campaign Gap",
                        agents_involved=["churn"] + (["campaign"] if campaign_data else []),
                        description="Critical churn risk detected but no campaign action exists.",
                        severity="High" if churn_status == "Critical" else "Medium",
                        evidence=[
                            f"Churn Status: {churn_status}",
                            f"Campaign Summary: {campaign_data.get('summary') if campaign_data else 'No Campaign Agent Output'}",
                        ],
                        resolution_suggestion="Prepare retention/service recovery campaign simulation.",
                    )
                )
    return conflicts


def detect_journey_conflicts(agent_outputs: List[Any], entity_id: str = "P_DEMO_001") -> List[AgentConflict]:
    """Detects Customer Risk + Journey Missing Warning for demo entities or broken journey steps."""
    conflicts: List[AgentConflict] = []
    by_id = _get_agent_dict(agent_outputs)

    journey_data = by_id.get("journey")

    if journey_data:
        j_status = journey_data.get("status")
        j_sum = journey_data.get("summary", "")
        j_risks = journey_data.get("risks", [])

        # Demo Journey Missing Warning for P_DEMO_001
        if entity_id == "P_DEMO_001" and (j_status == "Warning" or "0 steps" in j_sum or "not been started" in j_sum or any("demo readiness" in r.lower() for r in j_risks)):
            conflicts.append(
                AgentConflict(
                    conflict_id="CONF_JOURN_DEMO_001",
                    conflict_type="Customer Risk + Journey Missing Warning",
                    agents_involved=["journey"],
                    description="Demo journey is not ready for this entity.",
                    severity="Medium",
                    evidence=[f"Journey Summary: {j_sum}"],
                    resolution_suggestion="Run Journey Simulator before presentation.",
                )
            )

        # Broken Journey Integrity / Missing Foreign Keys
        elif j_status in {"Warning", "Critical"}:
            conflicts.append(
                AgentConflict(
                    conflict_id="CONF_JOURN_001",
                    conflict_type="Journey Integrity Conflict",
                    agents_involved=["journey"],
                    description="Journey Agent reports incomplete stage transitions, repeated steps, or missing trigger event references.",
                    severity="High" if j_status == "Critical" else "Medium",
                    evidence=[f"Journey Summary: {j_sum}"],
                    resolution_suggestion="Audit journey scenario steps and verify trigger event IDs in event_history.",
                )
            )
    return conflicts


def detect_all_conflicts(agent_outputs: List[Any], entity_id: str = "P_DEMO_001") -> List[AgentConflict]:
    """Runs all conflict detection routines and aggregates results."""
    all_conflicts: List[AgentConflict] = []
    all_conflicts.extend(detect_status_conflicts(agent_outputs))
    all_conflicts.extend(detect_priority_conflicts(agent_outputs))
    all_conflicts.extend(detect_data_quality_conflicts(agent_outputs))
    all_conflicts.extend(detect_persona_action_conflicts(agent_outputs))
    all_conflicts.extend(detect_campaign_readiness_conflicts(agent_outputs))
    all_conflicts.extend(detect_journey_conflicts(agent_outputs, entity_id=entity_id))
    return all_conflicts
