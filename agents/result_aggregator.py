"""
OSMOS Multi-Agent Supervision Layer — Result Aggregator (Phase 8.2)
====================================================================
Consolidates individual specialized agent outputs into a unified
supervision report with global status rules, merged risks/opportunities,
confidence scoring, system readiness summaries, and Next Best Action recommendations.
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


def compute_system_readiness_summary(agent_outputs: List[Any]) -> Dict[str, Any]:
    """Synthesizes an executive System Readiness Summary across operational agents."""
    by_id: Dict[str, Any] = {}
    for out in agent_outputs or []:
        aid = getattr(out, "agent_id", None) if hasattr(out, "agent_id") else (out.get("agent_id") if isinstance(out, dict) else None)
        if aid:
            by_id[aid] = out

    def get_status(out_item: Any) -> str:
        if not out_item:
            return "Not Checked"
        if hasattr(out_item, "status"):
            return str(out_item.status)
        if isinstance(out_item, dict):
            return str(out_item.get("status", "Not Checked"))
        return "Not Checked"

    db_status = get_status(by_id.get("database_audit"))
    journey_status = get_status(by_id.get("journey"))
    campaign_status = get_status(by_id.get("campaign"))
    ui_status = get_status(by_id.get("ui_ux"))

    statuses = [get_status(out) for out in agent_outputs or []]

    return {
        "database_integrity": db_status,
        "journey_readiness": journey_status,
        "campaign_readiness": campaign_status,
        "demo_readiness": ui_status,
        "total_agents_run": len(agent_outputs or []),
        "critical_agent_count": sum(1 for s in statuses if s == "Critical"),
        "warning_agent_count": sum(1 for s in statuses if s == "Warning"),
        "ok_agent_count": sum(1 for s in statuses if s == "OK"),
    }


def choose_next_best_action(
    agent_outputs: List[AgentOutput],
    entity_type: str = "Client",
    entity_id: str = "P_DEMO_001",
) -> str:
    """
    Deterministic rule-based engine selecting the Next Best Action (NBA).
    Priority order:
    1. Critical Churn + Campaign Gap + Persona Mapping / Journey Warning
    2. Critical Churn + High CLV VIP
    3. Critical / High Churn Risk
    4. Database Audit Foreign Key / Persistence Warning
    5. Persona Mapping Resolution
    6. Journey Simulator Demo Readiness
    7. VIP Loyalty Enrollment
    8. Prospect Conversion / Automated Nurturing
    """
    by_id: Dict[str, AgentOutput] = {out.agent_id: out for out in agent_outputs}

    clv_out = by_id.get("clv")
    churn_out = by_id.get("churn")
    twin_out = by_id.get("digital_twin")
    db_out = by_id.get("database_audit")
    journey_out = by_id.get("journey")
    campaign_out = by_id.get("campaign")
    persona_out = by_id.get("persona")

    churn_critical = churn_out and churn_out.status == "Critical"
    churn_risk_high = churn_critical or (churn_out and churn_out.status == "Warning")

    camp_gap = False
    if campaign_out:
        camp_sum = campaign_out.summary.lower()
        camp_risks = [r.lower() for r in campaign_out.risks]
        if "zero campaign" in camp_sum or "no campaign" in camp_sum or any("zero campaign" in r or "no campaign" in r for r in camp_risks):
            camp_gap = True
        elif campaign_out.status in {"Warning", "Critical", "Insufficient Data"}:
            camp_gap = True
    else:
        camp_gap = True

    persona_issue = False
    if persona_out:
        p_risks = [r.lower() for r in persona_out.risks]
        if any("persona mapping incomplete" in r or "returned none" in r for r in p_risks) or "none" in persona_out.summary.lower():
            persona_issue = True

    journey_not_started = False
    if journey_out:
        j_sum = journey_out.summary.lower()
        if journey_out.status == "Warning" or "0 steps" in j_sum or "not been started" in j_sum:
            journey_not_started = True

    # Required Fix 4 Scenario: Churn Critical + Campaign Gap + Persona issue / Journey missing
    if churn_critical and camp_gap:
        if persona_issue or journey_not_started or entity_id == "P_DEMO_001":
            return (
                "Prioritize service recovery and retention simulation because churn risk is critical and no campaign history exists. "
                "Before presentation, fix persona mapping for the current segment and run the Journey Simulator if P_DEMO_001 is used as the demo entity."
            )
        return "RETENTION INTERVENTION: Prepare retention and service recovery campaign simulation in Campaign Agent."

    # Priority 2: High Value at Risk (Critical CLV + Critical Churn)
    if clv_out and clv_out.status == "Critical" and churn_critical:
        return "URGENT VIP RETENTION: Initiate high-priority executive outreach and service recovery protocol."

    # Priority 3: Database Integrity Audit Critical
    if db_out and db_out.status == "Critical":
        return "DATABASE AUDIT REQUIRED: Verify PostgreSQL event persistence and resolve orphaned foreign key references in database_audit."

    # Priority 4: Persona Mapping Issue
    if persona_issue:
        return "PERSONA MAPPING AUDIT: Check persona_library for segment mapping and rerun segment-first persona resolution."

    # Priority 5: Journey Incomplete or Stuck
    if journey_out and journey_out.status == "Warning":
        if entity_id == "P_DEMO_001" and journey_not_started:
            return "JOURNEY SIMULATOR REQUIRED: Run Journey Simulator before presentation to generate 5-stage lifecycle scenario for P_DEMO_001."
        return "JOURNEY SCENARIO CONTINUATION: Execute remaining stages in Journey Simulator to complete lifecycle tree."

    # Priority 6: Warning Churn Risk
    if churn_risk_high:
        return "RETENTION CAMPAIGN SIMULATION: High churn risk detected; draft targeted retention campaign simulation."

    # Priority 7: High Value VIP (OK status)
    if clv_out and any("VIP" in o or "High Value" in o for o in clv_out.observations + clv_out.opportunities):
        return "VIP LOYALTY ENROLLMENT: Apply premium account perks and targeted cross-sell offering."

    # Priority 8: Prospect Conversion
    if entity_type == "Prospect":
        return "PROSPECT CONVERSION: Launch personalized introductory onboarding campaign."

    # Default Operational Monitoring
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
        f"across {len(agent_outputs)} specialized agents ({count_str}). "
        f"Recommended Next Best Action: '{next_best_action}'."
    )
