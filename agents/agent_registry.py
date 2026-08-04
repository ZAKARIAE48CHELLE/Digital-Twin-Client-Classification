"""
OSMOS Multi-Agent Supervision Layer — Agent Registry (Phase 8.2)
================================================================
Central registry managing all 8 active specialized supervision agents.
"""

import logging
from typing import Dict, List, Optional

from agents.base_agent import BaseAgent
from agents.digital_twin_agent import DigitalTwinAgent
from agents.clv_agent import CLVAgent
from agents.churn_agent import ChurnRiskAgent
from agents.persona_agent import PersonaAgent
from agents.campaign_agent import CampaignAgent
from agents.journey_agent import JourneyAgent
from agents.database_audit_agent import DatabaseAuditAgent
from agents.ui_ux_agent import UIUXAgent

logger = logging.getLogger("OSMOS_AGENT_REGISTRY")


# Global Agent Registry Singleton (8 Active Specialized Agents)
AGENT_REGISTRY: Dict[str, BaseAgent] = {
    # Core Customer Intelligence Agents
    "digital_twin": DigitalTwinAgent(),
    "clv": CLVAgent(),
    "churn": ChurnRiskAgent(),
    "persona": PersonaAgent(),
    # Operational Supervision Agents
    "campaign": CampaignAgent(),
    "journey": JourneyAgent(),
    "database_audit": DatabaseAuditAgent(),
    "ui_ux": UIUXAgent(),
}

CORE_AGENT_IDS = ["digital_twin", "clv", "churn", "persona", "database_audit"]
OPERATIONAL_AGENT_IDS = ["campaign", "journey", "database_audit", "ui_ux"]


def get_agent(agent_id: str) -> Optional[BaseAgent]:
    """Retrieves an agent instance by agent_id."""
    return AGENT_REGISTRY.get(str(agent_id).lower().strip())


def list_agents() -> List[Dict[str, Any]]:
    """Returns a list of metadata dictionaries for all registered agents."""
    return [
        {
            "agent_id": agent.agent_id,
            "agent_name": agent.agent_name,
            "agent_role": agent.agent_role,
            "version": agent.agent_version,
            "category": "Core Customer Intelligence" if agent.agent_id in {"digital_twin", "clv", "churn", "persona"} else "Operational Supervision",
        }
        for agent in AGENT_REGISTRY.values()
    ]


def get_active_agents(selected_ids: Optional[List[str]] = None) -> List[BaseAgent]:
    """
    Returns active agents filtered by selected_ids.
    If selected_ids is None or empty, defaults to the default core supervision set.
    """
    if not selected_ids:
        return [AGENT_REGISTRY[aid] for aid in CORE_AGENT_IDS if aid in AGENT_REGISTRY]

    selected_lower = [str(aid).lower().strip() for aid in selected_ids]
    return [
        agent
        for aid, agent in AGENT_REGISTRY.items()
        if aid in selected_lower
    ]
