"""
OSMOS Multi-Agent Supervision Layer (Phase 8.1)
================================================
A read-only, deterministic multi-agent framework for intelligent CRM supervision.
Coordinates specialized agents to inspect Digital Twin state, CLV evolution,
churn risk, persona consistency, campaign history, and journey transitions.
"""

from agents.agent_schemas import AgentContext, AgentOutput, OrchestratorOutput
from agents.base_agent import BaseAgent
from agents.orchestrator_agent import OrchestratorAgent, run_orchestrated_analysis
from agents.agent_registry import AGENT_REGISTRY, get_agent, list_agents

__all__ = [
    "AgentContext",
    "AgentOutput",
    "OrchestratorOutput",
    "BaseAgent",
    "OrchestratorAgent",
    "run_orchestrated_analysis",
    "AGENT_REGISTRY",
    "get_agent",
    "list_agents",
]
