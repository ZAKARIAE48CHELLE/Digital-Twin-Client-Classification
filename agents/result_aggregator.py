"""
OSMOS Multi-Agent Supervision Layer — Result Aggregator (Phase 8.1)
====================================================================
Consolidates individual specialized agent outputs into a unified
supervision report with global status rules, merged risks/opportunities,
confidence scoring, and Next Best Action recommendations.
"""

from typing import List, Dict, Any
from agents.agent_schemas import AgentOutput, OrchestratorOutput


def aggregate_agent_status(agent_outputs: List[AgentOutput]) -> str:
    """
    Computes global supervision status from agent outputs.
    Rules:
    - Critical if ANY agent is Critical
    - Warning if ANY agent is Warning and none is Critical
    - OK if all agents are OK
    - Insufficient Data if majority are Insufficient Data / Error
    """
    if not agent_outputs:
        return "Insufficient Data"

    statuses = [out.status for out in agent_outputs]

    if "Critical" in statuses:
        return "Critical"
    if "Warning" in statuses:
        return "Warning"
    if any(s == "OK" for s in statuses):
        return "OK"
    if all(s in {"Insufficient Data", "Error"} for s in statuses):
        return "Insufficient Data"

    return "Warning"


def merge_risks(agent_outputs: List[AgentOutput]) -> List[str]:
    """Extracts and deduplicates all risks from agent outputs."""
    merged = []
    seen = set()
    for out in agent_outputs:
        for r in out.risks:
            clean = r.strip()
            if clean and clean not in seen:
                seen.add(clean)
                merged.append(clean)
    return merged


def merge_opportunities(agent_outputs: List[AgentOutput]) -> List[str]:
    """Extracts and deduplicates all opportunities from agent outputs."""
    merged = []
    seen = set()
    for out in agent_outputs:
        for o in out.opportunities:
            clean = o.strip()
            if clean and clean not in seen:
                seen.add(clean)
                merged.append(clean)
    return merged


def merge_recommendations(agent_outputs: List[AgentOutput]) -> List[str]:
    """Extracts and deduplicates all recommendations from agent outputs."""
    merged = []
    seen = set()
    for out in agent_outputs:
        for rec in out.recommendations:
            clean = rec.strip()
            if clean and clean not in seen:
                seen.add(clean)
                merged.append(clean)
    return merged


def compute_global_confidence(agent_outputs: List[AgentOutput]) -> float:
    """Computes average confidence score across executed agents."""
    if not agent_outputs:
        return 0.0
    scores = [out.confidence_score for out in agent_outputs]
    return round(sum(scores) / len(scores), 2)


def choose_next_best_action(agent_outputs: List[AgentOutput], entity_type: str = "Client") -> str:
    """
    Deterministic rule-based engine selecting the Next Best Action (NBA).
    Priority order:
    1. Critical Churn + High CLV
    2. Critical / High Churn
    3. High CLV VIP Loyalty
    4. Prospect Conversion
    5. Low Value Nurture
    6. Profile Data Complete
    """
    by_id: Dict[str, AgentOutput] = {out.agent_id: out for out in agent_outputs}

    clv_out = by_id.get("clv")
    churn_out = by_id.get("churn")
    twin_out = by_id.get("digital_twin")
    persona_out = by_id.get("persona")

    global_status = aggregate_agent_status(agent_outputs)

    # Rule 1: High Value at Risk (Critical CLV + Critical Churn)
    if (clv_out and clv_out.status == "Critical") or (churn_out and churn_out.status == "Critical"):
        if clv_out and any("VIP" in r or "High CLV" in r or "High Value" in r for r in clv_out.risks + clv_out.observations):
            return "URGENT VIP RETENTION: Initiate high-priority executive outreach and service recovery protocol."
        return "RETENTION INTERVENTION: Execute churn prevention campaign with targeted customer incentive."

    # Rule 2: Warning Churn
    if churn_out and churn_out.status == "Warning":
        return "SERVICE RECOVERY: Schedule satisfaction survey and re-engagement campaign."

    # Rule 3: High Value VIP (OK status)
    if clv_out and any("VIP" in o or "High Value" in o for o in clv_out.observations + clv_out.opportunities):
        return "VIP LOYALTY ENROLLMENT: Apply premium account perks and targeted cross-sell offering."

    # Rule 4: Prospect Conversion
    if entity_type == "Prospect":
        return "PROSPECT CONVERSION: Launch personalized introductory onboarding campaign."

    # Rule 5: Profile Data Deficit
    if global_status == "Insufficient Data" or (twin_out and twin_out.status in {"Insufficient Data", "Warning"}):
        return "DATA ENRICHMENT: Review profile completeness and verify entity event ingestion."

    # Rule 6: Default Operational Monitoring
    return "AUTOMATED NURTURING: Continue standard monitoring and routine digital campaign dispatches."


def synthesize_orchestrator_summary(
    entity_id: str,
    global_status: str,
    next_best_action: str,
    agent_outputs: List[AgentOutput],
) -> str:
    """Generates a concise executive summary paragraph synthesizing agent outputs."""
    if not agent_outputs:
        return f"Supervision analysis for Entity [{entity_id}] failed to yield active agent results."

    status_counts: Dict[str, int] = {}
    for out in agent_outputs:
        status_counts[out.status] = status_counts.get(out.status, 0) + 1

    count_str = ", ".join(f"{cnt} {st}" for st, cnt in status_counts.items())

    return (
        f"Multi-Agent Supervision for Entity [{entity_id}] evaluated a global status of '{global_status}' "
        f"across {len(agent_outputs)} agents ({count_str}). "
        f"Recommended Next Best Action: '{next_best_action}'."
    )
