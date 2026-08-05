"""
OSMOS Multi-Agent Supervision Layer — Campaign Agent (Phase 8.2)
================================================================
Specialized agent for inspecting campaign dispatch history, response sentiment,
unsubscribed/ignored outcomes, and marketing strategy alignment.
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


class CampaignAgent(BaseAgent):
    """
    Analyzes campaign simulation dispatches, customer responses,
    messaging alignment with CLV/churn risk, and unhandled retention needs.
    """

    def __init__(self):
        super().__init__(
            agent_id="campaign",
            agent_name="Campaign Agent",
            agent_role="Campaign history, dispatch outcome & response alignment analysis",
            agent_version="1.0.0",
        )

    def _analyze_implementation(self, context: AgentContext) -> AgentOutput:
        history = context.campaign_history or []
        dt = context.latest_digital_twin or {}

        clv_val = safe_float(context.latest_clv.get("predicted_clv_amount_mad") or dt.get("predicted_clv_amount_mad"), 0.0)
        churn_risk = safe_float(context.latest_classification.get("churn_risk_score") or dt.get("churn_risk_score"), 0.0)

        observations: List[str] = []
        risks: List[str] = []
        opportunities: List[str] = []
        recommendations: List[str] = []
        evidence: List[Dict[str, Any]] = []

        dispatches = [item for item in history if "status" in item or "dispatch_id" in item]
        responses = [item for item in history if "response_type" in item or "response_id" in item]

        dispatch_count = len(dispatches)
        response_count = len(responses)

        latest_status = dispatches[0].get("status", "None") if dispatches else "None"
        latest_resp_type = responses[0].get("response_type", "None") if responses else "None"
        latest_resp_score = safe_float(responses[0].get("response_score"), 0.0) if responses else 0.0

        # Evidence Traceability
        evidence.append(
            EvidenceItem(
                metric_name="campaign_dispatch_count",
                value=dispatch_count,
                threshold=">=1 Campaign",
                interpretation=f"Recorded {dispatch_count} campaign dispatches.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="latest_campaign_status",
                value=latest_status,
                threshold="Dispatched | Responded",
                interpretation=f"Most recent campaign status is '{latest_status}'.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="latest_response_type",
                value=latest_resp_type,
                threshold="Positive Response",
                interpretation=f"Most recent customer response: '{latest_resp_type}' (Score: {latest_resp_score:.2f}).",
            ).to_dict()
        )

        observations.append(f"Recorded {dispatch_count} dispatches and {response_count} customer responses.")

        status = "OK"

        # Phase 8.5 Decision Memory Check
        if context.decision_memory:
            try:
                from knowledge.decision_memory import check_if_action_was_previously_rejected
                if check_if_action_was_previously_rejected(context.entity_id, "campaign"):
                    risks.append("Decision Memory: A similar campaign recommendation was previously REJECTED by an admin.")
            except Exception as e:
                pass

        if dispatch_count == 0:
            status = "OK"
            observations.append(f"No campaign history logged for Entity [{context.entity_id}].")

            if churn_risk >= 0.60:
                status = "Warning"
                risks.append(f"Entity exhibits high churn risk ({churn_risk * 100:.1f}%) but has ZERO campaign history.")
                recommendations.append("Launch an urgent retention/service recovery campaign simulation.")

            elif clv_val >= 5000.0:
                opportunities.append(f"High-value entity ({clv_val:,.2f} MAD) has no active campaign engagements.")
                recommendations.append("Enroll entity in a VIP loyalty appreciation campaign.")

            elif context.entity_type == "Prospect":
                opportunities.append("Prospect entity is ready for initial marketing onboarding campaign.")
                recommendations.append("Dispatch introductory welcome campaign.")

        else:
            observations.append(f"Latest response: '{latest_resp_type}' | Dispatched campaigns: {dispatch_count}.")

            # Negative response detection
            if latest_resp_type in {"Unsubscribed", "Complained", "Negative"} or latest_resp_score < 0.0:
                status = "Warning"
                risks.append(f"Negative campaign response detected: '{latest_resp_type}' (Score: {latest_resp_score:.2f}).")
                recommendations.append("Pause current campaign track and trigger customer satisfaction audit.")

            # Ignored campaign detection
            elif dispatch_count >= 2 and response_count == 0:
                status = "Warning"
                risks.append(f"Entity has {dispatch_count} dispatched campaigns with zero customer responses (Ignored).")
                recommendations.append("Switch campaign delivery channel (e.g. from Email to In-App Message).")

            # High churn + no recent campaign response
            if churn_risk >= 0.65 and (not responses or latest_resp_type not in {"Purchased", "Converted"}):
                if status != "Critical":
                    status = "Warning"
                risks.append("High churn risk entity lacks positive campaign conversion response.")
                recommendations.append("Dispatch targeted incentive offer or executive follow-up call.")

        if not recommendations:
            recommendations.append("Maintain standard campaign scheduling.")

        summary = (
            f"Campaign Agent evaluated Entity [{context.entity_id}] with status {status} "
            f"({dispatch_count} dispatches, {response_count} responses)."
        )

        return self.format_output(
            status=status,
            summary=summary,
            observations=observations,
            risks=risks,
            opportunities=opportunities,
            recommendations=recommendations,
            confidence_score=0.90 if dispatch_count > 0 else 0.70,
            evidence=evidence,
        )
