"""
OSMOS Executive Report Generator — Context Builder (Phase 8.6)
==============================================================
Assembles immutable ReportContext objects for Entity Executive Reports,
Agent Run Reports, Journey Reports, and System Overview Reports.

Read-Only Guarantee: Pure analytical context retrieval.
Zero database mutations or DataFrame alterations.
"""

import logging
from typing import Any, Dict, List, Optional
import pandas as pd

from reports.report_schemas import ReportContext
from agents.context_builder import build_entity_agent_context, get_latest_entity_state
from agents.orchestrator_agent import run_orchestrated_analysis
from agents.agent_repository import (
    get_agent_runs,
    get_agent_outputs,
    get_approval_queue,
    is_agent_db_available,
)
from storage.storage_manager import get_storage_backend
from admin.database_metrics import is_postgres_available

logger = logging.getLogger("OSMOS_REPORT_CONTEXT_BUILDER")


def get_latest_agent_run_for_entity(entity_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves the most recent agent supervision run for an entity."""
    runs = get_agent_runs(entity_id=entity_id, limit=1)
    return runs[0] if runs else None


def build_entity_report_context(
    entity_id: str,
    df: Optional[pd.DataFrame] = None,
    include_live_supervision: bool = True,
) -> ReportContext:
    """Assembles a 360° ReportContext for a single entity."""
    str_entity_id = str(entity_id).strip()

    # 1. Build AgentContext with knowledge
    agent_ctx = build_entity_agent_context(str_entity_id, df=df, include_knowledge=True)

    # 2. Run or retrieve agent analysis
    agent_run_dict: Dict[str, Any] = {}
    agent_outputs_list: List[Dict[str, Any]] = []
    debate_dict: Dict[str, Any] = {}
    nba = ""
    recommendation = ""

    latest_run = get_latest_agent_run_for_entity(str_entity_id)
    if latest_run:
        agent_run_dict = latest_run
        agent_outputs_list = get_agent_outputs(latest_run.get("run_id"))
        nba = latest_run.get("recommended_next_best_action", "")
        recommendation = latest_run.get("final_summary", "")

    if include_live_supervision and not agent_run_dict:
        try:
            live_report = run_orchestrated_analysis(
                entity_id=str_entity_id,
                df=df,
                debate_mode=True,
                include_knowledge=True,
            )
            agent_run_dict = live_report.to_dict()
            agent_outputs_list = live_report.agent_outputs
            debate_dict = live_report.debate_output or {}
            nba = live_report.recommended_next_best_action
            recommendation = live_report.final_summary
        except Exception as e:
            logger.debug(f"Live orchestrated analysis fallback for report context: {e}")

    # 3. Retrieve Approval History
    appr_history = get_approval_queue(entity_id=str_entity_id, limit=20)

    # 4. Scores dict
    scores = {
        "rfm_score": agent_ctx.latest_rfm.get("rfm_score", 0.0),
        "recency_days": agent_ctx.latest_rfm.get("recency_days", 0.0),
        "frequency": agent_ctx.latest_rfm.get("frequency", 0.0),
        "monetary_mad": agent_ctx.latest_rfm.get("monetary_mad", 0.0),
        "predicted_clv_mad": agent_ctx.latest_clv.get("predicted_clv_amount_mad", 0.0),
        "clv_score": agent_ctx.latest_clv.get("clv_score", 0.0),
        "clv_segment": agent_ctx.latest_clv.get("clv_segment", "Unknown"),
        "churn_risk_score": agent_ctx.latest_classification.get("churn_risk_score", 0.0),
        "customer_segment": agent_ctx.latest_segment,
        "persona_name": agent_ctx.latest_persona,
    }

    return ReportContext(
        report_type="Entity Executive Report",
        entity_id=str_entity_id,
        run_id=agent_run_dict.get("run_id"),
        storage_mode=agent_ctx.storage_mode,
        entity_profile=agent_ctx.latest_digital_twin,
        digital_twin_state=agent_ctx.latest_digital_twin,
        latest_scores=scores,
        recent_events=agent_ctx.recent_events,
        campaign_history=agent_ctx.campaign_history,
        journey_history=agent_ctx.journey_history,
        agent_run=agent_run_dict,
        agent_outputs=agent_outputs_list,
        debate_output=debate_dict or agent_run_dict.get("debate_output", {}),
        approval_history=appr_history,
        knowledge_evidence=agent_ctx.knowledge_results,
        final_recommendation=recommendation or "Maintain active supervision.",
        next_best_action=nba or "Review profile completeness.",
    )


def build_agent_run_report_context(run_id: int) -> ReportContext:
    """Assembles a ReportContext centered around a specific saved agent run."""
    if not is_agent_db_available():
        return ReportContext(
            report_type="Agent Run Report",
            run_id=run_id,
            final_recommendation="Agent Memory requires PostgreSQL database connection.",
        )

    try:
        from database.db import get_cursor
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT * FROM agent_runs WHERE run_id = %s;", (run_id,))
            run_row = cur.fetchone()
            if not run_row:
                return ReportContext(report_type="Agent Run Report", run_id=run_id)

            run_dict = dict(run_row)
            entity_id = run_dict.get("entity_id")
            outputs = get_agent_outputs(run_id)
            appr_history = get_approval_queue(run_id=run_id)

            return ReportContext(
                report_type="Agent Run Report",
                entity_id=entity_id,
                run_id=run_id,
                storage_mode=run_dict.get("storage_mode", "postgres"),
                agent_run=run_dict,
                agent_outputs=outputs,
                debate_output=run_dict.get("debate_output", {}),
                approval_history=appr_history,
                final_recommendation=run_dict.get("final_summary", ""),
                next_best_action=run_dict.get("recommended_next_best_action", ""),
            )
    except Exception as e:
        logger.error(f"Error building agent run report context for #{run_id}: {e}")

    return ReportContext(report_type="Agent Run Report", run_id=run_id)


def build_journey_report_context(
    entity_id: str = "P_DEMO_001",
    scenario_id: Optional[int] = None,
) -> ReportContext:
    """Assembles a ReportContext for a customer lifecycle journey scenario."""
    from journey.journey_runner import get_latest_scenario_for_entity
    scen = get_latest_scenario_for_entity(entity_id)

    journey_steps: List[Dict[str, Any]] = []
    if scen and is_postgres_available():
        try:
            from database.db import get_cursor
            with get_cursor(commit=False) as cur:
                cur.execute(
                    """
                    SELECT * FROM journey_steps WHERE scenario_id = %s ORDER BY step_order ASC;
                    """,
                    (scen.get("scenario_id"),),
                )
                rows = cur.fetchall()
                if rows:
                    journey_steps = [dict(r) for r in rows]
        except Exception as e:
            logger.debug(f"Journey steps query fallback: {e}")

    return ReportContext(
        report_type="Journey Report",
        entity_id=entity_id,
        scenario_id=scen.get("scenario_id") if scen else None,
        storage_mode=get_storage_backend(),
        journey_history=journey_steps,
        final_recommendation=f"Scenario: {scen.get('scenario_name', 'Default Lifecycle Journey')} | Stage: {scen.get('current_stage', 'Stage 1')}" if scen else "No active journey scenario.",
        next_best_action="Execute next journey transition step.",
    )


def build_system_report_context() -> ReportContext:
    """Assembles a global system overview ReportContext."""
    doc_cnt = 0
    chk_cnt = 0

    if is_postgres_available():
        try:
            from knowledge.knowledge_repository import get_knowledge_index_stats
            k_stats = get_knowledge_index_stats()
            doc_cnt = k_stats.get("document_count", 0)
            chk_cnt = k_stats.get("chunk_count", 0)
        except Exception:
            pass

    return ReportContext(
        report_type="System Overview Report",
        storage_mode=get_storage_backend(),
        knowledge_evidence=[{"document_count": doc_cnt, "chunk_count": chk_cnt}],
        final_recommendation="OSMOS Multi-Agent CRM System operating normally.",
        next_best_action="Review high-priority critical alerts in Supervision Center.",
    )
