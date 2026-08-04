"""
OSMOS Multi-Agent Supervision Layer — Agent Registry (Phase 8.1)
================================================================
Central registry managing all active specialized agents and placeholder agents.
"""

import logging
from typing import Dict, List, Optional

from agents.base_agent import BaseAgent
from agents.digital_twin_agent import DigitalTwinAgent
from agents.clv_agent import CLVAgent
from agents.churn_agent import ChurnRiskAgent
from agents.persona_agent import PersonaAgent
from agents.agent_schemas import AgentContext, AgentOutput

logger = logging.getLogger("OSMOS_AGENT_REGISTRY")


# Placeholder Agent Base Wrapper for future phase expansion
class PlaceholderAgent(BaseAgent):
    """Generic placeholder agent for Phase 8 expansion (Campaign, Journey, Database Audit, UI/UX)."""

    def __init__(self, agent_id: str, agent_name: str, agent_role: str):
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_role=agent_role,
            agent_version="0.1.0-placeholder",
        )

    def _analyze_implementation(self, context: AgentContext) -> AgentOutput:
        return self.format_output(
            status="OK",
            summary=f"{self.agent_name} is active in placeholder mode (Phase 8.1 baseline).",
            observations=[f"{self.agent_name} context inspected for Entity [{context.entity_id}]."],
            opportunities=["Agent framework prepared for deep analytical expansion."],
            recommendations=["Full domain modeling scheduled for future phase."],
            confidence_score=0.80,
            evidence=[{
                "metric_name": "agent_mode",
                "value": "Placeholder Baseline",
                "threshold": "Phase 8.1 Scope",
                "interpretation": f"{self.agent_name} initialized cleanly.",
            }],
        )


# Global Agent Registry Singleton
AGENT_REGISTRY: Dict[str, BaseAgent] = {
    "digital_twin": DigitalTwinAgent(),
    "clv": CLVAgent(),
    "churn": ChurnRiskAgent(),
    "persona": PersonaAgent(),
    # Placeholders prepared for future phase expansion
    "campaign": PlaceholderAgent("campaign", "Campaign Agent", "Analyzes campaign dispatch history & response simulation"),
    "journey": PlaceholderAgent("journey", "Journey Agent", "Analyzes customer journey stage transitions & bottleneck friction"),
    "database_audit": PlaceholderAgent("database_audit", "Database Audit Agent", "Audits database schema integrity & snapshot sync"),
    "ui_ux": PlaceholderAgent("ui_ux", "UI/UX Agent", "Evaluates admin supervision display clarity & readability"),
}


def get_agent(agent_id: str) -> Optional[BaseAgent]:
    """Retrieves an agent instance by agent_id."""
    return AGENT_REGISTRY.get(str(agent_id).lower().strip())


def list_agents() -> List[Dict[str, str]]:
    """Returns a list of metadata dictionaries for all registered agents."""
    return [
        {
            "agent_id": agent.agent_id,
            "agent_name": agent.agent_name,
            "agent_role": agent.agent_role,
            "version": agent.agent_version,
            "is_placeholder": isinstance(agent, PlaceholderAgent),
        }
        for agent in AGENT_REGISTRY.values()
    ]


def get_active_agents(selected_ids: Optional[List[str]] = None) -> List[BaseAgent]:
    """
    Returns active agents filtered by selected_ids.
    If selected_ids is None or empty, defaults to the core 4 analytical agents.
    """
    if not selected_ids:
        default_ids = ["digital_twin", "clv", "churn", "persona"]
        return [AGENT_REGISTRY[aid] for aid in default_ids if aid in AGENT_REGISTRY]

    selected_lower = [str(aid).lower().strip() for aid in selected_ids]
    return [
        agent
        for aid, agent in AGENT_REGISTRY.items()
        if aid in selected_lower
    ]
