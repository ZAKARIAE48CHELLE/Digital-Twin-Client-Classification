"""
OSMOS Multi-Agent Supervision Layer — Context Builder (Phase 8.1)
===================================================================
Constructs a unified, read-only AgentContext for a specific entity.
Safely extracts data from PostgreSQL or Excel fallback, DataFrame rows,
event history, predicted CLV/RFM, campaign history, journey steps,
and dynamic persona context.
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


def get_campaign_history(entity_id: str) -> List[Dict[str, Any]]:
    """Retrieves campaign dispatches and responses for entity (Read-Only)."""
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
            logger.debug(f"PostgreSQL campaign history fallback for {entity_id}: {e}")

    return campaigns


def get_journey_history(entity_id: str) -> List[Dict[str, Any]]:
    """Retrieves customer journey step transitions for entity (Read-Only)."""
    journeys = []
    if get_storage_backend() == "postgres" and is_postgres_available():
        try:
            from database.db import get_cursor
            with get_cursor(commit=False) as cur:
                cur.execute(
                    """
                    SELECT step_id, scenario_id, entity_id, current_stage, next_stage, action_taken, status, created_at
                    FROM journey_step_history
                    WHERE entity_id = %s
                    ORDER BY created_at DESC LIMIT 20;
                    """,
                    (entity_id,),
                )
                rows = cur.fetchall()
                if rows:
                    journeys = [dict(r) for r in rows]
        except Exception as e:
            logger.debug(f"PostgreSQL journey history fallback for {entity_id}: {e}")

    return journeys


def get_dynamic_persona_context(entity_id: str) -> Dict[str, Any]:
    """Retrieves dynamic exploratory persona context if generated (Read-Only)."""
    # Dynamic personas are exploratory and in-memory or session-based
    return {"cluster_id": None, "dynamic_persona_title": None, "exploratory_only": True}


def build_entity_agent_context(
    entity_id: str,
    df: Optional[pd.DataFrame] = None,
    history_df: Optional[pd.DataFrame] = None,
) -> AgentContext:
    """
    Main Context Builder entrypoint.
    Assembles a complete, immutable AgentContext for an entity in READ-ONLY mode.
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

    # Recent events, campaigns, journey
    recent_events = get_recent_events(str_entity_id)
    campaign_history = get_campaign_history(str_entity_id)
    journey_history = get_journey_history(str_entity_id)
    dynamic_persona_ctx = get_dynamic_persona_context(str_entity_id)

    storage_mode = get_storage_backend() if is_postgres_available() else "excel"

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
        journey_history=journey_history,
        dynamic_persona_context=dynamic_persona_ctx,
        storage_mode=storage_mode,
    )
