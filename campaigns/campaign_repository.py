import logging
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from database.db import get_cursor
from admin.database_metrics import is_postgres_available

logger = logging.getLogger("OSMOS_CAMPAIGN_REPOSITORY")

def create_campaign_dispatch(campaign_dict):
    """Inserts a new campaign dispatch draft in PostgreSQL."""
    if not is_postgres_available():
        logger.warning("PostgreSQL unavailable; cannot create campaign dispatch in Excel mode.")
        return None
        
    query = """
        INSERT INTO campaign_dispatches (
            recommendation_id, entity_id, campaign_type, campaign_channel,
            campaign_title, campaign_message_fr, campaign_message_en,
            action_source, priority, status, created_by, scheduled_at, dispatched_at, created_at, updated_at
        ) VALUES (
            %(recommendation_id)s, %(entity_id)s, %(campaign_type)s, %(campaign_channel)s,
            %(campaign_title)s, %(campaign_message_fr)s, %(campaign_message_en)s,
            %(action_source)s, %(priority)s, %(status)s, %(created_by)s, %(scheduled_at)s, %(dispatched_at)s, NOW(), NOW()
        ) RETURNING campaign_id;
    """
    params = {
        "recommendation_id": campaign_dict.get("recommendation_id"),
        "entity_id": campaign_dict.get("entity_id"),
        "campaign_type": campaign_dict.get("campaign_type", "Marketing Campaign"),
        "campaign_channel": campaign_dict.get("campaign_channel", "Email"),
        "campaign_title": campaign_dict.get("campaign_title", "Campaign Outreach"),
        "campaign_message_fr": campaign_dict.get("campaign_message_fr"),
        "campaign_message_en": campaign_dict.get("campaign_message_en"),
        "action_source": campaign_dict.get("action_source", "Manual"),
        "priority": campaign_dict.get("priority", "Medium"),
        "status": campaign_dict.get("status", "Draft"),
        "created_by": campaign_dict.get("created_by", "admin"),
        "scheduled_at": campaign_dict.get("scheduled_at"),
        "dispatched_at": campaign_dict.get("dispatched_at")
    }
    
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(query, params)
            res = cur.fetchone()
            return res['campaign_id'] if res else None
    except Exception as e:
        logger.error(f"Failed to create campaign dispatch: {e}")
        return None

def get_campaign_dispatches(status=None, entity_id=None, limit=100):
    """Retrieves campaign dispatches filtered by status or entity_id."""
    if not is_postgres_available():
        return []
        
    conditions = []
    params = []
    
    if status:
        conditions.append("status = %s")
        params.append(status)
    if entity_id:
        conditions.append("entity_id = %s")
        params.append(entity_id)
        
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
        SELECT * FROM campaign_dispatches
        {where_clause}
        ORDER BY created_at DESC
        LIMIT %s;
    """
    params.append(limit)
    
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query, tuple(params))
            return cur.fetchall() or []
    except Exception as e:
        logger.error(f"Failed to fetch campaign dispatches: {e}")
        return []

def get_campaign_by_id(campaign_id):
    """Gets a single campaign dispatch by ID."""
    if not is_postgres_available() or not campaign_id:
        return None
        
    query = "SELECT * FROM campaign_dispatches WHERE campaign_id = %s;"
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query, (campaign_id,))
            return cur.fetchone()
    except Exception as e:
        logger.error(f"Failed to fetch campaign {campaign_id}: {e}")
        return None

def update_campaign_status(campaign_id, status):
    """Updates status and dispatched_at/updated_at timestamp for a campaign."""
    if not is_postgres_available() or not campaign_id:
        return False
        
    if status in ['Simulated Dispatch', 'Dispatched']:
        query = """
            UPDATE campaign_dispatches
            SET status = %s, dispatched_at = NOW(), updated_at = NOW()
            WHERE campaign_id = %s;
        """
    else:
        query = """
            UPDATE campaign_dispatches
            SET status = %s, updated_at = NOW()
            WHERE campaign_id = %s;
        """
        
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(query, (status, campaign_id))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to update campaign {campaign_id} status to {status}: {e}")
        return False

def insert_campaign_response(response_dict):
    """Inserts a simulated campaign response in PostgreSQL."""
    if not is_postgres_available():
        return None
        
    query = """
        INSERT INTO campaign_responses (
            campaign_id, entity_id, response_type, response_score,
            response_event_id, response_details, simulated_at
        ) VALUES (
            %(campaign_id)s, %(entity_id)s, %(response_type)s, %(response_score)s,
            %(response_event_id)s, %(response_details)s, NOW()
        ) RETURNING response_id;
    """
    details = response_dict.get("response_details", {})
    params = {
        "campaign_id": response_dict.get("campaign_id"),
        "entity_id": response_dict.get("entity_id"),
        "response_type": response_dict.get("response_type"),
        "response_score": response_dict.get("response_score", 0.5),
        "response_event_id": response_dict.get("response_event_id"),
        "response_details": Json(details) if isinstance(details, dict) else details
    }
    
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(query, params)
            res = cur.fetchone()
            return res['response_id'] if res else None
    except Exception as e:
        logger.error(f"Failed to insert campaign response: {e}")
        return None

def get_campaign_responses(campaign_id=None, entity_id=None):
    """Retrieves campaign responses filtered by campaign_id or entity_id."""
    if not is_postgres_available():
        return []
        
    conditions = []
    params = []
    
    if campaign_id:
        conditions.append("campaign_id = %s")
        params.append(campaign_id)
    if entity_id:
        conditions.append("entity_id = %s")
        params.append(entity_id)
        
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
        SELECT * FROM campaign_responses
        {where_clause}
        ORDER BY simulated_at DESC;
    """
    
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query, tuple(params))
            return cur.fetchall() or []
    except Exception as e:
        logger.error(f"Failed to fetch campaign responses: {e}")
        return []

def get_pending_campaigns(limit=50):
    """Gets draft or approved campaigns waiting for dispatch simulation."""
    if not is_postgres_available():
        return []
        
    query = """
        SELECT * FROM campaign_dispatches
        WHERE status IN ('Draft', 'Approved')
        ORDER BY created_at DESC
        LIMIT %s;
    """
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query, (limit,))
            return cur.fetchall() or []
    except Exception as e:
        logger.error(f"Failed to fetch pending campaigns: {e}")
        return []

def get_campaign_metrics():
    """Calculates high-level campaign summary counts."""
    if not is_postgres_available():
        return {
            "total_campaigns": 0,
            "draft_campaigns": 0,
            "approved_campaigns": 0,
            "simulated_dispatches": 0,
            "responded_campaigns": 0,
            "total_responses": 0
        }
        
    query = """
        SELECT 
            COUNT(*) as total_campaigns,
            COUNT(*) FILTER (WHERE status = 'Draft') as draft_campaigns,
            COUNT(*) FILTER (WHERE status = 'Approved') as approved_campaigns,
            COUNT(*) FILTER (WHERE status = 'Simulated Dispatch') as simulated_dispatches,
            COUNT(*) FILTER (WHERE status = 'Responded') as responded_campaigns
        FROM campaign_dispatches;
    """
    resp_query = "SELECT COUNT(*) as total_responses FROM campaign_responses;"
    
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query)
            counts = cur.fetchone() or {}
            cur.execute(resp_query)
            resp_counts = cur.fetchone() or {}
            
            return {
                "total_campaigns": counts.get("total_campaigns", 0),
                "draft_campaigns": counts.get("draft_campaigns", 0),
                "approved_campaigns": counts.get("approved_campaigns", 0),
                "simulated_dispatches": counts.get("simulated_dispatches", 0),
                "responded_campaigns": counts.get("responded_campaigns", 0),
                "total_responses": resp_counts.get("total_responses", 0)
            }
    except Exception as e:
        logger.error(f"Failed to compute campaign metrics: {e}")
        return {
            "total_campaigns": 0,
            "draft_campaigns": 0,
            "approved_campaigns": 0,
            "simulated_dispatches": 0,
            "responded_campaigns": 0,
            "total_responses": 0
        }
