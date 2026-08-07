"""
OSMOS Multi-Agent Supervision Layer — Database Audit Agent (Phase 8.2)
======================================================================
Specialized agent for auditing PostgreSQL database table completeness,
orphaned event references, history versioning, and storage mode consistency.
"""

from typing import Any, Dict, List
import pandas as pd

from agents.base_agent import BaseAgent
from agents.agent_schemas import AgentContext, AgentOutput, EvidenceItem
from agents.context_builder import get_database_record_counts, get_event_reference_check


class DatabaseAuditAgent(BaseAgent):
    """
    Audits database record presence, orphaned event references,
    history table completeness, and storage mode fallback status (Read-Only).
    """

    def __init__(self):
        super().__init__(
            agent_id="database_audit",
            agent_name="Database Audit Agent",
            agent_role="PostgreSQL table completeness, orphaned event references & schema audit",
            agent_version="1.0.0",
        )

    def _analyze_implementation(self, context: AgentContext) -> AgentOutput:
        entity_id = context.entity_id
        dt = context.latest_digital_twin or {}
        storage_mode = context.storage_mode or "excel"

        counts = get_database_record_counts(entity_id)
        ref_check = get_event_reference_check(entity_id)

        observations: List[str] = []
        risks: List[str] = []
        opportunities: List[str] = []
        recommendations: List[str] = []
        evidence: List[Dict[str, Any]] = []

        dt_count = counts.get("digital_twin_count", 0)
        event_count = counts.get("event_count", len(context.recent_events or []))
        rfm_count = counts.get("rfm_count", 0)
        clv_count = counts.get("clv_count", 0)
        seg_count = counts.get("segment_count", 0)
        campaign_count = counts.get("campaign_count", len(context.campaign_history or []))
        journey_count = counts.get("journey_step_count", len(context.journey_history or []))

        missing_refs = ref_check.get("missing_event_refs", [])
        missing_ref_count = len(missing_refs)

        status = "OK"

        # Evidence Traceability
        evidence.append(
            EvidenceItem(
                metric_name="storage_mode",
                value=storage_mode,
                threshold="postgres",
                interpretation=f"Active database backend is '{storage_mode}'.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="digital_twin_snapshots",
                value=dt_count,
                threshold=">=1 Record",
                interpretation=f"Found {dt_count} digital twin snapshot records.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="event_history_records",
                value=event_count,
                threshold=">=1 Record",
                interpretation=f"Found {event_count} persisted customer interaction events.",
            ).to_dict()
        )

        evidence.append(
            EvidenceItem(
                metric_name="orphaned_event_references",
                value=missing_ref_count,
                threshold="0 Missing",
                interpretation=(
                    "No orphaned event references found."
                    if missing_ref_count == 0 else f"Found {missing_ref_count} orphaned event references."
                ),
            ).to_dict()
        )

        observations.append(f"Storage backend mode: '{storage_mode}'.")
        observations.append(
            f"Record distribution for [{entity_id}]: DT Snapshots={dt_count}, Events={event_count}, "
            f"RFM={rfm_count}, CLV={clv_count}, Segments={seg_count}, Campaigns={campaign_count}, Journey Steps={journey_count}."
        )

        # Storage mode evaluation
        if storage_mode == "excel":
            observations.append("PostgreSQL is offline or unconfigured. Operating in Excel fallback mode.")
            recommendations.append("Connect PostgreSQL backend to enable multi-table historical audit tracking.")

        # Table completeness checks (PostgreSQL mode)
        if storage_mode == "postgres":
            missing_tables = []
            if dt_count == 0: missing_tables.append("digital_twin_snapshot")
            if event_count == 0: missing_tables.append("customer_event_history")
            if rfm_count == 0: missing_tables.append("rfm_es_scores")
            if clv_count == 0: missing_tables.append("model_predictions_history")
            if seg_count == 0: missing_tables.append("segment_persona_history")

            if missing_tables:
                status = "Warning"
                if missing_ref_count == 0:
                    risks.append(f"Demo readiness / initialization warning: Missing entity history records in PostgreSQL tables: {', '.join(missing_tables)}.")
                else:
                    risks.append(f"Data integrity issue: Missing entity history records in PostgreSQL tables: {', '.join(missing_tables)}.")
                recommendations.append(f"Run data pipeline and initial snapshot seed for Entity [{entity_id}].")
            else:
                opportunities.append("Entity has complete multi-table audit trail across PostgreSQL history tables.")

        # Orphaned event reference check
        if missing_ref_count > 0:
            status = "Warning"
            risks.append(f"Data integrity issue: {missing_ref_count} journey/campaign records reference event IDs missing from customer_event_history.")
            recommendations.append("Verify event persistence pipeline to prevent orphaned foreign event keys.")

        # Inconsistency: Prospect vs Purchase count
        freq = float(dt.get("frequency") or 0.0)
        if context.entity_type == "Prospect" and freq > 0:
            status = "Warning"
            risks.append(f"Entity consistency conflict: Labeled 'Prospect' but record indicates {int(freq)} purchases.")
            recommendations.append("Update entity_type classification from Prospect to Client.")

        if not recommendations:
            recommendations.append("Database tables and foreign references are clean and synchronized.")

        summary = (
            f"Database Audit Agent verified Entity [{entity_id}] under '{storage_mode}' mode "
            f"with status {status} ({missing_ref_count} orphaned references)."
        )

        return self.format_output(
            status=status,
            summary=summary,
            observations=observations,
            risks=risks,
            opportunities=opportunities,
            recommendations=recommendations,
            confidence_score=0.95 if storage_mode == "postgres" else 0.75,
            evidence=evidence,
        )
