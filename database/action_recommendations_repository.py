import logging
import psycopg2.extras
from database.db import get_cursor, get_connection

logger = logging.getLogger("OSMOS_ACTION_REC_REPO")

def insert_llm_action_recommendation(action_dict):
    """Inserts a new LLM action recommendation into the database."""
    query = """
        INSERT INTO llm_action_recommendations (
            entity_id, alert_type, alert_source, alert_level,
            summary_fr, summary_en, risk_explanation_fr, risk_explanation_en,
            priority, recommended_action_fr, recommended_action_en, suggested_channel,
            message_draft_fr, message_draft_en, admin_guidance_fr, admin_guidance_en,
            confidence, status, llm_model, llm_provider, input_context, raw_llm_output
        ) VALUES (
            %(entity_id)s, %(alert_type)s, %(alert_source)s, %(alert_level)s,
            %(summary_fr)s, %(summary_en)s, %(risk_explanation_fr)s, %(risk_explanation_en)s,
            %(priority)s, %(recommended_action_fr)s, %(recommended_action_en)s, %(suggested_channel)s,
            %(message_draft_fr)s, %(message_draft_en)s, %(admin_guidance_fr)s, %(admin_guidance_en)s,
            %(confidence)s, %(status)s, %(llm_model)s, %(llm_provider)s, %(input_context)s, %(raw_llm_output)s
        )
        RETURNING id;
    """
    params = dict(action_dict)
    
    # Defaults
    if "status" not in params:
        params["status"] = "Pending"
        
    # Serialize JSONB fields using psycopg2.extras.Json
    params["input_context"] = psycopg2.extras.Json(params.get("input_context") or {})
    params["raw_llm_output"] = psycopg2.extras.Json(params.get("raw_llm_output") or {})
    
    try:
        with get_cursor() as cur:
            cur.execute(query, params)
            res = cur.fetchone()
            return res['id'] if res else None
    except Exception as e:
        logger.error(f"Failed to insert LLM action recommendation: {e}")
        raise

def get_llm_action_recommendations(status=None, entity_id=None, limit=100):
    """Retrieves LLM action recommendations filtered by status or entity_id."""
    query = """
        SELECT * FROM llm_action_recommendations
        WHERE 1=1
    """
    params = {}
    
    if status:
        query += " AND status = %(status)s"
        params["status"] = status
    if entity_id:
        query += " AND entity_id = %(entity_id)s"
        params["entity_id"] = entity_id
        
    query += " ORDER BY created_at DESC LIMIT %(limit)s"
    params["limit"] = limit
    
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    except Exception as e:
        logger.error(f"Failed to retrieve LLM action recommendations: {e}")
        return []

def update_llm_action_status(action_id, status):
    """Updates the status and updated_at timestamp of a recommendation."""
    query = """
        UPDATE llm_action_recommendations
        SET status = %(status)s, updated_at = NOW()
        WHERE id = %(id)s
        RETURNING id;
    """
    try:
        with get_cursor() as cur:
            cur.execute(query, {"status": status, "id": action_id})
            res = cur.fetchone()
            return res['id'] if res else None
    except Exception as e:
        logger.error(f"Failed to update LLM action status: {e}")
        raise

def get_pending_critical_actions(limit=20):
    """Retrieves pending recommendations with critical or high priority."""
    query = """
        SELECT * FROM llm_action_recommendations
        WHERE status = 'Pending'
          AND (priority = 'Critical' OR priority = 'High' OR alert_level = 'High')
        ORDER BY created_at DESC
        LIMIT %(limit)s;
    """
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query, {"limit": limit})
            return cur.fetchall()
    except Exception as e:
        logger.error(f"Failed to retrieve pending critical actions: {e}")
        return []
