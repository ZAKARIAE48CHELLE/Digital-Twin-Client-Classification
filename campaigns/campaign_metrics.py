import logging
import pandas as pd
from database.db import get_cursor
from admin.database_metrics import is_postgres_available
from campaigns.campaign_repository import get_campaign_metrics, get_campaign_dispatches, get_campaign_responses

logger = logging.getLogger("OSMOS_CAMPAIGN_METRICS")

def get_campaign_overview_metrics():
    """Computes comprehensive campaign overview metrics including rates."""
    base_counts = get_campaign_metrics()
    total = base_counts.get("total_campaigns", 0)
    dispatched = base_counts.get("simulated_dispatches", 0) + base_counts.get("responded_campaigns", 0)
    responded = base_counts.get("responded_campaigns", 0)
    
    responses = get_campaign_responses()
    purchases = sum(1 for r in responses if r.get("response_type") == "Purchased")
    complaints = sum(1 for r in responses if r.get("response_type") in ["Complained", "Negative Feedback"])
    
    response_rate = (responded / dispatched * 100) if dispatched > 0 else 0.0
    purchase_rate = (purchases / dispatched * 100) if dispatched > 0 else 0.0
    complaint_rate = (complaints / dispatched * 100) if dispatched > 0 else 0.0
    
    return {
        "total_campaigns": total,
        "draft_campaigns": base_counts.get("draft_campaigns", 0),
        "approved_campaigns": base_counts.get("approved_campaigns", 0),
        "simulated_dispatches": base_counts.get("simulated_dispatches", 0),
        "responded_campaigns": responded,
        "total_responses": base_counts.get("total_responses", 0),
        "response_rate_pct": round(response_rate, 1),
        "purchase_rate_pct": round(purchase_rate, 1),
        "complaint_rate_pct": round(complaint_rate, 1)
    }

def get_campaign_response_distribution(days=30):
    """Returns distribution of campaign responses."""
    responses = get_campaign_responses()
    if not responses:
        return pd.DataFrame(columns=["response_type", "count"])
        
    df = pd.DataFrame(responses)
    if "response_type" in df.columns:
        counts = df["response_type"].value_counts().reset_index()
        counts.columns = ["response_type", "count"]
        return counts
    return pd.DataFrame(columns=["response_type", "count"])

def get_campaign_success_by_type(days=30):
    """Returns campaign dispatch count by campaign type."""
    dispatches = get_campaign_dispatches(limit=500)
    if not dispatches:
        return pd.DataFrame(columns=["campaign_type", "count"])
        
    df = pd.DataFrame(dispatches)
    if "campaign_type" in df.columns:
        counts = df["campaign_type"].value_counts().reset_index()
        counts.columns = ["campaign_type", "count"]
        return counts
    return pd.DataFrame(columns=["campaign_type", "count"])

def get_campaign_success_by_channel(days=30):
    """Returns campaign dispatch count by channel."""
    dispatches = get_campaign_dispatches(limit=500)
    if not dispatches:
        return pd.DataFrame(columns=["campaign_channel", "count"])
        
    df = pd.DataFrame(dispatches)
    if "campaign_channel" in df.columns:
        counts = df["campaign_channel"].value_counts().reset_index()
        counts.columns = ["campaign_channel", "count"]
        return counts
    return pd.DataFrame(columns=["campaign_channel", "count"])

def get_entity_campaign_history(entity_id):
    """Retrieves all campaigns and responses for a specific entity."""
    dispatches = get_campaign_dispatches(entity_id=entity_id, limit=50)
    responses = get_campaign_responses(entity_id=entity_id)
    return {
        "dispatches": pd.DataFrame(dispatches) if dispatches else pd.DataFrame(),
        "responses": pd.DataFrame(responses) if responses else pd.DataFrame()
    }

def get_campaign_impact_on_clv(campaign_id):
    """Retrieves before/after CLV impact for entity in campaign."""
    if not is_postgres_available() or not campaign_id:
        return {"before_clv": 0.0, "after_clv": 0.0, "clv_lift": 0.0}
        
    query = """
        SELECT 
            c.campaign_id, c.entity_id,
            r.response_type, r.simulated_at,
            eh.old_clv_amount_mad, eh.new_clv_amount_mad
        FROM campaign_dispatches c
        JOIN campaign_responses r ON c.campaign_id = r.campaign_id
        LEFT JOIN event_history eh ON r.response_event_id = eh.event_id
        WHERE c.campaign_id = %s;
    """
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query, (campaign_id,))
            res = cur.fetchone()
            if res and res.get("old_clv_amount_mad") is not None:
                old_clv = float(res.get("old_clv_amount_mad") or 0.0)
                new_clv = float(res.get("new_clv_amount_mad") or 0.0)
                return {
                    "before_clv": old_clv,
                    "after_clv": new_clv,
                    "clv_lift": round(new_clv - old_clv, 2)
                }
    except Exception as e:
        logger.error(f"Error computing campaign CLV impact: {e}")
        
    return {"before_clv": 0.0, "after_clv": 0.0, "clv_lift": 0.0}

def get_campaign_impact_on_segment(entity_id):
    """Retrieves current vs previous segment/persona after campaign activity."""
    history = get_entity_campaign_history(entity_id)
    return {
        "has_campaign_activity": not history["dispatches"].empty,
        "history": history
    }
