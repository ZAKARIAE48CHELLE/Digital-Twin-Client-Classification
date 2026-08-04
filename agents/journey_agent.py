"""
OSMOS Multi-Agent Supervision Layer — Journey Agent (Phase 8.2)
================================================================
Specialized agent for inspecting customer lifecycle journey scenarios,
step sequence integrity, event reference validity, and before/after snapshot transitions.
"""

from typing import Any, Dict, List
import pandas as pd

from agents.base_agent import BaseAgent
from agents.agent_schemas import AgentContext, AgentOutput, EvidenceItem


class JourneyAgent(BaseAgent):
    """
    Analyzes customer journey scenario progression, step transition sequences,
    event reference integrity, and persona/segment lifecycle evolution.
    """

    def __init__(self):
        super().__init__(
            agent_id="journey",
            agent_name="Journey Agent",
            agent_role="Customer journey scenario, lifecycle progression & step reference analysis",
            agent_version="1.0.0",
        )

    def _analyze_implementation(self, context: AgentContext) -> AgentOutput:
        steps = context.journey_history or []
        dt = context.latest_digital_twin or {}

        observations: List[str] = []
        risks: List[str] = []
        opportunities: List[str] = []
        recommendations: List[str] = []
        evidence: List[Dict[str, Any]] = []

        step_count = len(steps)
        expected_steps = 5  # Standard 5-stage demo lifecycle scenario

        # Identify stage sequence
        stages = [s.get("current_stage") or s.get("next_stage") for s in reversed(steps) if s.get("current_stage") or s.get("next_stage")]
        unique_stages = list(dict.fromkeys(stages))

        # Check trigger_event_id validity
        missing_event_refs = [s for s in steps if not s.get("trigger_event_id")]
        missing_ref_count = len(missing_event_refs)

        # Determine Scenario Status
        scenario_status = "Completed" if step_count >= expected_steps else ("In Progress" if step_count > 0 else "Not Started")
        status = "OK"

        # Evidence Traceability
        evidence.append(
            EvidenceItem(
                metric_name="journey_step_count",
                value=step_count,
                threshold=f"{expected_steps} Steps (Complete Lifecycle)",
                interpretation=f"Recorded {step_count}/{expected_steps} journey lifecycle steps.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="scenario_status",
                value=scenario_status,
                threshold="Completed | In Progress",
                interpretation=f"Scenario execution status: {scenario_status}.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="missing_trigger_event_refs",
                value=missing_ref_count,
                threshold="0 Missing",
                interpretation=(
                    "All steps have valid event references."
                    if missing_ref_count == 0 else f"Found {missing_ref_count} steps without trigger_event_id."
                ),
            ).to_dict()
        )

        if step_count == 0:
            status = "OK"
            observations.append(f"No active journey history logged for Entity [{context.entity_id}].")
            if context.entity_id == "P_DEMO_001":
                opportunities.append("P_DEMO_001 is ready for standard 5-stage lifecycle simulation.")
                recommendations.append("Open Journey Simulator and execute 'Run Full Journey' for P_DEMO_001.")
            else:
                recommendations.append("Initialize a journey scenario for this entity if lifecycle demonstration is needed.")

        else:
            observations.append(f"Journey scenario status: '{scenario_status}' ({step_count}/{expected_steps} steps).")
            if unique_stages:
                observations.append(f"Stage progression: {' -> '.join(unique_stages)}.")

            # Check for completed journey
            if step_count >= expected_steps:
                opportunities.append("Journey successfully completed standard 5-stage lifecycle simulation.")
                recommendations.append("Use journey tree visualizer for presentation mode demonstration.")

            # Check for incomplete journey
            elif step_count < expected_steps:
                status = "Warning"
                risks.append(f"Incomplete journey scenario ({step_count}/{expected_steps} steps executed).")
                recommendations.append("Continue step execution in Journey Simulator to complete the lifecycle scenario.")

            # Check for repeated Step 1 problem
            if step_count >= 2 and len(unique_stages) == 1:
                status = "Warning"
                risks.append(f"Journey is stuck repeating stage '{unique_stages[0]}' across multiple step runs.")
                recommendations.append("Reset demo entity P_DEMO_001 and re-run journey runner.")

            # Check for missing trigger event references
            if missing_ref_count > 0:
                status = "Warning"
                risks.append(f"Found {missing_ref_count} journey steps missing trigger_event_id references.")
                recommendations.append("Verify journey event persistence in PostgreSQL mode.")

        # Detect transition highlights
        if "New Prospect" in stages and "VIP Loyalist" in stages:
            observations.append("Lifecycle clearly demonstrates transition from Prospect to VIP Client.")
        if "At-Risk VIP" in stages or "Churn Risk VIP" in stages:
            observations.append("Lifecycle demonstrates churn risk detection for a high-value entity.")

        summary = (
            f"Journey Agent evaluated Entity [{context.entity_id}] with status {status} "
            f"({scenario_status}, {step_count} steps executed)."
        )

        return self.format_output(
            status=status,
            summary=summary,
            observations=observations,
            risks=risks,
            opportunities=opportunities,
            recommendations=recommendations,
            confidence_score=0.95 if step_count > 0 else 0.70,
            evidence=evidence,
        )
