import logging
import pandas as pd
from database.repositories import (
    get_digital_twin_snapshot,
    get_event_history
)
from admin.database_metrics import (
    is_postgres_available,
    get_entity_prediction_history,
    get_entity_clv_history,
    get_entity_rfm_history,
    get_entity_segment_history
)

from personas.persona_matcher import get_persona_for_entity, match_persona_for_segment

logger = logging.getLogger("OSMOS_DIGITAL_TWIN_BUILDER")

def get_current_digital_twin_state(entity_id):
    """Retrieves the current snapshot state of an entity's digital twin."""
    snapshot = get_digital_twin_snapshot(entity_id)
    if snapshot:
        return snapshot
        
    # Return minimal default dictionary if snapshot is missing
    is_prospect = str(entity_id).startswith("P")
    return {
        "entity_id": entity_id,
        "entity_type": "Prospect" if is_prospect else "Client",
        "dynamic_class": "Cold Prospect" if is_prospect else "Standard Active Clients",
        "customer_segment": "Prospect" if is_prospect else "Standard Active Clients",
        "recency_days": 30,
        "visits_30d": 1,
        "product_views_30d": 1,
        "cart_additions_30d": 0,
        "purchases_90d": 0 if is_prospect else 1,
        "total_spent_90d_mad": 0.0,
        "avg_order_value_mad": 0.0,
        "email_open_rate": 0.2,
        "email_click_rate": 0.05,
        "complaint_count_90d": 0,
        "review_score_avg": 4.0,
        "social_mentions_30d": 0,
        "social_sentiment_avg": 0.0,
        "rfm_score": 0.5,
        "clv_score": 0.5,
        "predicted_clv_amount_mad": 1500.0,
        "predicted_clv_segment": "Medium-Value",
        "churn_risk": "Low Risk",
        "engagement_score": "Moderate",
        "predictive_value_score": "Standard",
        "decision_priority_score": "Normal"
    }

def get_digital_twin_scores(entity_id):
    """Calculates/retrieves normalized score vectors for the digital twin."""
    state = get_current_digital_twin_state(entity_id)
    
    rfm_score = float(state.get("rfm_score") if state.get("rfm_score") is not None and not pd.isna(state.get("rfm_score")) else 0.5)
    
    # Resolve CLV Score from predicted_clv_score or clv_score
    raw_clv_score = state.get("predicted_clv_score")
    if raw_clv_score is None or pd.isna(raw_clv_score):
        raw_clv_score = state.get("clv_score")
        
    if raw_clv_score is not None and not pd.isna(raw_clv_score):
        clv_score = float(raw_clv_score)
    else:
        clv_score = 50.0
        
    clv_amount = float(state.get("predicted_clv_amount_mad") if state.get("predicted_clv_amount_mad") is not None and not pd.isna(state.get("predicted_clv_amount_mad")) else 0.0)

    
    # Calculate churn risk level
    recency = int(state.get("recency_days") or 0)
    complaints = int(state.get("complaint_count_90d") or 0)
    
    if complaints > 1 or recency > 90:
        churn_risk = "Critical Risk"
    elif complaints == 1 or recency > 60:
        churn_risk = "High Risk"
    elif recency > 30:
        churn_risk = "Moderate Risk"
    else:
        churn_risk = "Low Risk"
        
    # Engagement Score
    visits = int(state.get("visits_30d") or 0)
    open_rate = float(state.get("email_open_rate") or 0.0)
    if visits >= 10 or open_rate >= 0.5:
        engagement_score = "High Engagement"
    elif visits >= 3 or open_rate >= 0.2:
        engagement_score = "Moderate Engagement"
    else:
        engagement_score = "Low Engagement"
        
    # Decision priority score
    if churn_risk in ["Critical Risk", "High Risk"] and clv_amount > 5000:
        priority_score = "Urgent Priority"
    elif churn_risk in ["High Risk"] or clv_amount > 10000:
        priority_score = "High Priority"
    else:
        priority_score = "Normal Priority"
        
    return {
        "rfm_score": rfm_score,
        "clv_score": clv_score,
        "churn_risk": churn_risk,
        "engagement_score": engagement_score,
        "predictive_value_score": state.get("predicted_clv_segment") or "Medium-Value",
        "decision_priority_score": priority_score
    }

def get_digital_twin_predictions(entity_id):
    """Retrieves prediction state outputs for the digital twin."""
    state = get_current_digital_twin_state(entity_id)
    return {
        "dynamic_class": state.get("dynamic_class"),
        "predicted_clv_amount_mad": float(state.get("predicted_clv_amount_mad") or 0.0),
        "predicted_clv_segment": state.get("predicted_clv_segment"),
        "customer_segment": state.get("customer_segment")
    }

def get_digital_twin_events(entity_id):
    """Retrieves event logs history for this digital twin."""
    if is_postgres_available():
        events = get_event_history(entity_id)
        return events
    return []

def get_digital_twin_history(entity_id):
    """Retrieves full historical track records across all sub-engines."""
    if not is_postgres_available():
        return {
            "events": [],
            "clv_history": [],
            "rfm_history": [],
            "classification_history": [],
            "segment_history": []
        }
        
    return {
        "events": get_event_history(entity_id),
        "clv_history": get_entity_clv_history(entity_id),
        "rfm_history": get_entity_rfm_history(entity_id),
        "classification_history": get_entity_prediction_history(entity_id),
        "segment_history": get_entity_segment_history(entity_id)
    }


def get_digital_twin_persona_context(entity_id):
    """Resolves persona context through the segment mapping layer."""
    persona = get_persona_for_entity(entity_id)
    state = get_current_digital_twin_state(entity_id)
    segment = state.get("customer_segment") or persona.get("segment_name")
    
    return {
        "customer_segment": segment,
        "customer_persona": persona.get("persona_name"),
        "persona_description_fr": persona.get("description_fr"),
        "persona_description_en": persona.get("description_en"),
        "recommended_action_fr": persona.get("recommended_action_fr"),
        "recommended_action_en": persona.get("recommended_action_en"),
        "preferred_channel": persona.get("preferred_channel"),
        "priority_level": persona.get("priority_level")
    }

def build_digital_twin_profile(entity_id):
    """
    Assembles the complete, unified Digital Twin Profile object.
    Combines: Core Identity, Behavioral State, Scores, Predictions, Persona Context, History.
    """
    state = get_current_digital_twin_state(entity_id)
    scores = get_digital_twin_scores(entity_id)
    predictions = get_digital_twin_predictions(entity_id)
    persona_ctx = get_digital_twin_persona_context(entity_id)
    history = get_digital_twin_history(entity_id)
    
    profile = {
        "core_identity": {
            "entity_id": state.get("entity_id"),
            "entity_type": state.get("entity_type"),
            "created_at": state.get("created_at"),
            "converted_at": state.get("converted_at"),
            "completed_client_profile": bool(state.get("completed_client_profile", True))
        },
        "behavioral_state": {
            "recency_days": int(state.get("recency_days") or 0),
            "visits_30d": int(state.get("visits_30d") or 0),
            "product_views_30d": int(state.get("product_views_30d") or 0),
            "cart_additions_30d": int(state.get("cart_additions_30d") or 0),
            "purchases_90d": int(state.get("purchases_90d") or 0),
            "total_spent_90d_mad": float(state.get("total_spent_90d_mad") or 0.0),
            "avg_order_value_mad": float(state.get("avg_order_value_mad") or 0.0),
            "email_open_rate": float(state.get("email_open_rate") or 0.0),
            "email_click_rate": float(state.get("email_click_rate") or 0.0),
            "complaint_count_90d": int(state.get("complaint_count_90d") or 0),
            "review_score_avg": float(state.get("review_score_avg") or 5.0),
            "social_mentions_30d": int(state.get("social_mentions_30d") or 0),
            "social_sentiment_avg": float(state.get("social_sentiment_avg") or 0.0)
        },
        "scores": scores,
        "predictions": predictions,
        "persona_context": persona_ctx,
        "history": history
    }
    return profile
