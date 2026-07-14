import pandas as pd
from sqlalchemy import create_engine, text
from database.db import get_connection_string, test_connection

def get_engine():
    return create_engine(get_connection_string())

def is_postgres_available():
    connected, _ = test_connection()
    return connected

def get_database_health():
    """Retrieve high level database health parameters."""
    connected, reason = test_connection()
    if not connected:
        return {
            "status": "Offline",
            "reason": reason,
            "entity_count": 0,
            "event_count": 0,
            "model_count": 0
        }
        
    engine = get_engine()
    with engine.connect() as conn:
        try:
            ent_count = conn.execute(text("SELECT COUNT(*) FROM entities;")).scalar()
            ev_count = conn.execute(text("SELECT COUNT(*) FROM event_history;")).scalar()
            mod_count = conn.execute(text("SELECT COUNT(*) FROM model_registry;")).scalar()
            
            # Fetch last event and prediction dates
            last_ev = conn.execute(text("SELECT MAX(event_date) FROM event_history;")).scalar()
            last_pred = conn.execute(text("SELECT MAX(predicted_at) FROM classification_predictions;")).scalar()
            
            # Format dates to string
            last_ev_str = last_ev.strftime("%Y-%m-%d %H:%M:%S") if last_ev else "N/A"
            last_pred_str = last_pred.strftime("%Y-%m-%d %H:%M:%S") if last_pred else "N/A"
            
            return {
                "status": "Online",
                "database_name": "osmos_db",
                "entity_count": ent_count,
                "event_count": ev_count,
                "model_count": mod_count,
                "last_event_date": last_ev_str,
                "last_prediction_date": last_pred_str
            }
        except Exception as e:
            return {
                "status": "Error",
                "reason": str(e),
                "entity_count": 0,
                "event_count": 0,
                "model_count": 0
            }

def get_table_counts():
    """Retrieve row count and purpose for each PostgreSQL table."""
    tables = [
        ("entities", "Base client and prospect entities data"),
        ("customer_profiles", "PII customer profile demographics"),
        ("digital_twin_snapshots", "Current digital twin snapshot metrics"),
        ("event_history", "Historical customer transaction and interaction logs"),
        ("rfm_es_scores", "Historical versioned RFM-ES calculation results"),
        ("classification_predictions", "Historical dynamic customer lifecycle classification predictions"),
        ("clv_predictions", "Historical customer lifetime value prediction parameters"),
        ("customer_segments", "Historical customer segment/persona assignments"),
        ("model_registry", "Metadata of trained machine learning model artifacts"),
        ("audit_logs", "Platform security and maintenance audit log trail")
    ]
    
    if not is_postgres_available():
        return [{"table_name": t[0], "row_count": 0, "purpose": t[1]} for t in tables]
        
    engine = get_engine()
    results = []
    with engine.connect() as conn:
        for t_name, purpose in tables:
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {t_name};")).scalar()
                results.append({
                    "table_name": t_name,
                    "row_count": count,
                    "purpose": purpose
                })
            except Exception:
                results.append({
                    "table_name": t_name,
                    "row_count": 0,
                    "purpose": purpose
                })
    return results

def get_latest_events(limit=20):
    if not is_postgres_available():
        return pd.DataFrame()
    engine = get_engine()
    query = """
        SELECT event_id, entity_id, event_type, event_date, old_class, new_class, class_changed, old_entity_type, new_entity_type 
        FROM event_history 
        ORDER BY event_date DESC 
        LIMIT :limit;
    """
    return pd.read_sql(text(query), engine, params={"limit": limit})

def get_latest_classification_predictions(limit=20):
    if not is_postgres_available():
        return pd.DataFrame()
    engine = get_engine()
    query = """
        SELECT entity_id, event_id, dynamic_class, confidence AS prediction_confidence, model_name, predicted_at 
        FROM classification_predictions 
        ORDER BY predicted_at DESC 
        LIMIT :limit;
    """
    return pd.read_sql(text(query), engine, params={"limit": limit})

def get_latest_clv_predictions(limit=20):
    if not is_postgres_available():
        return pd.DataFrame()
    engine = get_engine()
    query = """
        SELECT entity_id, event_id, predicted_clv_amount_mad, predicted_clv_score, predicted_clv_segment, clv_method_used, predicted_at 
        FROM clv_predictions 
        ORDER BY predicted_at DESC 
        LIMIT :limit;
    """
    return pd.read_sql(text(query), engine, params={"limit": limit})

def get_latest_rfm_scores(limit=20):
    if not is_postgres_available():
        return pd.DataFrame()
    engine = get_engine()
    query = """
        SELECT entity_id, event_id, rfm_score, rfm_score_raw_1_to_5, calculated_at 
        FROM rfm_es_scores 
        ORDER BY calculated_at DESC 
        LIMIT :limit;
    """
    return pd.read_sql(text(query), engine, params={"limit": limit})

def get_latest_customer_segments(limit=20):
    if not is_postgres_available():
        return pd.DataFrame()
    engine = get_engine()
    query = """
        SELECT entity_id, event_id, customer_segment, customer_persona, segmentation_method, assigned_at 
        FROM customer_segments 
        ORDER BY assigned_at DESC 
        LIMIT :limit;
    """
    return pd.read_sql(text(query), engine, params={"limit": limit})

def get_model_registry():
    if not is_postgres_available():
        return pd.DataFrame()
    engine = get_engine()
    query = "SELECT * FROM model_registry ORDER BY registered_at DESC;"
    return pd.read_sql(text(query), engine)

def get_audit_logs(limit=50):
    if not is_postgres_available():
        return pd.DataFrame()
    engine = get_engine()
    query = "SELECT action_type, entity_id, event_id, details, created_at FROM audit_logs ORDER BY created_at DESC LIMIT :limit;"
    return pd.read_sql(text(query), engine, params={"limit": limit})

# --------------------------------------------------------
# Entity History Explorer Helpers
# --------------------------------------------------------
def get_entity_prediction_history(entity_id):
    if not is_postgres_available():
        return pd.DataFrame()
    engine = get_engine()
    query = """
        SELECT predicted_at, dynamic_class, confidence AS prediction_confidence, model_name 
        FROM classification_predictions 
        WHERE entity_id = :entity_id 
        ORDER BY predicted_at ASC;
    """
    return pd.read_sql(text(query), engine, params={"entity_id": entity_id})

def get_entity_clv_history(entity_id):
    if not is_postgres_available():
        return pd.DataFrame()
    engine = get_engine()
    query = """
        SELECT predicted_at, predicted_clv_amount_mad, predicted_clv_score, predicted_clv_segment, clv_method_used 
        FROM clv_predictions 
        WHERE entity_id = :entity_id 
        ORDER BY predicted_at ASC;
    """
    return pd.read_sql(text(query), engine, params={"entity_id": entity_id})

def get_entity_rfm_history(entity_id):
    if not is_postgres_available():
        return pd.DataFrame()
    engine = get_engine()
    query = """
        SELECT calculated_at, rfm_score, rfm_score_raw_1_to_5 
        FROM rfm_es_scores 
        WHERE entity_id = :entity_id 
        ORDER BY calculated_at ASC;
    """
    return pd.read_sql(text(query), engine, params={"entity_id": entity_id})

def get_entity_segment_history(entity_id):
    if not is_postgres_available():
        return pd.DataFrame()
    engine = get_engine()
    query = """
        SELECT assigned_at, customer_segment, customer_persona, persona_recommended_action 
        FROM customer_segments 
        WHERE entity_id = :entity_id 
        ORDER BY assigned_at ASC;
    """
    return pd.read_sql(text(query), engine, params={"entity_id": entity_id})

def get_entity_event_timeline(entity_id):
    if not is_postgres_available():
        return pd.DataFrame()
    engine = get_engine()
    query = """
        SELECT event_date, event_id, event_type, old_class, new_class, class_changed, prospect_to_client_conversion 
        FROM event_history 
        WHERE entity_id = :entity_id 
        ORDER BY event_date ASC;
    """
    return pd.read_sql(text(query), engine, params={"entity_id": entity_id})
