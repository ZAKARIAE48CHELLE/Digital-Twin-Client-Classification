"""
OSMOS Multi-Agent Supervision Layer — Context Builder (Phase 8.2)
===================================================================
Constructs a unified, read-only AgentContext for a specific entity.
Safely extracts data from PostgreSQL or Excel fallback, DataFrame rows,
event history, predicted CLV/RFM, campaign dispatches & responses,
journey scenarios & steps, database record counts, and demo readiness indicators.
"""

import logging
from typing import Any, Dict, List, Optional
import pandas as pd

from agents.agent_schemas import AgentContext
from storage.storage_manager import get_storage_backend
from admin.database_metrics import is_postgres_available

logger = logging.getLogger("OSMOS_CONTEXT_BUILDER")


def get_latest_entity_state(entity_id: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Retrieves the latest entity record from DataFrame or database (Read-Only)."""
    if df is not None and not df.empty:
        if "entity_id" in df.columns:
            matches = df[df["entity_id"].astype(str) == str(entity_id)]
            if not matches.empty:
                return matches.iloc[0].to_dict()

    # Try PostgreSQL read if available
    if get_storage_backend() == "postgres" and is_postgres_available():
        try:
            from database.db import get_cursor
            with get_cursor(commit=False) as cur:
                cur.execute(
                    "SELECT * FROM digital_twin_snapshot WHERE entity_id = %s ORDER BY created_at DESC LIMIT 1;",
                    (entity_id,),
                )
                row = cur.fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            logger.debug(f"PostgreSQL entity lookup fallback for {entity_id}: {e}")

    return {}


def get_recent_events(entity_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieves recent event history for entity (Read-Only)."""
    events = []
    if get_storage_backend() == "postgres" and is_postgres_available():
        try:
            from database.db import get_cursor
            with get_cursor(commit=False) as cur:
                cur.execute(
                    """
                    SELECT event_id, entity_id, event_name, channel, sentiment_score, created_at
                    FROM customer_event_history
                    WHERE entity_id = %s
                    ORDER BY created_at DESC LIMIT %s;
                    """,
                    (entity_id, limit),
                )
                rows = cur.fetchall()
                if rows:
                    events = [dict(r) for r in rows]
        except Exception as e:
            logger.debug(f"PostgreSQL event lookup fallback for {entity_id}: {e}")

    return events


def get_latest_predictions(entity_id: str) -> Dict[str, Any]:
    """Retrieves latest ML predictions (CLV, Churn, RFM) for entity (Read-Only)."""
    if get_storage_backend() == "postgres" and is_postgres_available():
        try:
            from database.db import get_cursor
            with get_cursor(commit=False) as cur:
                cur.execute(
                    "SELECT * FROM model_predictions_history WHERE entity_id = %s ORDER BY created_at DESC LIMIT 1;",
                    (entity_id,),
                )
                row = cur.fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            logger.debug(f"PostgreSQL predictions lookup fallback for {entity_id}: {e}")

    return {}


def get_latest_segment_persona(entity_id: str) -> Dict[str, Any]:
    """Retrieves latest customer segment & stable persona assignment (Read-Only)."""
    if get_storage_backend() == "postgres" and is_postgres_available():
        try:
            from database.db import get_cursor
            with get_cursor(commit=False) as cur:
                cur.execute(
                    "SELECT customer_segment, persona_name FROM segment_persona_history WHERE entity_id = %s ORDER BY created_at DESC LIMIT 1;",
                    (entity_id,),
                )
                row = cur.fetchone()
                if row:
                    return {"customer_segment": row.get("customer_segment"), "persona_name": row.get("persona_name")}
        except Exception as e:
            logger.debug(f"PostgreSQL segment/persona lookup fallback for {entity_id}: {e}")

    return {}


def get_campaign_dispatches_for_entity(entity_id: str) -> List[Dict[str, Any]]:
    """Retrieves campaign dispatches for entity (Read-Only)."""
    campaigns = []
    if get_storage_backend() == "postgres" and is_postgres_available():
        try:
            from database.db import get_cursor
            with get_cursor(commit=False) as cur:
                cur.execute(
                    """
                    SELECT dispatch_id, campaign_id, entity_id, channel, status, created_at
                    FROM campaign_dispatches
                    WHERE entity_id = %s
                    ORDER BY created_at DESC LIMIT 20;
                    """,
                    (entity_id,),
                )
                rows = cur.fetchall()
                if rows:
                    campaigns = [dict(r) for r in rows]
        except Exception as e:
            logger.debug(f"PostgreSQL campaign dispatches fallback for {entity_id}: {e}")

    return campaigns


def get_campaign_responses_for_entity(entity_id: str) -> List[Dict[str, Any]]:
    """Retrieves campaign responses for entity (Read-Only)."""
    responses = []
    if get_storage_backend() == "postgres" and is_postgres_available():
        try:
            from database.db import get_cursor
            with get_cursor(commit=False) as cur:
                cur.execute(
                    """
                    SELECT response_id, campaign_id, entity_id, response_type, response_score, event_id, created_at
                    FROM campaign_responses
                    WHERE entity_id = %s
                    ORDER BY created_at DESC LIMIT 20;
                    """,
                    (entity_id,),
                )
                rows = cur.fetchall()
                if rows:
                    responses = [dict(r) for r in rows]
        except Exception as e:
            logger.debug(f"PostgreSQL campaign responses fallback for {entity_id}: {e}")

    return responses


def get_journey_scenarios_for_entity(entity_id: str) -> List[Dict[str, Any]]:
    """Retrieves journey scenarios for entity (Read-Only)."""
    scenarios = []
    if get_storage_backend() == "postgres" and is_postgres_available():
        try:
            from database.db import get_cursor
            with get_cursor(commit=False) as cur:
                cur.execute(
                    """
                    SELECT scenario_id, entity_id, scenario_name, current_stage, status, created_at, updated_at
                    FROM journey_scenarios
                    WHERE entity_id = %s
                    ORDER BY updated_at DESC LIMIT 10;
                    """,
                    (entity_id,),
                )
                rows = cur.fetchall()
                if rows:
                    scenarios = [dict(r) for r in rows]
        except Exception as e:
            logger.debug(f"PostgreSQL journey scenarios fallback for {entity_id}: {e}")

    return scenarios


def get_journey_steps_for_entity(entity_id: str) -> List[Dict[str, Any]]:
    """Retrieves journey step transitions for entity (Read-Only)."""
    steps = []
    if get_storage_backend() == "postgres" and is_postgres_available():
        try:
            from database.db import get_cursor
            with get_cursor(commit=False) as cur:
                cur.execute(
                    """
                    SELECT step_id, scenario_id, entity_id, current_stage, next_stage, action_taken, trigger_event_id, status, created_at
                    FROM journey_step_history
                    WHERE entity_id = %s
                    ORDER BY created_at DESC LIMIT 20;
                    """,
                    (entity_id,),
                )
                rows = cur.fetchall()
                if rows:
                    steps = [dict(r) for r in rows]
        except Exception as e:
            logger.debug(f"PostgreSQL journey step history fallback for {entity_id}: {e}")

    return steps


def get_event_reference_check(entity_id: str) -> Dict[str, Any]:
    """Audits whether journey/campaign event IDs exist in customer_event_history (Read-Only)."""
    result = {"missing_event_refs": [], "valid_event_refs_count": 0, "total_refs_checked": 0}
    if get_storage_backend() == "postgres" and is_postgres_available():
        try:
            from database.db import get_cursor
            steps = get_journey_steps_for_entity(entity_id)
            responses = get_campaign_responses_for_entity(entity_id)

            ref_ids = set()
            for s in steps:
                if s.get("trigger_event_id"):
                    ref_ids.add(str(s["trigger_event_id"]))
            for r in responses:
                if r.get("event_id"):
                    ref_ids.add(str(r["event_id"]))

            if ref_ids:
                result["total_refs_checked"] = len(ref_ids)
                with get_cursor(commit=False) as cur:
                    cur.execute(
                        "SELECT event_id FROM customer_event_history WHERE event_id = ANY(%s);",
                        (list(ref_ids),),
                    )
                    found = set(r.get("event_id") for r in cur.fetchall())
                    result["valid_event_refs_count"] = len(found)
                    result["missing_event_refs"] = list(ref_ids - found)
        except Exception as e:
            logger.debug(f"PostgreSQL event reference check fallback for {entity_id}: {e}")

    return result


def get_database_record_counts(entity_id: str) -> Dict[str, int]:
    """Audits record counts across entity tables in PostgreSQL (Read-Only)."""
    counts = {
        "digital_twin_count": 0,
        "event_count": 0,
        "rfm_count": 0,
        "clv_count": 0,
        "classification_count": 0,
        "segment_count": 0,
        "campaign_count": 0,
        "journey_step_count": 0,
    }

    if get_storage_backend() == "postgres" and is_postgres_available():
        try:
            from database.db import get_cursor
            with get_cursor(commit=False) as cur:
                cur.execute("SELECT COUNT(*) FROM digital_twin_snapshot WHERE entity_id = %s;", (entity_id,))
                counts["digital_twin_count"] = cur.fetchone().get("count", 0)

                cur.execute("SELECT COUNT(*) FROM customer_event_history WHERE entity_id = %s;", (entity_id,))
                counts["event_count"] = cur.fetchone().get("count", 0)

                cur.execute("SELECT COUNT(*) FROM rfm_es_scores WHERE entity_id = %s;", (entity_id,))
                counts["rfm_count"] = cur.fetchone().get("count", 0)

                cur.execute("SELECT COUNT(*) FROM model_predictions_history WHERE entity_id = %s;", (entity_id,))
                counts["clv_count"] = cur.fetchone().get("count", 0)

                cur.execute("SELECT COUNT(*) FROM segment_persona_history WHERE entity_id = %s;", (entity_id,))
                counts["segment_count"] = cur.fetchone().get("count", 0)

                cur.execute("SELECT COUNT(*) FROM campaign_dispatches WHERE entity_id = %s;", (entity_id,))
                counts["campaign_count"] = cur.fetchone().get("count", 0)

                cur.execute("SELECT COUNT(*) FROM journey_step_history WHERE entity_id = %s;", (entity_id,))
                counts["journey_step_count"] = cur.fetchone().get("count", 0)
        except Exception as e:
            logger.debug(f"PostgreSQL database record counts fallback for {entity_id}: {e}")

    return counts


def get_dynamic_persona_context(entity_id: str) -> Dict[str, Any]:
    """Retrieves dynamic exploratory persona context if generated (Read-Only)."""
    return {"cluster_id": None, "dynamic_persona_title": None, "exploratory_only": True}


def build_entity_agent_context(
    entity_id: str,
    df: Optional[pd.DataFrame] = None,
    history_df: Optional[pd.DataFrame] = None,
    include_knowledge: bool = False,
) -> AgentContext:
    """
    Main Context Builder entrypoint.
    Assembles a complete, immutable AgentContext for an entity in READ-ONLY mode.
    Optionally fetches decision memory and knowledge base snippets when include_knowledge=True.
    """
    str_entity_id = str(entity_id).strip()
    entity_state = get_latest_entity_state(str_entity_id, df=df)

    # Determine Entity Type (Prospect vs Client)
    raw_type = entity_state.get("entity_type", "")
    if not raw_type and str_entity_id.startswith("P"):
        entity_type = "Prospect"
    elif not raw_type and str_entity_id.startswith("C"):
        entity_type = "Client"
    else:
        entity_type = str(raw_type) if raw_type else "Client"

    # Extract RFM and CLV dicts
    rfm_dict = {
        "recency_days": entity_state.get("recency_days", entity_state.get("recency")),
        "frequency": entity_state.get("frequency"),
        "monetary_mad": entity_state.get("monetary_mad", entity_state.get("monetary")),
        "rfm_score": entity_state.get("rfm_score", entity_state.get("rfm")),
    }

    predictions = get_latest_predictions(str_entity_id)
    clv_dict = {
        "predicted_clv_amount_mad": predictions.get(
            "predicted_clv_amount_mad",
            entity_state.get("predicted_clv_amount_mad", entity_state.get("predicted_clv", 0.0)),
        ),
        "clv_score": predictions.get("clv_score", entity_state.get("clv_score", 0.0)),
        "clv_segment": predictions.get("clv_segment", entity_state.get("clv_segment", "Unknown")),
    }

    # Extract Segment and Persona
    seg_persona = get_latest_segment_persona(str_entity_id)
    latest_segment = seg_persona.get(
        "customer_segment", entity_state.get("customer_segment", entity_state.get("segment", "Unknown"))
    )
    latest_persona = seg_persona.get(
        "persona_name", entity_state.get("persona_name", entity_state.get("persona", "Unknown"))
    )

    # Recent events, campaigns, journey, database audit
    recent_events = get_recent_events(str_entity_id)
    campaign_dispatches = get_campaign_dispatches_for_entity(str_entity_id)
    campaign_responses = get_campaign_responses_for_entity(str_entity_id)
    journey_scenarios = get_journey_scenarios_for_entity(str_entity_id)
    journey_steps = get_journey_steps_for_entity(str_entity_id)
    ref_check = get_event_reference_check(str_entity_id)
    record_counts = get_database_record_counts(str_entity_id)
    dynamic_persona_ctx = get_dynamic_persona_context(str_entity_id)

    storage_mode = get_storage_backend() if is_postgres_available() else "excel"

    # Merge dispatches & responses into campaign_history
    campaign_history = campaign_dispatches + campaign_responses

    # Optional Phase 8.5 Knowledge Base & Decision Memory Retrieval
    k_results = []
    d_memory = []
    prev_runs = []
    appr_hist = []

    if include_knowledge:
        try:
            from knowledge.decision_memory import get_entity_decision_memory
            from knowledge.knowledge_retriever import retrieve_relevant_knowledge
            from agents.agent_repository import get_agent_runs, get_approval_queue

            d_mem_items = get_entity_decision_memory(str_entity_id)
            d_memory = [m.to_dict() for m in d_mem_items]

            k_items = retrieve_relevant_knowledge(f"governance rule {latest_segment} {latest_persona}", limit=3)
            k_results = [k.to_dict() for k in k_items]

            prev_runs = get_agent_runs(entity_id=str_entity_id, limit=10)
            appr_hist = get_approval_queue(entity_id=str_entity_id, limit=10)
        except Exception as e:
            logger.debug(f"Knowledge memory retrieval fallback for {str_entity_id}: {e}")

    return AgentContext(
        entity_id=str_entity_id,
        entity_type=entity_type,
        latest_digital_twin=entity_state,
        latest_rfm=rfm_dict,
        latest_clv=clv_dict,
        latest_classification={"churn_risk_score": entity_state.get("churn_risk_score", 0.0)},
        latest_segment=str(latest_segment),
        latest_persona=str(latest_persona),
        recent_events=recent_events,
        campaign_history=campaign_history,
        journey_history=journey_steps,
        dynamic_persona_context=dynamic_persona_ctx,
        knowledge_results=k_results,
        decision_memory=d_memory,
        documentation_context=k_results,
        previous_agent_runs=prev_runs,
        approval_history=appr_hist,
        storage_mode=storage_mode,
    )
