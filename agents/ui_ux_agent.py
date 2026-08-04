"""
OSMOS Multi-Agent Supervision Layer — UI/UX Agent (Phase 8.2)
================================================================
Specialized agent for evaluating UI readiness, demo presentation quality,
entity data richness for video recording, and contextual guide availability.
"""

from typing import Any, Dict, List
import pandas as pd

from agents.base_agent import BaseAgent
from agents.agent_schemas import AgentContext, AgentOutput, EvidenceItem


class UIUXAgent(BaseAgent):
    """
    Analyzes UI presentation readiness, entity demo suitability,
    presentation mode availability, and visual demonstration readiness.
    """

    def __init__(self):
        super().__init__(
            agent_id="ui_ux",
            agent_name="UI/UX Agent",
            agent_role="UI readiness, presentation quality & demo suitability analysis",
            agent_version="1.0.0",
        )

    def _analyze_implementation(self, context: AgentContext) -> AgentOutput:
        entity_id = context.entity_id
        dt = context.latest_digital_twin or {}
        events = context.recent_events or []
        journeys = context.journey_history or []
        campaigns = context.campaign_history or []

        observations: List[str] = []
        risks: List[str] = []
        opportunities: List[str] = []
        recommendations: List[str] = []
        evidence: List[Dict[str, Any]] = []

        has_events = len(events) > 0
        has_journey = len(journeys) > 0
        has_campaigns = len(campaigns) > 0

        # Calculate Presentation Readiness Score
        readiness_points = 0
        if entity_id == "P_DEMO_001": readiness_points += 30
        else: readiness_points += 15

        if has_events: readiness_points += 20
        if has_journey: readiness_points += 25
        if has_campaigns: readiness_points += 15
        if dt.get("persona_name") and dt.get("persona_name") != "Unknown": readiness_points += 10

        readiness_score = min(100, readiness_points)
        status = "OK" if readiness_score >= 70 else ("Warning" if readiness_score >= 40 else "Insufficient Data")

        # Evidence Traceability
        evidence.append(
            EvidenceItem(
                metric_name="demo_entity_suitability",
                value=entity_id,
                threshold="P_DEMO_001 (Recommended)",
                interpretation=(
                    "Entity P_DEMO_001 is the official multi-stage demonstration entity."
                    if entity_id == "P_DEMO_001" else f"Entity '{entity_id}' is a standard CRM record."
                ),
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="presentation_readiness_score",
                value=f"{readiness_score}%",
                threshold=">=70%",
                interpretation=f"UI demonstration readiness score evaluated at {readiness_score}%.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="has_journey_history",
                value=has_journey,
                threshold="True for Journey Tree Demo",
                interpretation=f"Recorded {len(journeys)} journey step transitions for visual demonstration.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="has_campaign_history",
                value=has_campaigns,
                threshold="True for Campaign Demo",
                interpretation=f"Recorded {len(campaigns)} campaign dispatches/responses for demonstration.",
            ).to_dict()
        )

        observations.append(f"UI presentation readiness score for Entity [{entity_id}]: {readiness_score}%.")
        observations.append(
            f"Demo context elements: Events={has_events} ({len(events)}), "
            f"Journey Steps={has_journey} ({len(journeys)}), Campaigns={has_campaigns} ({len(campaigns)})."
        )

        if entity_id == "P_DEMO_001":
            opportunities.append("P_DEMO_001 is optimal for video recording and executive presentations.")
            if not has_journey:
                recommendations.append("Execute 'Run Full Journey' in Journey Simulator before video recording to populate lifecycle tree.")
            else:
                recommendations.append("Toggle 'Presentation Mode' in Journey Simulator and Agent Supervision Center for clean executive slides.")

        else:
            if not has_events and not has_journey:
                status = "Warning"
                risks.append(f"Entity [{entity_id}] has minimal event/journey data for visual demonstration.")
                recommendations.append("Switch to P_DEMO_001 or run Journey Simulator to generate visual timeline cards.")

        if not recommendations:
            recommendations.append("Toggle 'Presentation Mode' for high-level executive view during live demos.")

        summary = (
            f"UI/UX Agent evaluated Entity [{entity_id}] presentation readiness as "
            f"{status} (Score: {readiness_score}%)."
        )

        return self.format_output(
            status=status,
            summary=summary,
            observations=observations,
            risks=risks,
            opportunities=opportunities,
            recommendations=recommendations,
            confidence_score=0.90,
            evidence=evidence,
        )
