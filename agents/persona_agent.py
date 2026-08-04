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
        segment = str(context.latest_segment or dt.get("customer_segment") or dt.get("segment") or "Unknown")
        persona_name = str(context.latest_persona or dt.get("persona_name") or dt.get("persona") or "Unknown")
        dynamic_ctx = context.dynamic_persona_context or {}

        observations: List[str] = []
        risks: List[str] = []
        opportunities: List[str] = []
        recommendations: List[str] = []
        evidence: List[Dict[str, Any]] = []

        # Extract official persona names from DEFAULT_PERSONA_MAP
        official_names = list(set(p["persona_name"] for p in DEFAULT_PERSONA_MAP.values()))
        is_official = persona_name in official_names

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

        if segment == "Unknown" or persona_name == "Unknown":
            status = "Warning"
            risks.append("Missing segment or persona assignment in Digital Twin context.")
            recommendations.append("Run Segment Classifier and Persona Matcher on this entity.")

        elif not is_official:
            status = "Warning"
            risks.append(f"Persona '{persona_name}' is not registered in the official persona library.")
            recommendations.append("Re-run persona matcher to resolve to an official strategic persona.")

        else:
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
            f"Persona Agent verified Entity [{context.entity_id}] under segment '{segment}' "
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
