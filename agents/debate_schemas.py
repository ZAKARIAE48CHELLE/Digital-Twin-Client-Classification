"""
OSMOS Multi-Agent Supervision Layer — Agent Debate Schemas (Phase 8.4)
======================================================================
Dataclasses and schemas for agent debate statements, conflict detection,
consensus synthesis, and structured debate outputs.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class AgentDebateStatement:
    """Represents a structured analytical position submitted by a specialized agent into debate."""
    statement_id: str
    agent_id: str
    agent_name: str
    position: str
    supporting_evidence: List[str] = field(default_factory=list)
    concern_level: str = "Low"  # Low, Medium, High, Critical
    proposed_action: str = ""
    confidence_score: float = 0.85

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentConflict:
    """Represents a detected contradiction or priority clash between two or more agent positions."""
    conflict_id: str
    conflict_type: str  # Risk vs Opportunity, Status Disagreement, Data Quality Override, Persona Conflict, etc.
    agents_involved: List[str] = field(default_factory=list)
    description: str = ""
    severity: str = "Medium"  # Low, Medium, High, Critical
    evidence: List[str] = field(default_factory=list)
    resolution_suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentConsensus:
    """Represents the synthesized consensus decision and prioritized next action after debate."""
    consensus_status: str  # Strong Consensus, Partial Consensus, Conflict Detected, Insufficient Data, Critical Conflict
    agreed_risks: List[str] = field(default_factory=list)
    agreed_opportunities: List[str] = field(default_factory=list)
    agreed_recommendations: List[str] = field(default_factory=list)
    unresolved_conflicts: List[Dict[str, Any]] = field(default_factory=list)
    priority_action: str = ""
    confidence_score: float = 0.85
    reasoning_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DebateOutput:
    """Complete output artifact produced by the Agent Debate & Collaboration Engine."""
    entity_id: str
    debate_mode: bool = True
    agent_statements: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    consensus: Dict[str, Any] = field(default_factory=dict)
    final_debate_summary: str = ""
    llm_debate_summary: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
