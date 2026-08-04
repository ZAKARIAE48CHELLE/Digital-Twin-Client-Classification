"""
OSMOS Multi-Agent Supervision Layer — CLV Agent (Phase 8.1)
===========================================================
Specialized agent for evaluating Customer Lifetime Value (CLV), value tiering,
VIP protection strategies, and value collapse risks.
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


class CLVAgent(BaseAgent):
    """
    Evaluates predicted CLV monetary amount, CLV tier classification,
    high-value client protection, and low-value nurture automation.
    """

    def __init__(self):
        super().__init__(
            agent_id="clv",
            agent_name="CLV Agent",
            agent_role="Customer Lifetime Value evolution & VIP value protection analysis",
            agent_version="1.0.0",
        )

    def _analyze_implementation(self, context: AgentContext) -> AgentOutput:
        clv_info = context.latest_clv or {}
        dt = context.latest_digital_twin or {}

        clv_val = safe_float(
            clv_info.get("predicted_clv_amount_mad")
            or dt.get("predicted_clv_amount_mad")
            or dt.get("predicted_clv"),
            0.0,
        )
        clv_score = safe_float(clv_info.get("clv_score") or dt.get("clv_score"), 0.0)
        clv_segment = str(
            clv_info.get("clv_segment") or dt.get("clv_segment") or "Unknown"
        )

        observations: List[str] = []
        risks: List[str] = []
        opportunities: List[str] = []
        recommendations: List[str] = []
        evidence: List[Dict[str, Any]] = []

        # Value Tier Classification
        if clv_val >= 8000.0:
            value_tier = "High Value (VIP)"
            status = "OK"
        elif 1500.0 <= clv_val < 8000.0:
            value_tier = "Medium Value"
            status = "OK"
        elif 0.0 < clv_val < 1500.0:
            value_tier = "Low Value"
            status = "OK"
        else:
            value_tier = "Value Collapse / Minimal"
            status = "Warning"

        # Evidence Traceability
        evidence.append(
            EvidenceItem(
                metric_name="predicted_clv_mad",
                value=f"{clv_val:,.2f} MAD",
                threshold="High: >=8,000 | Med: 1,500-7,999 | Low: <1,500 | Collapse: <=0",
                interpretation=f"Entity classified under '{value_tier}' tier based on projected revenue.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="clv_score",
                value=round(clv_score, 3),
                threshold="0.0 - 1.0",
                interpretation=f"Normalized CLV probability score is {clv_score:.2f}.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="clv_segment",
                value=clv_segment,
                threshold="Mapped Tier",
                interpretation=f"Assigned to CLV segment '{clv_segment}'.",
            ).to_dict()
        )

        observations.append(f"Predicted CLV is {clv_val:,.2f} MAD ({value_tier}).")
        observations.append(f"CLV segment: {clv_segment} | Normalized CLV score: {clv_score:.2f}.")

        # Risk & Opportunity Logic
        if clv_val >= 8000.0:
            opportunities.append("High-value VIP entity suitable for dedicated account management and exclusive perks.")
            recommendations.append("Apply VIP retention protocol and priority customer support routing.")
        elif 1500.0 <= clv_val < 8000.0:
            opportunities.append("Core customer segment with potential for expansion into high-value tier.")
            recommendations.append("Enroll in automated cross-sell/upsell nurturing workflows.")
        elif 0.0 < clv_val < 1500.0:
            observations.append("Low monetary footprint requires low-cost automated engagement.")
            recommendations.append("Use automated digital campaigns to maximize margin efficiency.")
        else:
            risks.append("Predicted CLV is 0 MAD or negative, indicating potential churned value or lack of monetization.")
            recommendations.append("Conduct value recovery review or evaluate re-engagement cost-efficiency.")

        # Check for High Churn Risk on High CLV (Dangerous combination)
        churn_risk = safe_float(context.latest_classification.get("churn_risk_score") or dt.get("churn_risk_score"), 0.0)
        if clv_val >= 5000.0 and churn_risk >= 0.60:
            status = "Critical"
            risks.append(f"CRITICAL VALUE AT RISK: High CLV ({clv_val:,.2f} MAD) combined with High Churn Risk ({churn_risk:.2f}).")
            recommendations.insert(0, "IMMEDIATE VIP RETENTION ACTION REQUIRED: Prevent high-value client churn.")

        summary = (
            f"CLV analysis classifies Entity [{context.entity_id}] as {value_tier} "
            f"({clv_val:,.2f} MAD) with status {status}."
        )

        return self.format_output(
            status=status,
            summary=summary,
            observations=observations,
            risks=risks,
            opportunities=opportunities,
            recommendations=recommendations,
            confidence_score=0.90 if clv_val != 0.0 else 0.60,
            evidence=evidence,
        )
