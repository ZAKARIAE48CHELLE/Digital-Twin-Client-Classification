"""
OSMOS Multi-Agent Supervision Layer — Digital Twin Agent (Phase 8.1)
====================================================================
Specialized agent for inspecting individual Digital Twin behavioral state,
profile completeness, entity type transitions, and behavioral history anomalies.
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


class DigitalTwinAgent(BaseAgent):
    """
    Analyzes Digital Twin profile integrity, event frequency,
    prospect vs client behavioral consistency, and timeline completeness.
    """

    def __init__(self):
        super().__init__(
            agent_id="digital_twin",
            agent_name="Digital Twin Agent",
            agent_role="Digital Twin behavioral state & profile consistency analysis",
            agent_version="1.0.0",
        )

    def _analyze_implementation(self, context: AgentContext) -> AgentOutput:
        dt = context.latest_digital_twin or {}
        events = context.recent_events or []
        entity_type = context.entity_type or "Client"

        observations: List[str] = []
        risks: List[str] = []
        opportunities: List[str] = []
        recommendations: List[str] = []
        evidence: List[Dict[str, Any]] = []

        if not dt:
            evidence.append(
                EvidenceItem(
                    metric_name="digital_twin_record",
                    value="Missing",
                    threshold="Present",
                    interpretation="No digital twin record found in system context.",
                ).to_dict()
            )
            return self.format_output(
                status="Insufficient Data",
                summary=f"No active Digital Twin record available for Entity [{context.entity_id}].",
                observations=["Digital Twin snapshot dictionary is empty or unavailable."],
                risks=["Supervision restricted due to missing entity parameters."],
                recommendations=["Verify entity ingestion and run Digital Twin builder."],
                confidence_score=0.3,
                evidence=evidence,
            )

        # Profile Completeness Traceability
        known_keys = [
            "entity_type", "recency_days", "frequency", "monetary_mad",
            "predicted_clv_amount_mad", "churn_risk_score", "customer_segment", "persona_name"
        ]
        present_count = sum(1 for k in known_keys if dt.get(k) is not None and not pd.isna(dt.get(k)))
        completeness_pct = round((present_count / len(known_keys)) * 100.0, 1)

        evidence.append(
            EvidenceItem(
                metric_name="profile_completeness",
                value=f"{completeness_pct}%",
                threshold=">=70.0%",
                interpretation=f"Profile has {present_count}/{len(known_keys)} key analytical fields populated.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="entity_type",
                value=entity_type,
                threshold="Prospect | Client",
                interpretation=f"Entity operates under {entity_type} behavioral flow.",
            ).to_dict()
        )

        event_count = len(events)
        evidence.append(
            EvidenceItem(
                metric_name="recent_event_count",
                value=event_count,
                threshold=">=1 event",
                interpretation=f"Found {event_count} recorded interaction events in history.",
            ).to_dict()
        )

        # Behavioral & Inconsistency Evaluation
        observations.append(f"Entity [{context.entity_id}] classified as {entity_type} with {completeness_pct}% profile completeness.")
        observations.append(f"Recorded {event_count} historical interaction events.")

        status = "OK"

        # Inconsistency: Prospect with high purchase frequency
        freq = safe_float(dt.get("frequency"), 0.0)
        monetary = safe_float(dt.get("monetary_mad") or dt.get("monetary"), 0.0)
        recency = safe_float(dt.get("recency_days") or dt.get("recency"), 0.0)

        if entity_type == "Prospect" and (freq > 0 or monetary > 0):
            status = "Warning"
            risks.append(f"Entity is labeled 'Prospect' but shows {freq} transactions totaling {monetary} MAD.")
            recommendations.append("Update entity classification from Prospect to Client.")
        elif entity_type == "Client" and freq == 0 and monetary == 0:
            status = "Warning"
            risks.append("Entity labeled 'Client' has zero recorded purchases in Digital Twin snapshot.")
            recommendations.append("Audit transaction history ingestion for this entity.")

        # Event sentiment signals
        negative_events = sum(1 for e in events if safe_float(e.get("sentiment_score"), 0.0) < -0.3)
        if negative_events > 0:
            status = "Warning" if status != "Critical" else "Critical"
            risks.append(f"Detected {negative_events} negative sentiment events in recent interaction history.")
            recommendations.append("Inspect timeline event log for specific customer friction points.")

        # Engagement opportunities
        if recency > 0 and recency <= 30 and freq >= 3:
            opportunities.append("High recent engagement and recurring frequency signal upselling potential.")
            recommendations.append("Consider targeted engagement or premium loyalty offering.")

        if not recommendations:
            recommendations.append("Maintain routine Digital Twin monitoring.")

        summary = (
            f"Digital Twin analysis for {entity_type} [{context.entity_id}] indicates "
            f"{status} state with {event_count} recent events and {completeness_pct}% completeness."
        )

        return self.format_output(
            status=status,
            summary=summary,
            observations=observations,
            risks=risks,
            opportunities=opportunities,
            recommendations=recommendations,
            confidence_score=0.95 if completeness_pct >= 70 else 0.70,
            evidence=evidence,
        )
