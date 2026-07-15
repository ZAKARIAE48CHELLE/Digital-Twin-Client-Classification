import pandas as pd
import numpy as np
from sqlalchemy import text
from database.db import get_connection_string
from admin.database_metrics import is_postgres_available

def get_engine():
    from sqlalchemy import create_engine
    return create_engine(get_connection_string())

def classify_clv_trend(old_value, new_value):
    """Classify CLV drop trend and return alert level and recommended action."""
    if old_value is None or new_value is None or old_value <= 0:
        return "None", "Monitor customer activity"
        
    pct_drop = (old_value - new_value) / old_value
    
    if pct_drop >= 0.35:
        return "High", "Trigger retention campaign"
    elif pct_drop >= 0.20:
        return "Medium", "Send personalized offer"
    elif pct_drop >= 0.10:
        return "Low", "Monitor customer activity"
    else:
        return "None", "Monitor customer activity"

def get_clv_trend_alerts(days=30, drop_threshold=0.20):
    """Retrieve all entities with a CLV drop within specified days window."""
    if not is_postgres_available():
        return pd.DataFrame()
        
    engine = get_engine()
    # SQL query utilizing window functions to find current and previous CLV
    query = """
        WITH ranked_predictions AS (
            SELECT 
                entity_id,
                predicted_clv_amount_mad,
                predicted_clv_segment,
                predicted_at,
                LAG(predicted_clv_amount_mad) OVER (PARTITION BY entity_id ORDER BY predicted_at ASC) as prev_clv_amount,
                ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY predicted_at DESC) as rn
            FROM clv_predictions
        )
        SELECT 
            entity_id,
            prev_clv_amount as previous_clv_amount,
            predicted_clv_amount_mad as latest_clv_amount,
            predicted_clv_segment as latest_clv_segment,
            predicted_at as detected_at
        FROM ranked_predictions
        WHERE rn = 1 
          AND prev_clv_amount IS NOT NULL 
          AND predicted_at >= NOW() - CAST(:days_interval AS INTERVAL);
    """
    
    try:
        days_str = f"{days} days"
        df = pd.read_sql(text(query), engine, params={"days_interval": days_str})
        if df.empty:
            return pd.DataFrame(columns=[
                "entity_id", "previous_clv_amount", "latest_clv_amount",
                "clv_change_amount", "clv_change_percent", "alert_level",
                "latest_clv_segment", "recommended_action", "detected_at"
            ])
            
        # Calculate changes and alert details
        df["previous_clv_amount"] = df["previous_clv_amount"].astype(float)
        df["latest_clv_amount"] = df["latest_clv_amount"].astype(float)
        df["clv_change_amount"] = df["latest_clv_amount"] - df["previous_clv_amount"]
        df["clv_change_percent"] = (df["clv_change_amount"] / df["previous_clv_amount"])
        
        alerts = []
        for _, row in df.iterrows():
            old_val = row["previous_clv_amount"]
            new_val = row["latest_clv_amount"]
            level, action = classify_clv_trend(old_val, new_val)
            alerts.append({"alert_level": level, "recommended_action": action})
            
        alerts_df = pd.DataFrame(alerts)
        df["alert_level"] = alerts_df["alert_level"]
        df["recommended_action"] = alerts_df["recommended_action"]
        
        # Filter for drops only (where clv_change_percent is negative, representing a decrease)
        # Drop threshold is passed as a positive number (e.g. 0.20 = 20% drop),
        # so change percent must be <= -drop_threshold.
        df = df[df["clv_change_percent"] <= -drop_threshold]
        
        # Format columns order
        order = [
            "entity_id", "previous_clv_amount", "latest_clv_amount",
            "clv_change_amount", "clv_change_percent", "alert_level",
            "latest_clv_segment", "recommended_action", "detected_at"
        ]
        return df[order].sort_values(by="clv_change_percent", ascending=True)
    except Exception:
        return pd.DataFrame()

def get_entity_clv_trend(entity_id):
    """Get the CLV trend for a single entity."""
    if not is_postgres_available():
        return pd.DataFrame()
        
    engine = get_engine()
    query = """
        SELECT 
            predicted_clv_amount_mad as clv_amount,
            predicted_clv_score as clv_score,
            predicted_clv_segment as clv_segment,
            predicted_at
        FROM clv_predictions
        WHERE entity_id = :entity_id
        ORDER BY predicted_at ASC;
    """
    try:
        return pd.read_sql(text(query), engine, params={"entity_id": entity_id})
    except Exception:
        return pd.DataFrame()
