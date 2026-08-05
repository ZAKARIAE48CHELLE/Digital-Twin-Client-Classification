"""
OSMOS LangGraph Supervision — State Schema (Phase 8.7)
======================================================
Defines the serializable TypedDict state schema passed through the LangGraph workflow.

Constraint 3: State is 100% serializable.
No class instances, database handles, or DataFrames are stored in state.
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class SupervisionGraphState(TypedDict, total=False):
    """LangGraph workflow state object for Multi-Agent Supervision."""
    entity_id: str
    selected_agents: List[str]
    include_knowledge: bool
    debate_mode: bool
    storage_mode: str
    context: Dict[str, Any]
    agent_outputs: List[Dict[str, Any]]
    core_agent_outputs: List[Dict[str, Any]]
    operational_agent_outputs: List[Dict[str, Any]]
    debate_output: Dict[str, Any]
    conflicts: List[Dict[str, Any]]
    consensus: Dict[str, Any]
    orchestrator_output: Dict[str, Any]
    approval_actions: List[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    created_at: str
