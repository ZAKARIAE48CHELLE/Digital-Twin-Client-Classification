import json
import logging
from database.db import get_connection_string
from database.repositories import get_digital_twin_snapshot, get_event_history
from database.action_recommendations_repository import insert_llm_action_recommendation
from llm.llm_client import generate_json, get_llm_model, get_llm_provider
import llm.prompt_templates as prompts

logger = logging.getLogger("OSMOS_ACTION_INTELLIGENCE")

EXPECTED_KEYS = [
    "summary_fr", "summary_en", "risk_explanation_fr", "risk_explanation_en",
    "priority", "recommended_action_fr", "recommended_action_en", "suggested_channel",
    "message_draft_fr", "message_draft_en", "admin_guidance_fr", "admin_guidance_en",
    "confidence"
]

def build_alert_context(entity_id, alert_type):
    """Build a detailed text context from PostgreSQL snapshot and event logs."""
    try:
        snapshot = get_digital_twin_snapshot(entity_id)
        events = get_event_history(entity_id)
    except Exception as e:
        logger.error(f"Error fetching DB context for alert context building: {e}")
        snapshot = None
        events = []
        
    context = {
        "entity_id": entity_id,
        "alert_type": alert_type,
        "current_snapshot": dict(snapshot) if snapshot else {},
        "recent_events": [dict(e) for e in events[:5]] if events else []
    }
    
    # Remove large/unnecessary values to fit context windows
    if "changed_variables" in context["current_snapshot"]:
        context["current_snapshot"].pop("changed_variables", None)
        
    for e in context["recent_events"]:
        e.pop("changed_variables", None)
        e.pop("before_values", None)
        e.pop("after_values", None)
        
    return json.dumps(context, default=str, indent=2)

def generate_llm_action_for_clv_alert(alert_row):
    """Generate and save LLM action guidance for a CLV drop alert."""
    entity_id = alert_row.get("entity_id")
    alert_level = alert_row.get("alert_level")
    
    # 1. Gather context
    alert_info = {
        "entity_id": entity_id,
        "previous_clv_amount": alert_row.get("previous_clv_amount"),
        "latest_clv_amount": alert_row.get("latest_clv_amount"),
        "clv_change_amount": alert_row.get("clv_change_amount"),
        "clv_change_percent": alert_row.get("clv_change_percent"),
        "alert_level": alert_level,
        "latest_clv_segment": alert_row.get("latest_clv_segment")
    }
    db_context = build_alert_context(entity_id, "CLV Drop Alert")
    
    input_context = {
        "alert_details": alert_info,
        "customer_telemetry": json.loads(db_context)
    }
    
    # 2. Build prompt
    prompt = prompts.explain_clv_alert_prompt(json.dumps(input_context, indent=2))
    
    # 3. Call LLM
    result = generate_json(prompt, temperature=0.1, expected_keys=EXPECTED_KEYS)
    
    # 4. Add metadata and save to DB
    action_data = dict(result)
    action_data["entity_id"] = entity_id
    action_data["alert_type"] = "CLV Drop Alert"
    action_data["alert_source"] = "CLV Predictions table"
    action_data["alert_level"] = alert_level
    action_data["llm_model"] = get_llm_model()
    action_data["llm_provider"] = get_llm_provider()
    action_data["input_context"] = input_context
    action_data["raw_llm_output"] = result
    
    try:
        insert_llm_action_recommendation(action_data)
    except Exception as e:
        logger.error(f"Failed to persist LLM CLV recommendation: {e}")
        
    return action_data

def generate_llm_action_for_segment_transition(transition_row):
    """Generate and save LLM action guidance for a customer segment cohort transition."""
    entity_id = transition_row.get("entity_id")
    transition_type = transition_row.get("transition_type")
    
    # 1. Gather context
    transition_info = {
        "entity_id": entity_id,
        "previous_segment": transition_row.get("previous_segment"),
        "latest_segment": transition_row.get("latest_segment"),
        "previous_persona": transition_row.get("previous_persona"),
        "latest_persona": transition_row.get("latest_persona"),
        "transition_date": transition_row.get("transition_date"),
        "transition_type": transition_type
    }
    db_context = build_alert_context(entity_id, "Segment Transition Alert")
    
    input_context = {
        "transition_details": transition_info,
        "customer_telemetry": json.loads(db_context)
    }
    
    # 2. Build prompt
    prompt = prompts.explain_segment_transition_prompt(json.dumps(input_context, indent=2))
    
    # 3. Call LLM
    result = generate_json(prompt, temperature=0.1, expected_keys=EXPECTED_KEYS)
    
    # 4. Add metadata and save to DB
    action_data = dict(result)
    action_data["entity_id"] = entity_id
    action_data["alert_type"] = "Segment Transition Alert"
    action_data["alert_source"] = "Customer Segments table"
    # Transition severity maps to alert_level
    action_data["alert_level"] = "High" if transition_type in ["Downgrade", "Risk Increase"] else "Low"
    action_data["llm_model"] = get_llm_model()
    action_data["llm_provider"] = get_llm_provider()
    action_data["input_context"] = input_context
    action_data["raw_llm_output"] = result
    
    try:
        insert_llm_action_recommendation(action_data)
    except Exception as e:
        logger.error(f"Failed to persist LLM segment transition recommendation: {e}")
        
    return action_data

def generate_llm_action_for_prediction_drift(drift_row):
    """Generate and save LLM action guidance for prediction drift alerts."""
    dynamic_class = drift_row.get("dynamic_class")
    drift_level = drift_row.get("drift_level")
    
    # 1. Gather context
    drift_info = {
        "dynamic_class": dynamic_class,
        "baseline_count": drift_row.get("baseline_count"),
        "current_count": drift_row.get("current_count"),
        "baseline_percent": drift_row.get("baseline_percent"),
        "current_percent": drift_row.get("current_percent"),
        "change_percent": drift_row.get("change_percent"),
        "drift_flag": drift_row.get("drift_flag"),
        "drift_level": drift_level
    }
    
    # 2. Build prompt
    prompt = prompts.explain_prediction_drift_prompt(json.dumps(drift_info, indent=2))
    
    # 3. Call LLM
    result = generate_json(prompt, temperature=0.1, expected_keys=EXPECTED_KEYS)
    
    # 4. Add metadata and save to DB
    action_data = dict(result)
    action_data["entity_id"] = None
    action_data["alert_type"] = "Prediction Drift Alert"
    action_data["alert_source"] = "Classification Predictions distribution comparison"
    action_data["alert_level"] = drift_level
    action_data["llm_model"] = get_llm_model()
    action_data["llm_provider"] = get_llm_provider()
    action_data["input_context"] = {"drift_details": drift_info}
    action_data["raw_llm_output"] = result
    
    try:
        insert_llm_action_recommendation(action_data)
    except Exception as e:
        logger.error(f"Failed to persist LLM prediction drift recommendation: {e}")
        
    return action_data

def generate_entity_guidance(entity_id):
    """Generate bilingual French/English customer guidance summary."""
    db_context = build_alert_context(entity_id, "Customer History Summary Guidance")
    
    # Build prompt
    prompt = prompts.generate_customer_summary_prompt(db_context)
    
    # Call LLM
    result = generate_json(prompt, temperature=0.2, expected_keys=EXPECTED_KEYS)
    
    # Add metadata and save to DB
    action_data = dict(result)
    action_data["entity_id"] = entity_id
    action_data["alert_type"] = "Entity Guidance Assistant"
    action_data["alert_source"] = "Customer Profile & Event History"
    action_data["alert_level"] = "Low"
    action_data["llm_model"] = get_llm_model()
    action_data["llm_provider"] = get_llm_provider()
    action_data["input_context"] = {"customer_history": json.loads(db_context)}
    action_data["raw_llm_output"] = result
    
    try:
        insert_llm_action_recommendation(action_data)
    except Exception as e:
        logger.error(f"Failed to persist LLM customer guidance recommendation: {e}")
        
    return action_data
