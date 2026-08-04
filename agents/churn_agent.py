"""
OSMOS Multi-Agent Supervision Layer — Churn Risk Agent (Phase 8.1)
===================================================================
Specialized agent for evaluating churn risk probabilities, dissatisfaction signals,
inactivity events, and service recovery recommendations.
"""

from typing import Any, Dict, List
import pandas as pd

from agents.base_agent import BaseAgent
from agents.agent_schemas import AgentContext, AgentOutput, EvidenceItem


def safe_float(val: Any, default: float = 0.0) -> float:
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val: Any, default: int = 0) -> int:
    if val is None or pd.isna(val):
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


class ChurnRiskAgent(BaseAgent):
    """
    Evaluates churn risk scores, complaint history, sentiment friction,
    and inactivity thresholds to recommend proactive retention actions.
    """

    def __init__(self):
        super().__init__(
            agent_id="churn",
            agent_name="Churn Risk Agent",
            agent_role="Churn probability detection, friction signals & retention intervention analysis",
            agent_version="1.0.0",
        )

    def _analyze_implementation(self, context: AgentContext) -> AgentOutput:
        dt = context.latest_digital_twin or {}
        cls_dict = context.latest_classification or {}
        events = context.recent_events or []

        churn_score = safe_float(
            cls_dict.get("churn_risk_score")
            or dt.get("churn_risk_score")
            or dt.get("churn_risk"),
            0.0,
        )
        recency_days = safe_float(dt.get("recency_days") or dt.get("recency"), 0.0)
        complaints = safe_int(dt.get("complaint_count_90d") or dt.get("complaints"), 0)
        review_score = safe_float(dt.get("review_score_avg") or dt.get("review_score"), 5.0)

        observations: List[str] = []
        risks: List[str] = []
        opportunities: List[str] = []
        recommendations: List[str] = []
        evidence: List[Dict[str, Any]] = []

        # Churn Risk Classification
        if churn_score >= 0.70:
            risk_tier = "Critical Churn Risk"
            status = "Critical"
        elif 0.40 <= churn_score < 0.70:
            risk_tier = "Medium Churn Risk"
            status = "Warning"
        else:
            risk_tier = "Low Churn Risk"
            status = "OK"

        # Evidence Traceability
        evidence.append(
            EvidenceItem(
                metric_name="churn_risk_score",
                value=round(churn_score, 3),
                threshold="Critical: >=0.70 | Medium: 0.40-0.69 | Low: <0.40",
                interpretation=f"Model churn probability evaluated at {churn_score * 100:.1f}% ({risk_tier}).",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="recency_days",
                value=int(recency_days),
                threshold="Active: <=30d | Moderate: 31-90d | Inactive: >90d",
                interpretation=f"Customer has been inactive for {int(recency_days)} days.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="complaint_count_90d",
                value=complaints,
                threshold="Low: 0 | Warning: 1 | High: >=2",
                interpretation=f"Registered {complaints} complaints in past 90 days.",
            ).to_dict()
        )

        observations.append(f"Churn risk score is {churn_score * 100:.1f}% ({risk_tier}).")
        observations.append(f"Inactivity recency: {int(recency_days)} days | Complaints: {complaints}.")

        # Risk Analysis
        if churn_score >= 0.70:
            risks.append(f"Critical churn risk ({churn_score * 100:.1f}%) requires immediate intervention.")
            recommendations.append("Trigger emergency retention campaign with targeted incentive or discount.")
            recommendations.append("Assign priority human agent follow-up call.")
        elif 0.40 <= churn_score < 0.70:
            risks.append(f"Moderate churn risk ({churn_score * 100:.1f}%) indicates growing disengagement.")
            recommendations.append("Schedule re-engagement outreach campaign and satisfaction check-in.")
        else:
            opportunities.append("Customer exhibits low churn probability and high engagement stability.")
            recommendations.append("Maintain standard service communications and loyalty incentives.")

        # Additional Friction Factors
        if recency_days > 90:
            if status == "OK":
                status = "Warning"
            risks.append(f"Severe inactivity threshold reached ({int(recency_days)} days without activity).")
            recommendations.append("Send 'We miss you' reactivation campaign.")

        if complaints >= 2 or review_score < 3.0:
            if status != "Critical":
                status = "Warning"
            risks.append(f"High dissatisfaction signals detected (Complaints: {complaints}, Review Score: {review_score:.1f}/5).")
            recommendations.append("Execute formal service recovery process and issue satisfaction survey.")

        summary = (
            f"Churn Risk Agent analysis for Entity [{context.entity_id}] evaluated "
            f"risk status as {status} (Score: {churn_score * 100:.1f}%)."
        )

        return self.format_output(
            status=status,
            summary=summary,
            observations=observations,
            risks=risks,
            opportunities=opportunities,
            recommendations=recommendations,
            confidence_score=0.92,
            evidence=evidence,
        )
