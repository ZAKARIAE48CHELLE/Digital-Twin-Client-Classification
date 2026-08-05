"""
OSMOS Executive Report Generator Package (Phase 8.6)
====================================================
"""

from reports.report_schemas import ReportContext, ReportSection, ReportExportResult
from reports.report_context_builder import (
    build_entity_report_context,
    build_agent_run_report_context,
    build_journey_report_context,
    build_system_report_context,
)
from reports.report_generator import (
    generate_report_markdown,
    generate_entity_executive_report,
    generate_agent_run_report,
    generate_journey_report,
    generate_system_overview_report,
)
from reports.report_exporter import export_report_to_file, convert_markdown_to_html

__all__ = [
    "ReportContext",
    "ReportSection",
    "ReportExportResult",
    "build_entity_report_context",
    "build_agent_run_report_context",
    "build_journey_report_context",
    "build_system_report_context",
    "generate_report_markdown",
    "generate_entity_executive_report",
    "generate_agent_run_report",
    "generate_journey_report",
    "generate_system_overview_report",
    "export_report_to_file",
    "convert_markdown_to_html",
]
