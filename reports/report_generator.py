"""
OSMOS Executive Report Generator — Generator (Phase 8.6)
=========================================================
Report compilation engine linking context builders with markdown section templates.

Read-Only Guarantee: Generates report text deterministically from read-only contexts.
Zero core database or DataFrame mutations.
"""

import logging
from typing import Optional, Tuple
import pandas as pd

from reports.report_schemas import ReportContext
from reports.report_context_builder import (
    build_entity_report_context,
    build_agent_run_report_context,
    build_journey_report_context,
    build_system_report_context,
)
from reports.report_templates import (
    render_report_title_page,
    render_executive_summary,
    render_digital_twin_section,
    render_scores_section,
    render_persona_section,
    render_agent_supervision_section,
    render_debate_consensus_section,
    render_approval_history_section,
    render_knowledge_evidence_section,
    render_final_recommendation_section,
)

logger = logging.getLogger("OSMOS_REPORT_GENERATOR")


def generate_report_markdown(ctx: ReportContext) -> str:
    """Compiles a complete structured Markdown report from a ReportContext."""
    sections = [
        render_report_title_page(ctx),
        render_executive_summary(ctx),
        render_digital_twin_section(ctx),
        render_scores_section(ctx),
        render_persona_section(ctx),
        render_agent_supervision_section(ctx),
        render_debate_consensus_section(ctx),
        render_approval_history_section(ctx),
        render_knowledge_evidence_section(ctx),
        render_final_recommendation_section(ctx),
    ]
    return "\n".join(sections)


def generate_entity_executive_report(
    entity_id: str,
    df: Optional[pd.DataFrame] = None,
) -> Tuple[str, ReportContext]:
    """Generates a complete Entity Executive Report markdown and context."""
    ctx = build_entity_report_context(entity_id=entity_id, df=df)
    md_text = generate_report_markdown(ctx)
    return md_text, ctx


def generate_agent_run_report(run_id: int) -> Tuple[str, ReportContext]:
    """Generates an Agent Run Report markdown and context for a saved run."""
    ctx = build_agent_run_report_context(run_id=run_id)
    md_text = generate_report_markdown(ctx)
    return md_text, ctx


def generate_journey_report(
    entity_id: str = "P_DEMO_001",
    scenario_id: Optional[int] = None,
) -> Tuple[str, ReportContext]:
    """Generates a Customer Journey Report markdown and context."""
    ctx = build_journey_report_context(entity_id=entity_id, scenario_id=scenario_id)
    md_text = generate_report_markdown(ctx)
    return md_text, ctx


def generate_system_overview_report() -> Tuple[str, ReportContext]:
    """Generates a System Overview Report markdown and context."""
    ctx = build_system_report_context()
    md_text = generate_report_markdown(ctx)
    return md_text, ctx
