import pandas as pd
import json
import logging
from sqlalchemy import create_engine
from database.db import get_connection, get_cursor, get_connection_string
from database.repositories import (
    upsert_entity,
    upsert_customer_profile,
    upsert_digital_twin_snapshot,
    insert_rfm_es_score,
    get_latest_rfm_es_score,
    insert_classification_prediction,
    get_latest_classification_prediction,
    insert_clv_prediction,
    get_latest_clv_prediction,
    insert_customer_segment,
    get_latest_customer_segment,
    insert_event_history,
    get_event_history
)

logger = logging.getLogger("OSMOS_POSTGRES_STORAGE")

def clean_dict_values(d):
    """Ensure all numpy/pandas types in dictionary are native python types."""
    import numpy as np
    clean = {}
    for k, v in d.items():
        if isinstance(v, bool):
            # IMPORTANT: bool must be checked BEFORE int because in Python
            # bool is a subclass of int (isinstance(True, int) == True).
            # Without this ordering, True/False would be cast to 1/0,
            # causing PostgreSQL BOOLEAN column type mismatches.
            clean[k] = v
        elif v is None or (not isinstance(v, bool) and pd.isna(v)):
            clean[k] = None
        elif isinstance(v, (np.integer, int)):
            clean[k] = int(v)
        elif isinstance(v, (np.floating, float)):
            clean[k] = float(v)
        elif isinstance(v, (np.ndarray, list)):
            clean[k] = list(v)
        elif isinstance(v, dict):
            clean[k] = clean_dict_values(v)
        else:
            clean[k] = str(v)
    return clean

# --------------------------------------------------------
# 1. PostgreSQL Load Data
# --------------------------------------------------------
def load_postgres_data():
    engine = create_engine(get_connection_string())
    
    query = """
    WITH latest_rfm AS (
        SELECT DISTINCT ON (entity_id) *
        FROM rfm_es_scores
        ORDER BY entity_id, calculated_at DESC
    ),
    latest_classification AS (
        SELECT DISTINCT ON (entity_id) *
        FROM classification_predictions
        ORDER BY entity_id, predicted_at DESC
    ),
    latest_clv AS (
        SELECT DISTINCT ON (entity_id) *
        FROM clv_predictions
        ORDER BY entity_id, predicted_at DESC
    ),
    latest_segment AS (
        SELECT DISTINCT ON (entity_id) *
        FROM customer_segments
        ORDER BY entity_id, assigned_at DESC
    )
    SELECT 
        e.entity_id,
        e.entity_type,
        e.original_entity_type,
        e.created_at,
        e.converted_at,
        e.conversion_event_id,
        e.completed_client_profile,
        e.region,
        e.source_channel,
        e.segment,
        e.persona,
        e.age_group,
        e.preferred_device,
        e.preferred_category,
        e.marketing_consent,
        e.price_sensitivity,
        e.income_power_score,
        e.initial_interest_score,
        e.basic_profile_score,
        
        p.age,
        p.sex,
        p.email,
        p.customer_type,
        p.household_size,
        p.phone_number,
        p.company_name,
        p.job_title,
        p.city,
        p.address,
        
        s.snapshot_date,
        s.recency_days,
        s.visits_30d,
        s.product_views_30d,
        s.cart_additions_30d,
        s.purchases_90d,
        s.total_spent_90d_mad,
        s.avg_order_value_mad,
        s.email_open_rate,
        s.email_click_rate,
        s.complaint_count_90d,
        s.review_score_avg,
        s.social_mentions_30d,
        s.social_sentiment_avg,
        s.conversion_probability,
        s.churn_risk_score,
        r.rfm_score,
        s.behavioral_engagement_score,
        s.predictive_value_score,
        s.decision_priority_score,
        
        r.r_raw AS "R_raw",
        r.f_raw AS "F_raw",
        r.m_raw AS "M_raw",
        r.e_raw AS "E_raw",
        r.s_raw AS "S_raw",
        r.rfm_recency_score,
        r.rfm_frequency_score,
        r.rfm_monetary_score,
        r.rfm_engagement_score,
        r.rfm_sentiment_score,
        r.rfm_score_raw_1_to_5,
        r.ahp_weight_r AS "ahp_weight_R",
        r.ahp_weight_f AS "ahp_weight_F",
        r.ahp_weight_m AS "ahp_weight_M",
        r.ahp_weight_e AS "ahp_weight_E",
        r.ahp_weight_s AS "ahp_weight_S",
        r.ahp_group_cr AS "ahp_group_CR",
        r.ahp_group_ci AS "ahp_group_CI",
        r.ahp_expert_count,
        
        c.dynamic_class,
        c.confidence AS "prediction_confidence",
        c.model_name AS "classification_model_name",
        c.top_3_probs AS "classification_top_3",
        
        v.predicted_clv_amount_mad,
        v.predicted_clv_score,
        v.predicted_clv_segment,
        v.clv_model_name,
        v.clv_segment_model_name,
        v.clv_method_used,
        v.ml_predicted_clv_amount_mad,
        v.math_clv_amount_mad,
        v.clv_segment_prediction_source,
        v.clv_segment_confidence,
        v.clv_segment_top_3,
        v.predicted_at AS "clv_last_updated",
        
        g.customer_segment,
        g.customer_persona,
        g.persona_description,
        g.persona_recommended_action,
        g.persona_recommended_action AS "recommended_action",
        g.segmentation_method,
        g.ml_cluster_id,
        g.ml_cluster_label,
        g.cluster_persona,
        g.assigned_at AS "segmentation_last_updated"
    FROM entities e
    LEFT JOIN customer_profiles p ON e.entity_id = p.entity_id
    LEFT JOIN digital_twin_snapshots s ON e.entity_id = s.entity_id
    LEFT JOIN latest_rfm r ON e.entity_id = r.entity_id
    LEFT JOIN latest_classification c ON e.entity_id = c.entity_id
    LEFT JOIN latest_clv v ON e.entity_id = v.entity_id
    LEFT JOIN latest_segment g ON e.entity_id = g.entity_id;
    """
    
    df = pd.read_sql(query, engine)
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    # Safely parse JSON columns
    for col in ["classification_top_3", "clv_segment_top_3"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
            
    # Standardize columns to match Excel Digital_Twins exactly
    excel_cols = [
        "entity_id", "entity_type", "original_entity_type", "snapshot_date", "created_at", "converted_at", "conversion_event_id", "completed_client_profile",
        "recency_days", "visits_30d", "product_views_30d", "cart_additions_30d", "purchases_90d", "total_spent_90d_mad", "avg_order_value_mad",
        "email_open_rate", "email_click_rate", "complaint_count_90d", "review_score_avg", "social_mentions_30d", "social_sentiment_avg",
        "basic_profile_score", "behavioral_engagement_score", "predictive_value_score", "decision_priority_score", "conversion_probability", "churn_risk_score",
        "R_raw", "F_raw", "M_raw", "E_raw", "S_raw",
        "rfm_recency_score", "rfm_frequency_score", "rfm_monetary_score", "rfm_engagement_score", "rfm_sentiment_score",
        "rfm_score_raw_1_to_5", "rfm_score",
        "ahp_weight_R", "ahp_weight_F", "ahp_weight_M", "ahp_weight_E", "ahp_weight_S",
        "ahp_group_CR", "ahp_group_CI", "ahp_expert_count",
        "dynamic_class", "prediction_confidence", "classification_model_name", "classification_top_3",
        "predicted_clv_amount_mad", "predicted_clv_score", "predicted_clv_segment",
        "clv_model_name", "clv_segment_model_name", "clv_method_used",
        "ml_predicted_clv_amount_mad", "math_clv_amount_mad",
        "clv_segment_prediction_source", "clv_segment_confidence", "clv_segment_top_3", "clv_last_updated",
        "customer_segment", "customer_persona", "persona_description", "persona_recommended_action", "recommended_action",
        "segmentation_method", "ml_cluster_id", "ml_cluster_label", "cluster_persona", "segmentation_last_updated",
        "age", "sex", "email", "customer_type", "household_size", "phone_number", "company_name", "job_title", "city", "address",
        "region", "source_channel", "segment", "persona", "age_group", "preferred_device", "preferred_category", "marketing_consent",
        "price_sensitivity", "income_power_score", "initial_interest_score"
    ]
    
    # Copy profile duplicate columns if they exist in excel cols
    for col in ["price_sensitivity", "income_power_score", "marketing_consent"]:
        for suffix in ["_profile", "_profile_profile"]:
            col_suf = f"{col}{suffix}"
            if col_suf not in df.columns and col in df.columns:
                df[col_suf] = df[col]
                
    for col in excel_cols:
        if col not in df.columns:
            df[col] = None
            
    df = df.loc[:, ~df.columns.duplicated()]
    
    # Re-fetch event history log
    history_list = get_event_history()
    history_df = pd.DataFrame(history_list) if history_list else pd.DataFrame(columns=[
        "event_id", "entity_id", "event_type", "event_date", "old_class", "new_class",
        "class_changed", "old_entity_type", "new_entity_type", "prospect_to_client_conversion",
        "completed_client_profile", "changed_variables", "before_values", "after_values"
    ])
    
    return df, history_df

# --------------------------------------------------------
# 2. PostgreSQL Save Data / Individual Updates
# --------------------------------------------------------
def save_postgres_data(df, history_df=None):
    """Iterate and upsert every row in DataFrame to PostgreSQL database."""
    for idx, row in df.iterrows():
        entity_id = row.get("entity_id")
        if not entity_id or pd.isna(entity_id):
            continue
            
        # Convert row object to clean dictionary
        row_dict = clean_dict_values(row.to_dict())
        
        # 1. Core entity core
        entity_data = {
            "entity_id": entity_id,
            "entity_type": row_dict.get("entity_type"),
            "original_entity_type": row_dict.get("original_entity_type"),
            "created_at": row_dict.get("created_at"),
            "converted_at": row_dict.get("converted_at"),
            "conversion_event_id": row_dict.get("conversion_event_id"),
            "completed_client_profile": row_dict.get("completed_client_profile"),
            "region": row_dict.get("region"),
            "source_channel": row_dict.get("source_channel"),
            "segment": row_dict.get("segment"),
            "persona": row_dict.get("persona"),
            "age_group": row_dict.get("age_group"),
            "preferred_device": row_dict.get("preferred_device"),
            "preferred_category": row_dict.get("preferred_category"),
            "marketing_consent": row_dict.get("marketing_consent"),
            "price_sensitivity": row_dict.get("price_sensitivity"),
            "income_power_score": row_dict.get("income_power_score"),
            "initial_interest_score": row_dict.get("initial_interest_score"),
            "basic_profile_score": row_dict.get("basic_profile_score", 0.5)
        }
        upsert_entity(entity_data)
        
        # 2. Demographic customer profiles
        profile_data = {
            "entity_id": entity_id,
            "age": row_dict.get("age"),
            "sex": row_dict.get("sex"),
            "email": row_dict.get("email"),
            "customer_type": row_dict.get("customer_type"),
            "household_size": row_dict.get("household_size"),
            "phone_number": row_dict.get("phone_number"),
            "company_name": row_dict.get("company_name"),
            "job_title": row_dict.get("job_title"),
            "city": row_dict.get("city"),
            "address": row_dict.get("address")
        }
        has_profile = any(profile_data[k] is not None for k in profile_data if k != "entity_id")
        if has_profile:
            upsert_customer_profile(profile_data)
            
        # 3. Digital Twin snapshot values
        snapshot_data = {
            "entity_id": entity_id,
            "snapshot_date": row_dict.get("snapshot_date"),
            "recency_days": row_dict.get("recency_days"),
            "visits_30d": row_dict.get("visits_30d"),
            "product_views_30d": row_dict.get("product_views_30d"),
            "cart_additions_30d": row_dict.get("cart_additions_30d"),
            "purchases_90d": row_dict.get("purchases_90d"),
            "total_spent_90d_mad": row_dict.get("total_spent_90d_mad"),
            "avg_order_value_mad": row_dict.get("avg_order_value_mad"),
            "email_open_rate": row_dict.get("email_open_rate"),
            "email_click_rate": row_dict.get("email_click_rate"),
            "complaint_count_90d": row_dict.get("complaint_count_90d"),
            "review_score_avg": row_dict.get("review_score_avg"),
            "social_mentions_30d": row_dict.get("social_mentions_30d"),
            "social_sentiment_avg": row_dict.get("social_sentiment_avg"),
            "conversion_probability": row_dict.get("conversion_probability"),
            "churn_risk_score": row_dict.get("churn_risk_score"),
            "rfm_score": row_dict.get("rfm_score"),
            "behavioral_engagement_score": row_dict.get("behavioral_engagement_score"),
            "predictive_value_score": row_dict.get("predictive_value_score"),
            "decision_priority_score": row_dict.get("decision_priority_score")
        }
        upsert_digital_twin_snapshot(snapshot_data)
        
        # 4. Save RFM score with duplication guard
        save_postgres_rfm_score(entity_id, row_dict)
        
        # 5. Save Classification prediction with duplication guard
        save_postgres_classification_prediction(entity_id, row_dict)
        
        # 6. Save CLV prediction with duplication guard
        save_postgres_clv_prediction(entity_id, row_dict)
        
        # 7. Save Customer segment with duplication guard
        save_postgres_customer_segment(entity_id, row_dict)
    if history_df is not None:
        for idx, row in history_df.iterrows():
            event_id = row.get("event_id")
            if not event_id or pd.isna(event_id):
                continue
            event_dict = clean_dict_values(row.to_dict())
            save_postgres_event(event_dict)
            
    return True, None

# --------------------------------------------------------
# 3. PostgreSQL Specific Persistence / Duplication Guards
# --------------------------------------------------------
def save_postgres_event(event_dict):
    clean_ev = clean_dict_values(event_dict)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM event_history WHERE event_id = %s;", (clean_ev["event_id"],))
        exists = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
        
    if not exists:
        return insert_event_history(clean_ev)
    return None


def save_postgres_rfm_score(entity_id, rfm_dict, event_id=None):
    clean_rfm = clean_dict_values(rfm_dict)
    if clean_rfm.get("rfm_score") is None:
        return None
        
    latest = get_latest_rfm_es_score(entity_id)
    if event_id or not latest or abs(float(latest["rfm_score"]) - float(clean_rfm["rfm_score"])) > 0.0001:
        rfm_data = {
            "entity_id": entity_id,
            "event_id": event_id,
            "R_raw": clean_rfm.get("R_raw"),
            "F_raw": clean_rfm.get("F_raw"),
            "M_raw": clean_rfm.get("M_raw"),
            "E_raw": clean_rfm.get("E_raw"),
            "S_raw": clean_rfm.get("S_raw"),
            "rfm_recency_score": clean_rfm.get("rfm_recency_score"),
            "rfm_frequency_score": clean_rfm.get("rfm_frequency_score"),
            "rfm_monetary_score": clean_rfm.get("rfm_monetary_score"),
            "rfm_engagement_score": clean_rfm.get("rfm_engagement_score"),
            "rfm_sentiment_score": clean_rfm.get("rfm_sentiment_score"),
            "rfm_score_raw_1_to_5": clean_rfm.get("rfm_score_raw_1_to_5"),
            "rfm_score": clean_rfm.get("rfm_score"),
            "ahp_weight_R": clean_rfm.get("ahp_weight_R"),
            "ahp_weight_F": clean_rfm.get("ahp_weight_F"),
            "ahp_weight_M": clean_rfm.get("ahp_weight_M"),
            "ahp_weight_E": clean_rfm.get("ahp_weight_E"),
            "ahp_weight_S": clean_rfm.get("ahp_weight_S"),
            "ahp_group_CR": clean_rfm.get("ahp_group_CR"),
            "ahp_group_CI": clean_rfm.get("ahp_group_CI"),
            "ahp_expert_count": clean_rfm.get("ahp_expert_count")
        }
        return insert_rfm_es_score(rfm_data)
    return None

def save_postgres_classification_prediction(entity_id, prediction_dict, event_id=None):
    clean_pred = clean_dict_values(prediction_dict)
    dyn_class = clean_pred.get("dynamic_class")
    if not dyn_class:
        return None
        
    latest = get_latest_classification_prediction(entity_id)
    # Check if prediction value changed
    if event_id or not latest or latest["dynamic_class"] != dyn_class:
        class_data = {
            "entity_id": entity_id,
            "event_id": event_id,
            "dynamic_class": dyn_class,
            "confidence": clean_pred.get("prediction_confidence", 1.0),
            "top_3_probs": clean_pred.get("classification_top_3"),
            "model_name": clean_pred.get("classification_model_name", "Best Classification Model"),
            "model_version": "1.0",
            "model_registry_id": None
        }
        return insert_classification_prediction(class_data)
    return None

def save_postgres_clv_prediction(entity_id, clv_dict, event_id=None):
    clean_clv = clean_dict_values(clv_dict)
    clv_amount = clean_clv.get("predicted_clv_amount_mad")
    if clv_amount is None:
        return None
        
    latest = get_latest_clv_prediction(entity_id)
    if event_id or not latest or abs(float(latest["predicted_clv_amount_mad"]) - float(clv_amount)) > 0.01:
        clv_data = {
            "entity_id": entity_id,
            "event_id": event_id,
            "predicted_clv_amount_mad": clv_amount,
            "predicted_clv_score": clean_clv.get("predicted_clv_score"),
            "predicted_clv_segment": clean_clv.get("predicted_clv_segment"),
            "clv_model_name": clean_clv.get("clv_model_name"),
            "clv_segment_model_name": clean_clv.get("clv_segment_model_name"),
            "clv_method_used": clean_clv.get("clv_method_used"),
            "ml_predicted_clv_amount_mad": clean_clv.get("ml_predicted_clv_amount_mad"),
            "math_clv_amount_mad": clean_clv.get("math_clv_amount_mad"),
            "clv_segment_prediction_source": clean_clv.get("clv_segment_prediction_source"),
            "clv_segment_confidence": clean_clv.get("clv_segment_confidence"),
            "clv_segment_top_3": clean_clv.get("clv_segment_top_3"),
            "model_registry_id": None
        }
        return insert_clv_prediction(clv_data)
    return None

def save_postgres_customer_segment(entity_id, segment_dict, event_id=None):
    clean_seg = clean_dict_values(segment_dict)
    cust_seg = clean_seg.get("customer_segment")
    if not cust_seg:
        return None
        
    latest = get_latest_customer_segment(entity_id)
    if event_id or not latest or latest["customer_segment"] != cust_seg or latest["customer_persona"] != clean_seg.get("customer_persona"):
        segment_data = {
            "entity_id": entity_id,
            "event_id": event_id,
            "customer_segment": cust_seg,
            "customer_persona": clean_seg.get("customer_persona"),
            "persona_description": clean_seg.get("persona_description"),
            "persona_recommended_action": clean_seg.get("persona_recommended_action"),
            "segmentation_method": clean_seg.get("segmentation_method", "Rule-Based RFM-ES + CLV Segmentation"),
            "ml_cluster_id": clean_seg.get("ml_cluster_id"),
            "ml_cluster_label": clean_seg.get("ml_cluster_label"),
            "cluster_persona": clean_seg.get("cluster_persona")
        }
        return insert_customer_segment(segment_data)
    return None

def load_postgres_event_history(entity_id=None):
    history_list = get_event_history(entity_id)
    return pd.DataFrame(history_list) if history_list else pd.DataFrame()
