"""
OSMOS Multi-Agent Supervision Layer — Persona Agent (Phase 8.1)
================================================================
Specialized agent for inspecting customer segment assignment, stable persona resolution,
and explaining the architectural distinction between fixed vs dynamic personas.
"""

from typing import Any, Dict, List
from agents.base_agent import BaseAgent
from agents.agent_schemas import AgentContext, AgentOutput, EvidenceItem
from personas.persona_library import DEFAULT_PERSONA_MAP


class PersonaAgent(BaseAgent):
    """
    Evaluates customer segment consistency, stable persona library assignment,
    and enforces the segment-first resolution rule across OSMOS modules.
    """

    def __init__(self):
        super().__init__(
            agent_id="persona",
            agent_name="Persona Agent",
            agent_role="Customer segment alignment & stable vs dynamic persona resolution analysis",
            agent_version="1.0.0",
        )

    def _analyze_implementation(self, context: AgentContext) -> AgentOutput:
        dt = context.latest_digital_twin or {}
        # Determine segment and persona string values
        seg_raw = context.latest_segment or dt.get("customer_segment") or dt.get("segment") or ""
        persona_raw = context.latest_persona or dt.get("persona_name") or dt.get("persona") or ""

        segment = str(seg_raw).strip() if seg_raw and str(seg_raw).strip() != "None" else "Unknown"
        persona_name = str(persona_raw).strip() if persona_raw and str(persona_raw).strip() != "None" else "Unknown"

        dynamic_ctx = context.dynamic_persona_context or {}

        observations: List[str] = []
        risks: List[str] = []
        opportunities: List[str] = []
        recommendations: List[str] = []
        evidence: List[Dict[str, Any]] = []

        # Check against DEFAULT_PERSONA_MAP official names
        official_names = list(set(p["persona_name"] for p in DEFAULT_PERSONA_MAP.values()))
        is_official = persona_name in official_names and persona_name != "Unknown"

        status = "OK"

        # Evidence Traceability
        evidence.append(
            EvidenceItem(
                metric_name="customer_segment",
                value=segment,
                threshold="Valid Cohort Segment",
                interpretation=f"Entity assigned to segment '{segment}'.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="stable_persona",
                value=persona_name,
                threshold="Official Persona Library",
                interpretation=(
                    f"Matched to stable persona '{persona_name}'"
                    if is_official else f"Persona '{persona_name}' not in official library."
                ),
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="resolution_rule",
                value="Segment-First Protocol",
                threshold="Strict Hierarchy",
                interpretation="Digital Twin resolves persona strictly via customer_segment mapping.",
            ).to_dict()
        )

        observations.append(f"Customer Segment: '{segment}' | Stable Persona: '{persona_name}'.")
        observations.append("Resolution Protocol: Entity -> Digital Twin -> Segment -> Persona Library (Segment-First).")

        # Required Fix 5 — Persona Mapping Warning/Critical
        churn_ctx = context.latest_churn
        churn_status = None
        churn_score = 0.0

        if churn_ctx:
            if isinstance(churn_ctx, dict):
                churn_status = churn_ctx.get("status")
                churn_score = float(churn_ctx.get("churn_risk_score", 0.0) or 0.0)
            else:
                churn_status = getattr(churn_ctx, "status", None)
                churn_score = float(getattr(churn_ctx, "churn_risk_score", 0.0) or 0.0)

        dt_churn_score = float(dt.get("churn_risk_score", 0.0) or 0.0)

        churn_risk_high = (
            churn_status in {"Warning", "Critical"} or
            churn_score >= 0.60 or
            dt_churn_score >= 0.60
        )

        if segment != "Unknown" and (persona_name == "Unknown" or not is_official):
            status = "Critical" if churn_risk_high else "Warning"
            observations.append(f"Segment '{segment}' exists, but stable persona resolution returned None or unmapped value.")
            risks.append(f"Persona mapping incomplete for segment '{segment}'.")
            recommendations.append("Check persona_library for segment mapping and rerun segment-first persona resolution.")

        elif segment == "Unknown" and persona_name == "Unknown":
            status = "Warning"
            risks.append("Missing segment and persona assignment in Digital Twin context.")
            recommendations.append("Run Segment Classifier and Persona Matcher on this entity.")

        elif is_official:
            opportunities.append(f"Entity is mapped to official strategic persona '{persona_name}' for targeted messaging.")
            recommendations.append(f"Use '{persona_name}' value proposition guidelines for communication styling.")

        # Explain Stable vs Dynamic Personas
        dyn_cluster = dynamic_ctx.get("cluster_id")
        if dyn_cluster is not None:
            observations.append(
                f"Exploratory Dynamic Persona active (Cluster #{dyn_cluster}). "
                "Dynamic personas are temporary, data-driven profiles used ONLY for exploratory clustering analysis."
            )
            recommendations.append("Do not replace official stable persona with dynamic cluster personas for automated campaigns.")
        else:
            observations.append(
                "Note: Stable personas represent fixed strategic interpretation profiles. "
                "Dynamic personas are temporary exploratory cluster profiles."
            )

        summary = (
            f"Persona Agent evaluated Entity [{context.entity_id}] under segment '{segment}' "
            f"and stable persona '{persona_name}' (Status: {status})."
        )

        return self.format_output(
            status=status,
            summary=summary,
            observations=observations,
            risks=risks,
            opportunities=opportunities,
            recommendations=recommendations,
            confidence_score=0.95 if is_official else 0.70,
            evidence=evidence,
        )
