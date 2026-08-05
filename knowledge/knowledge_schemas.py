"""
OSMOS Agent Knowledge Base — Schemas (Phase 8.5)
================================================
Dataclasses for documents, chunks, search results, and decision memory items.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeDocument:
    """Represents an indexed document source (markdown doc or governance spec)."""
    document_id: Optional[int]
    source_type: str = "documentation"  # "documentation", "system_rule", "agent_memory"
    source_name: str = ""
    title: str = ""
    content: str = ""
    section_name: str = ""
    section_order: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    indexed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeChunk:
    """Represents a text chunk created from an indexed document."""
    chunk_id: Optional[int]
    document_id: int
    chunk_order: int = 1
    chunk_title: str = ""
    chunk_text: str = ""
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    indexed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeResult:
    """Structured result returned by the Knowledge Retriever."""
    source_name: str
    section_name: str
    chunk_title: str
    chunk_text: str
    relevance_score: float = 0.80
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionMemoryItem:
    """Represents a historical administrative decision or agent run for an entity."""
    entity_id: str
    run_id: Optional[int]
    decision_type: str  # "Supervision Run", "Approval Item", "Campaign Dispatch"
    status: str  # "Approved", "Rejected", "Pending", "Converted to Campaign Draft"
    recommendation: str
    outcome: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
