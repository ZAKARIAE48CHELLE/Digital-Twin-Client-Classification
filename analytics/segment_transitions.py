import pandas as pd
from sqlalchemy import text
from database.db import get_connection_string
from admin.database_metrics import is_postgres_available

def get_engine():
    from sqlalchemy import create_engine
    return create_engine(get_connection_string())

def classify_transition(prev_seg, latest_seg, prev_pers, latest_pers):
    """Classify the transition between previous and latest segments/personas."""
    if prev_seg == latest_seg:
        return "Stable"
    
    if prev_seg is None or prev_seg == "None":
        return "New Assignment"
        
    # Standard segment names in OSMOS:
    # - Prospect
    # - New Customers (New Explorer)
    # - High-Value Loyalists (Premium Loyalist)
    # - At-Risk Premium Clients (Silent VIP at Risk)
    # - Growth Potential Clients (Emerging Loyalist)
    # - Price-Sensitive Occasional Buyers (Deal Seeker)
    # - Complaint-Driven Risk Clients (Frustrated Client)
    # - Dormant Low-Value Clients (Sleeping Client)
    # - Social Advocates (Brand Advocate)
    # - Standard Active Clients (Regular Buyer)
    
    if latest_seg == "Dormant Low-Value Clients" or latest_pers == "Sleeping Client":
        return "Downgrade"
        
    if prev_seg == "Prospect" and latest_seg != "Prospect":
        return "New Assignment"
        
    # Upgrades
    if prev_seg == "New Customers" and latest_seg in ["Growth Potential Clients", "High-Value Loyalists", "Standard Active Clients", "Social Advocates"]:
        return "Upgrade"
    if prev_seg == "Growth Potential Clients" and latest_seg == "High-Value Loyalists":
        return "Upgrade"
    if latest_seg in ["High-Value Loyalists", "Social Advocates"] and prev_seg not in ["High-Value Loyalists", "Social Advocates"]:
        return "Upgrade"
        
    # Risk Increases
    if latest_seg in ["At-Risk Premium Clients", "Complaint-Driven Risk Clients"] or latest_pers in ["Silent VIP at Risk", "Frustrated Client"]:
        return "Risk Increase"
        
    # Downgrades
    if latest_seg in ["Price-Sensitive Occasional Buyers", "Dormant Low-Value Clients"] and prev_seg in ["High-Value Loyalists", "Growth Potential Clients", "Standard Active Clients", "Social Advocates"]:
        return "Downgrade"
        
    return "Stable"

def get_segment_transitions(days=90):
    """Get list of detailed customer segment transitions in the specified window."""
    if not is_postgres_available():
        return pd.DataFrame()
        
    engine = get_engine()
    query = """
        WITH ranked_segments AS (
            SELECT 
                entity_id,
                customer_segment,
                customer_persona,
                assigned_at,
                LAG(customer_segment) OVER (PARTITION BY entity_id ORDER BY assigned_at ASC) as prev_segment,
                LAG(customer_persona) OVER (PARTITION BY entity_id ORDER BY assigned_at ASC) as prev_persona,
                ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY assigned_at DESC) as rn
            FROM customer_segments
        )
        SELECT 
            entity_id,
            prev_segment as previous_segment,
            customer_segment as latest_segment,
            prev_persona as previous_persona,
            customer_persona as latest_persona,
            assigned_at as transition_date
        FROM ranked_segments
        WHERE rn = 1 
          AND prev_segment IS NOT NULL 
          AND assigned_at >= NOW() - CAST(:days_interval AS INTERVAL);
    """
    try:
        days_str = f"{days} days"
        df = pd.read_sql(text(query), engine, params={"days_interval": days_str})
        if df.empty:
            return pd.DataFrame(columns=[
                "entity_id", "previous_segment", "latest_segment",
                "previous_persona", "latest_persona", "transition_date", "transition_type"
            ])
            
        transitions = []
        for _, row in df.iterrows():
            t_type = classify_transition(
                row["previous_segment"], row["latest_segment"],
                row["previous_persona"], row["latest_persona"]
            )
            transitions.append(t_type)
            
        df["transition_type"] = transitions
        return df
    except Exception:
        return pd.DataFrame()

def get_segment_transition_matrix(days=90):
    """Retrieve transitions formatted as a transition matrix (previous_segment x latest_segment)."""
    df = get_segment_transitions(days)
    if df.empty:
        return pd.DataFrame()
        
    # Use pandas crosstab to build the pivot/crosstab matrix
    matrix = pd.crosstab(
        df["previous_segment"],
        df["latest_segment"]
    )
    return matrix

def get_entity_segment_journey(entity_id):
    """Get the customer segment journey/history for a single entity."""
    if not is_postgres_available():
        return pd.DataFrame()
        
    engine = get_engine()
    query = """
        SELECT 
            customer_segment,
            customer_persona,
            assigned_at
        FROM customer_segments
        WHERE entity_id = :entity_id
        ORDER BY assigned_at ASC;
    """
    try:
        return pd.read_sql(text(query), engine, params={"entity_id": entity_id})
    except Exception:
        return pd.DataFrame()
