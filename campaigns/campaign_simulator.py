import logging
import random
from datetime import datetime
from storage.storage_manager import load_data, save_entity_snapshot
from digital_twin.digital_twin_builder import build_digital_twin_profile
from campaigns.campaign_repository import (
    get_campaign_by_id,
    update_campaign_status,
    insert_campaign_response
)

logger = logging.getLogger("OSMOS_CAMPAIGN_SIMULATOR")

RESPONSE_TO_EVENT_MAP = {
    "Opened": "email_open",
    "Clicked": "email_click",
    "Purchased": "purchase",
    "Complained": "complaint",
    "Positive Feedback": "positive_review",
    "Negative Feedback": "negative_review",
    "Ignored": "inactivity_period",
    "Unsubscribed": "complaint"
}

def determine_probabilistic_response(entity_id):
    """
    Computes a probabilistic customer response based on Digital Twin behavioral & risk scores.
    Rules:
    - High engagement -> higher chance of Opened / Clicked
    - High CLV + low churn risk -> higher chance of Purchased
    - High churn risk + complaints -> higher chance of Complained / Ignored
    """
    profile = build_digital_twin_profile(entity_id)
    scores = profile.get("scores", {})
    behavior = profile.get("behavioral_state", {})
    
    churn_risk = scores.get("churn_risk", "Low Risk")
    engagement = scores.get("engagement_score", "Low Engagement")
    clv_amount = behavior.get("total_spent_90d_mad", 0.0)
    complaints = behavior.get("complaint_count_90d", 0)
    
    # Weight probabilities: [Opened, Clicked, Purchased, Ignored, Complained, Positive Feedback, Negative Feedback, Unsubscribed]
    types = ["Opened", "Clicked", "Purchased", "Ignored", "Complained", "Positive Feedback", "Negative Feedback", "Unsubscribed"]
    
    if complaints > 1 or "Critical" in churn_risk:
        weights = [0.10, 0.05, 0.0, 0.45, 0.25, 0.0, 0.10, 0.05]
    elif "High" in churn_risk:
        weights = [0.20, 0.10, 0.05, 0.40, 0.15, 0.0, 0.05, 0.05]
    elif "High" in engagement or clv_amount > 10000:
        weights = [0.25, 0.30, 0.30, 0.05, 0.0, 0.10, 0.0, 0.0]
    elif "Moderate" in engagement:
        weights = [0.40, 0.25, 0.15, 0.15, 0.0, 0.05, 0.0, 0.0]
    else:
        weights = [0.30, 0.15, 0.05, 0.40, 0.05, 0.0, 0.03, 0.02]
        
    chosen = random.choices(types, weights=weights, k=1)[0]
    return chosen

def simulate_campaign_response(campaign_id, forced_response_type=None):
    """
    Simulates customer response to a dispatched campaign.
    Converts response to an event, updates the entity's Digital Twin state,
    saves the single updated entity, and records campaign response metrics.
    """
    campaign = get_campaign_by_id(campaign_id)
    if not campaign:
        logger.error(f"Campaign #{campaign_id} not found for response simulation.")
        return None
        
    entity_id = campaign.get("entity_id")
    if not entity_id:
        logger.error(f"Campaign #{campaign_id} has no associated entity_id.")
        return None
        
    # Determine response type
    if forced_response_type:
        response_type = forced_response_type
    else:
        response_type = determine_probabilistic_response(entity_id)
        
    # Generate event and apply single-entity Digital Twin update
    event_id = generate_response_event(entity_id, campaign_id, response_type)
    
    # Calculate response score (0.0 to 1.0)
    score_map = {
        "Purchased": 1.0,
        "Clicked": 0.8,
        "Positive Feedback": 0.9,
        "Opened": 0.5,
        "Ignored": 0.2,
        "Negative Feedback": 0.1,
        "Complained": 0.0,
        "Unsubscribed": 0.0
    }
    resp_score = score_map.get(response_type, 0.5)
    
    response_dict = {
        "campaign_id": campaign_id,
        "entity_id": entity_id,
        "response_type": response_type,
        "response_score": resp_score,
        "response_event_id": event_id,
        "response_details": {
            "campaign_title": campaign.get("campaign_title"),
            "channel": campaign.get("campaign_channel"),
            "simulated_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    resp_id = insert_campaign_response(response_dict)
    
    # Update campaign status
    new_status = "Responded" if response_type != "Ignored" else "No Response"
    update_campaign_status(campaign_id, new_status)
    
    logger.info(f"Simulated response '{response_type}' for Campaign #{campaign_id} (Entity [{entity_id}]). Event ID: {event_id}")
    
    return {
        "response_id": resp_id,
        "campaign_id": campaign_id,
        "entity_id": entity_id,
        "response_type": response_type,
        "event_id": event_id,
        "status": new_status
    }

def generate_response_event(entity_id, campaign_id, response_type):
    """
    Converts a campaign response into a standard OSMOS event and applies single-entity snapshot save.
    """
    event_type = RESPONSE_TO_EVENT_MAP.get(response_type, "page_visit")
    
    try:
        from app import simulate_event
        df, history = load_data()
        
        # Determine purchase value if applicable
        event_value = None
        if event_type == "purchase":
            profile = build_digital_twin_profile(entity_id)
            aov = profile.get("behavioral_state", {}).get("avg_order_value_mad", 1500.0)
            event_value = max(float(aov if aov > 0 else 1500.0), 500.0)
            
        updated_df, updated_hist, _, _, _, _, _, _, new_event_id = simulate_event(
            df, history, entity_id, event_type, event_value
        )
        return new_event_id or f"E_CAMP_{campaign_id}"
    except Exception as e:
        logger.error(f"Error generating event for entity {entity_id}: {e}")
        return f"E_CAMP_{campaign_id}"

def apply_campaign_response_to_digital_twin(entity_id, response_type):
    """Applies direct single-entity Digital Twin state modification."""
    return generate_response_event(entity_id, 0, response_type)
