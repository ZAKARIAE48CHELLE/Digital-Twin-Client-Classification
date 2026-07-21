import logging
from database.repositories import get_llm_recommendation_by_id
from digital_twin.digital_twin_builder import build_digital_twin_profile
from campaigns.campaign_repository import (
    create_campaign_dispatch,
    get_campaign_by_id,
    update_campaign_status
)

logger = logging.getLogger("OSMOS_CAMPAIGN_DISPATCHER")

def create_campaign_from_recommendation(recommendation_id):
    """
    Creates a new campaign dispatch draft from a saved LLM action recommendation.
    """
    rec = get_llm_recommendation_by_id(recommendation_id)
    if not rec:
        logger.error(f"LLM Recommendation #{recommendation_id} not found.")
        return None
        
    campaign_dict = {
        "recommendation_id": rec.get("id"),
        "entity_id": rec.get("entity_id"),
        "campaign_type": f"LLM Advisory ({rec.get('alert_type', 'Action Alert')})",
        "campaign_channel": rec.get("suggested_channel") or "Email",
        "campaign_title": f"Action Alert: {rec.get('alert_type', 'Customer Outreach')}",
        "campaign_message_fr": rec.get("message_draft_fr") or rec.get("recommended_action_fr"),
        "campaign_message_en": rec.get("message_draft_en") or rec.get("recommended_action_en"),
        "action_source": "LLM Advisory",
        "priority": rec.get("priority") or "High",
        "status": "Draft",
        "created_by": "admin"
    }
    
    cid = create_campaign_dispatch(campaign_dict)
    if cid:
        logger.info(f"Successfully created Campaign #{cid} from LLM Recommendation #{recommendation_id}")
    return cid

def create_campaign_from_digital_twin_action(entity_id, action_context=None):
    """
    Creates a new campaign dispatch draft directly from an entity's Digital Twin state.
    """
    if not action_context:
        profile = build_digital_twin_profile(entity_id)
        persona = profile.get("persona_context", {})
        action_context = {
            "campaign_type": f"Persona Campaign ({persona.get('customer_persona', 'Standard')})",
            "campaign_channel": persona.get("preferred_channel", "Email"),
            "campaign_title": f"Digital Twin Outreach: Entity [{entity_id}]",
            "campaign_message_fr": persona.get("recommended_action_fr", "Maintenir l'engagement avec le client."),
            "campaign_message_en": persona.get("recommended_action_en", "Maintain customer engagement."),
            "priority": persona.get("priority_level", "Medium")
        }
        
    campaign_dict = {
        "recommendation_id": None,
        "entity_id": entity_id,
        "campaign_type": action_context.get("campaign_type", "Retention Campaign"),
        "campaign_channel": action_context.get("campaign_channel", "Email"),
        "campaign_title": action_context.get("campaign_title", f"Digital Twin Outreach [{entity_id}]"),
        "campaign_message_fr": action_context.get("campaign_message_fr"),
        "campaign_message_en": action_context.get("campaign_message_en"),
        "action_source": "Digital Twin Engine",
        "priority": action_context.get("priority", "Medium"),
        "status": "Draft",
        "created_by": "admin"
    }
    
    cid = create_campaign_dispatch(campaign_dict)
    if cid:
        logger.info(f"Successfully created Campaign #{cid} from Digital Twin entity [{entity_id}]")
    return cid

def approve_campaign(campaign_id):
    """Approves a campaign draft for simulation."""
    campaign = get_campaign_by_id(campaign_id)
    if not campaign:
        return False
    if campaign.get("status") not in ["Draft", "Cancelled"]:
        logger.warning(f"Campaign #{campaign_id} cannot be approved from status {campaign.get('status')}")
        return False
        
    return update_campaign_status(campaign_id, "Approved")

def simulate_dispatch(campaign_id):
    """
    Simulates campaign dispatch.
    CRITICAL PROTOTYPE RULE: NO REAL EMAIL OR SMS IS SENT.
    Updates status to 'Simulated Dispatch' and records dispatched_at timestamp.
    """
    campaign = get_campaign_by_id(campaign_id)
    if not campaign:
        logger.error(f"Campaign #{campaign_id} not found for dispatch simulation.")
        return False
        
    if campaign.get("status") not in ["Draft", "Approved"]:
        logger.warning(f"Campaign #{campaign_id} cannot be dispatched from status {campaign.get('status')}")
        return False
        
    success = update_campaign_status(campaign_id, "Simulated Dispatch")
    if success:
        logger.info(f"SIMULATED DISPATCH EXECUTED for Campaign #{campaign_id} to Entity [{campaign.get('entity_id')}]. (Zero real messages sent).")
    return success

def cancel_campaign(campaign_id):
    """Cancels a campaign draft or approved dispatch."""
    return update_campaign_status(campaign_id, "Cancelled")
