"""
OSMOS Executive Report Generator — Schemas (Phase 8.6)
======================================================
Dataclasses for ReportContext, ReportSection, and ReportExportResult.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ReportContext:
    """Complete context dictionary assembled for report compilation."""
    report_type: str = "Entity Executive Report"  # "Entity Executive Report", "Agent Run Report", "Journey Report", "System Overview Report"
    entity_id: Optional[str] = None
    run_id: Optional[int] = None
    scenario_id: Optional[int] = None
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    storage_mode: str = "excel"
    entity_profile: Dict[str, Any] = field(default_factory=dict)
    digital_twin_state: Dict[str, Any] = field(default_factory=dict)
    latest_scores: Dict[str, Any] = field(default_factory=dict)
    recent_events: List[Dict[str, Any]] = field(default_factory=list)
    campaign_history: List[Dict[str, Any]] = field(default_factory=list)
    journey_history: List[Dict[str, Any]] = field(default_factory=list)
    agent_run: Dict[str, Any] = field(default_factory=dict)
    agent_outputs: List[Dict[str, Any]] = field(default_factory=list)
    debate_output: Dict[str, Any] = field(default_factory=dict)
    approval_history: List[Dict[str, Any]] = field(default_factory=list)
    knowledge_evidence: List[Dict[str, Any]] = field(default_factory=list)
    final_recommendation: str = ""
    next_best_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReportSection:
    """Represents a single formatted section inside a report."""
    section_id: str
    title: str
    content: str
    tables: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    order: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReportExportResult:
    """Metadata result returned when exporting a report file."""
    file_path: str
    file_name: str
    export_format: str = "markdown"  # "markdown", "html", "pdf"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "Success"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
