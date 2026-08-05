"""
OSMOS Multi-Agent Supervision Layer — Consensus Builder (Phase 8.4)
===================================================================
Synthesis engine evaluating agent agreement, determining consensus status,
ranking recommendations, selecting priority actions, and computing debate confidence.

Read-Only Guarantee: Pure analytical evaluation. Zero database or DataFrame mutations.
"""

import logging
from typing import Any, Dict, List, Optional
from agents.debate_schemas import AgentConflict, AgentConsensus

logger = logging.getLogger("OSMOS_CONSENSUS_BUILDER")


def _get_agent_dict(agent_outputs: List[Any]) -> Dict[str, Dict[str, Any]]:
    """Helper to index agent outputs by agent_id."""
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


def compute_consensus_status(conflicts: List[AgentConflict], agent_outputs: List[Any]) -> str:
    """
    Determines overall consensus status across agents:
    - 'Critical Conflict'
    - 'Conflict Detected'
    - 'Partial Consensus'
    - 'Insufficient Data'
    - 'Strong Consensus'
    """
    by_id = _get_agent_dict(agent_outputs)
    statuses = [d.get("status") for d in by_id.values()]

    # 1. Critical Conflict check
    if any(c.severity == "Critical" for c in conflicts) or by_id.get("database_audit", {}).get("status") == "Critical":
        return "Critical Conflict"

    # 2. High severity conflicts
    if any(c.severity == "High" for c in conflicts):
        return "Conflict Detected"

    # 3. Insufficient data check
    insufficient_count = sum(1 for s in statuses if s == "Insufficient Data")
    if insufficient_count >= (len(agent_outputs) / 2) and len(agent_outputs) > 0:
        return "Insufficient Data"

    # 4. Partial consensus check (minor conflicts or warnings present)
    if conflicts or any(s in {"Warning", "Critical"} for s in statuses):
        return "Partial Consensus"

    # 5. Strong Consensus
    return "Strong Consensus"


def rank_recommendations(agent_outputs: List[Any], conflicts: List[AgentConflict]) -> List[str]:
    """Merges and ranks recommendations putting retention/recovery before expansion if risks exist."""
    by_id = _get_agent_dict(agent_outputs)

    retention_recs: List[str] = []
    operational_recs: List[str] = []
    expansion_recs: List[str] = []

    for d in by_id.values():
        recs = d.get("recommendations", [])
        for r in recs:
            clean = r.strip()
            if not clean:
                continue
            lower = clean.lower()
            if any(k in lower for k in ["churn", "retention", "recovery", "complaint", "urgent", "risk"]):
                if clean not in retention_recs:
                    retention_recs.append(clean)
            elif any(k in lower for k in ["audit", "fix", "verify", "db", "journey", "data"]):
                if clean not in operational_recs:
                    operational_recs.append(clean)
            else:
                if clean not in expansion_recs:
                    expansion_recs.append(clean)

    # Order: Retention -> Operational Audit -> Expansion
    return retention_recs + operational_recs + expansion_recs


def choose_priority_action(agent_outputs: List[Any], conflicts: List[AgentConflict]) -> str:
    """
    Selects the single most urgent Next Best Action based on priority rules:
    - High CLV + High churn -> retention/service recovery first
    - High CLV + Low churn -> VIP loyalty / upsell
    - High churn + complaint -> service recovery campaign
    - Missing DB evidence -> audit data first
    - Journey broken -> fix journey consistency
    - Campaign missing + high churn -> prepare retention campaign draft
    - Low value + low risk -> automated nurturing
    """
    by_id = _get_agent_dict(agent_outputs)

    churn_d = by_id.get("churn", {})
    clv_d = by_id.get("clv", {})
    db_d = by_id.get("database_audit", {})
    journey_d = by_id.get("journey", {})
    camp_d = by_id.get("campaign", {})

    # Priority Rule 1: Database Audit Critical
    if db_d.get("status") == "Critical":
        return "DATABASE AUDIT: Audit schema integrity and resolve database errors before operational actions."

    # Priority Rule 2: High Churn + High CLV
    if churn_d.get("status") in {"Warning", "Critical"} and clv_d.get("status") in {"OK", "Warning"}:
        return "SERVICE RECOVERY: Prioritize urgent retention outreach before upsell or expansion."

    # Priority Rule 3: High Churn + Missing Campaign
    if churn_d.get("status") in {"Warning", "Critical"} and camp_d.get("status") in {"Warning", "Critical", "Insufficient Data"}:
        return "CAMPAIGN DRAFT: Prepare a targeted retention campaign draft in Human Approval Queue."

    # Priority Rule 4: Journey Stage Error
    if journey_d.get("status") in {"Warning", "Critical"}:
        return "JOURNEY AUDIT: Fix journey step trigger references and verify stage transition history."

    # Priority Rule 5: High CLV + Low Churn
    if clv_d.get("status") == "OK" and churn_d.get("status") == "OK":
        opps = clv_d.get("opportunities", [])
        if opps:
            return f"VIP EXPANSION: Execute loyalty reward or cross-sell ({opps[0]})."
        return "VIP LOYALTY: Maintain active VIP engagement and priority customer support."

    # Default Fallback
    ranked = rank_recommendations(agent_outputs, conflicts)
    if ranked:
        return f"SUPERVISED ACTION: {ranked[0]}"

    return "STANDARD NURTURING: Continue automated baseline engagement and monitoring."


def compute_debate_confidence(agent_outputs: List[Any], conflicts: List[AgentConflict]) -> float:
    """Calculates overall confidence score weighted by conflict severity."""
    if not agent_outputs:
        return 0.50

    base_scores = [d.get("confidence_score", 0.80) for d in _get_agent_dict(agent_outputs).values()]
    avg_base = sum(base_scores) / len(base_scores) if base_scores else 0.80

    penalty = 0.0
    for c in conflicts:
        if c.severity == "Critical":
            penalty += 0.20
        elif c.severity == "High":
            penalty += 0.10
        elif c.severity == "Medium":
            penalty += 0.05

    final_score = max(0.20, min(0.98, avg_base - penalty))
    return round(final_score, 2)


def generate_consensus_reasoning(
    agent_outputs: List[Any],
    conflicts: List[AgentConflict],
    consensus_status: str,
    priority_action: str,
) -> str:
    """Generates a human-readable explanation of how consensus was formed."""
    total = len(agent_outputs)
    conflict_cnt = len(conflicts)

    if consensus_status == "Strong Consensus":
        return f"All {total} active agents arrived at aligned findings with zero conflicts detected. Priority action: '{priority_action}'."
    elif consensus_status == "Critical Conflict":
        return f"Critical conflict detected among agents. Priority action reflects risk mitigation first: '{priority_action}'."
    elif consensus_status == "Conflict Detected":
        return f"Disagreements detected between risk and opportunity agents ({conflict_cnt} conflicts). Priority action resolves risk before expansion."
    elif consensus_status == "Partial Consensus":
        return f"Partial consensus formed across {total} agents with {conflict_cnt} minor priority alignments noted."
    else:
        return f"Consensus status evaluated as '{consensus_status}'. Priority action: '{priority_action}'."


def build_consensus(agent_outputs: List[Any], conflicts: List[AgentConflict]) -> AgentConsensus:
    """Main entrypoint for synthesizing AgentConsensus."""
    by_id = _get_agent_dict(agent_outputs)

    agreed_risks: List[str] = []
    agreed_opps: List[str] = []

    for d in by_id.values():
        for r in d.get("risks", []):
            if r not in agreed_risks:
                agreed_risks.append(r)
        for o in d.get("opportunities", []):
            if o not in agreed_opps:
                agreed_opps.append(o)

    status = compute_consensus_status(conflicts, agent_outputs)
    ranked_recs = rank_recommendations(agent_outputs, conflicts)
    priority = choose_priority_action(agent_outputs, conflicts)
    confidence = compute_debate_confidence(agent_outputs, conflicts)

    unresolved = [c.to_dict() if hasattr(c, "to_dict") else dict(c) for c in conflicts]
    reasoning = generate_consensus_reasoning(agent_outputs, conflicts, status, priority)

    return AgentConsensus(
        consensus_status=status,
        agreed_risks=agreed_risks,
        agreed_opportunities=agreed_opps,
        agreed_recommendations=ranked_recs,
        unresolved_conflicts=unresolved,
        priority_action=priority,
        confidence_score=confidence,
        reasoning_summary=reasoning,
    )
