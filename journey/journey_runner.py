import logging
import pandas as pd
from datetime import datetime
from storage.storage_manager import load_data, save_entity_snapshot
from digital_twin.digital_twin_builder import build_digital_twin_profile
from personas.persona_matcher import get_persona_for_entity

from journey.journey_scenarios import DEFAULT_STAGES, get_default_scenario_definition
from journey.journey_repository import (
    create_journey_scenario,
    get_journey_scenario_by_id,
    update_journey_scenario_status,
    insert_journey_step,
    get_journey_steps,
    delete_journey_scenario,
    get_latest_scenario_for_entity
)

logger = logging.getLogger("OSMOS_JOURNEY_RUNNER")

DEMO_ENTITY_ID = "P_DEMO_001"

def create_demo_entity(entity_id=DEMO_ENTITY_ID):
    """
    Creates or resets the demo entity P_DEMO_001 in memory and database.
    Uses single-entity snapshot save optimization (< 1s execution).
    """
    from admin.database_metrics import is_postgres_available
    if is_postgres_available():
        from database.db import get_cursor
        try:
            with get_cursor(commit=True) as cur:
                cur.execute("DELETE FROM classification_predictions WHERE entity_id = %s;", (entity_id,))
                cur.execute("DELETE FROM customer_segments WHERE entity_id = %s;", (entity_id,))
                cur.execute("DELETE FROM clv_predictions WHERE entity_id = %s;", (entity_id,))
                cur.execute("DELETE FROM rfm_es_scores WHERE entity_id = %s;", (entity_id,))
        except Exception as e:
            logger.warning(f"Cleanup of old prediction history for [{entity_id}] failed: {e}")


    df, history = load_data()
    
    demo_row = {
        "entity_id": entity_id,
        "entity_type": "Prospect",
        "original_entity_type": "Prospect",
        "dynamic_class": "Cold Prospect",
        "customer_segment": "Prospect",
        "first_name": "Demo",
        "last_name": "Explorer",
        "email": "p_demo_001@osmos-demo.ma",
        "phone": "+212-600-000000",
        "city": "Casablanca",
        "region": "Grand Casablanca",
        "age": 28,
        "gender": "M",
        "signup_date": datetime.now().strftime("%Y-%m-%d"),
        "source_channel": "Web Search",
        "preferred_category": "Electronics",
        "income_power_score": 0.5,
        "recency_days": 30.0,
        "visits_30d": 1.0,
        "product_views_30d": 1.0,
        "cart_additions_30d": 0.0,
        "purchases_90d": 0.0,
        "total_spent_90d_mad": 0.0,
        "avg_order_value_mad": 0.0,
        "email_open_rate": 0.0,
        "email_click_rate": 0.0,
        "complaint_count_90d": 0.0,
        "review_score_avg": 0.0,
        "social_mentions_30d": 0.0,
        "social_sentiment_avg": 0.5,
        "rfm_score": 0.15,
        "predicted_clv_score": 0.0,
        "predicted_clv_amount_mad": 0.0,
        "predicted_clv_segment": "Low Value",
        "churn_risk_score": 0.10,
        "conversion_probability": 0.10,
        "behavioral_engagement_score": 0.20,
        "predictive_value_score": 0.10,
        "decision_priority_score": 0.30,
        "customer_persona": "New Explorer",
        "converted_at": None,
        "conversion_event_id": None,
        "completed_client_profile": False
    }
    
    # Update or append in DataFrame
    idx_matches = df[df["entity_id"] == entity_id].index
    if len(idx_matches) > 0:
        idx = idx_matches[0]
        for k, v in demo_row.items():
            df.at[idx, k] = v
    else:
        new_df = pd.DataFrame([demo_row])
        df = pd.concat([df, new_df], ignore_index=True)
        
    # Save single entity snapshot
    save_entity_snapshot(df, entity_id, history)
    logger.info(f"Demo entity [{entity_id}] initialized/reset successfully.")
    return df

def reset_demo_journey(entity_id=DEMO_ENTITY_ID):
    """
    Resets the demo entity state and creates a fresh journey scenario in PostgreSQL.
    """
    create_demo_entity(entity_id)
    
    # Create fresh scenario
    scen_def = get_default_scenario_definition()
    scen_dict = {
        "scenario_name": scen_def["scenario_name"],
        "description": scen_def["description"],
        "entity_id": entity_id,
        "status": "Draft"
    }
    scenario_id = create_journey_scenario(scen_dict)
    return scenario_id

def capture_entity_state(entity_id=DEMO_ENTITY_ID):
    """Captures current entity metrics and segment-first persona for journey step recording."""
    from digital_twin.digital_twin_builder import get_current_digital_twin_state
    profile = build_digital_twin_profile(entity_id)
    state = get_current_digital_twin_state(entity_id)
    
    identity = profile.get("core_identity", {})
    scores = profile.get("scores", {})
    predictions = profile.get("predictions", {})
    persona_ctx = profile.get("persona_context", {})
    
    def safe_num(val, default=0.0):
        if val is None or pd.isna(val):
            return default
        try:
            f = float(val)
            return default if pd.isna(f) else f
        except Exception:
            return default

    rfm_val = safe_num(state.get("rfm_score"), safe_num(scores.get("rfm_score"), 0.15))
    churn_val = safe_num(state.get("churn_risk_score"), 0.10)
    
    clv_val = safe_num(predictions.get("predicted_clv_amount_mad"))
    if clv_val == 0.0:
        clv_val = safe_num(state.get("predicted_clv_amount_mad"))
    if clv_val == 0.0:
        clv_val = safe_num(state.get("total_spent_90d_mad"))
        
    return {
        "entity_id": entity_id,
        "entity_type": identity.get("entity_type") or state.get("entity_type"),
        "dynamic_class": predictions.get("dynamic_class") or state.get("dynamic_class"),
        "customer_segment": persona_ctx.get("customer_segment") or state.get("customer_segment"),
        "customer_persona": persona_ctx.get("customer_persona") or state.get("customer_persona"),
        "clv_amount": clv_val,
        "rfm_score": rfm_val,
        "churn_risk": churn_val
    }



def apply_journey_stage_events(entity_id, stage):
    """
    Applies trigger events for a stage to the demo entity via app.simulate_event.
    Updates ONLY single entity (< 1s execution).
    Returns (primary_event_id, generated_event_ids).
    """
    from app import simulate_event
    df, history = load_data()
    
    events = stage.get("trigger_events", [])
    values = stage.get("event_values", [])
    
    generated_event_ids = []
    for evt_type, val in zip(events, values):
        df, history, _, _, _, _, _, _, new_ev_id = simulate_event(
            df, history, entity_id, evt_type, val
        )
        if new_ev_id:
            generated_event_ids.append(new_ev_id)
            
    primary_event_id = generated_event_ids[0] if generated_event_ids else None
    return primary_event_id, generated_event_ids

def run_next_journey_step(scenario_id):
    """
    Executes the next step in the journey scenario.
    Updates entity, recalculates scores, resolves segment-first persona, and inserts step record.
    """
    scenario = get_journey_scenario_by_id(scenario_id)
    if not scenario:
        logger.error(f"Scenario #{scenario_id} not found.")
        return None
        
    entity_id = scenario.get("entity_id", DEMO_ENTITY_ID)
    existing_steps = get_journey_steps(scenario_id)
    next_order = len(existing_steps) + 1
    
    if next_order > len(DEFAULT_STAGES):
        logger.info(f"Scenario #{scenario_id} has already completed all {len(DEFAULT_STAGES)} stages.")
        return None
        
    stage = DEFAULT_STAGES[next_order - 1]
    
    # 1. Update scenario status to Running
    if scenario.get("status") == "Draft":
        update_journey_scenario_status(scenario_id, "Running")
        
    # 2. Capture before state
    before_state = capture_entity_state(entity_id)
    
    # 3. Apply stage events
    trigger_ev_id, generated_ev_ids = apply_journey_stage_events(entity_id, stage)
    
    # 4. FK & Persistence Integrity Check: Verify trigger_event_id exists in event_history
    if not trigger_ev_id:
        logger.error("Journey step could not be saved because the trigger event was not persisted.")
        return None
        
    from admin.database_metrics import is_postgres_available
    if is_postgres_available():
        from database.db import get_cursor
        try:
            with get_cursor(commit=False) as cur:
                cur.execute("SELECT 1 FROM event_history WHERE event_id = %s;", (trigger_ev_id,))
                exists = cur.fetchone()
        except Exception:
            exists = None
            
        if not exists:
            logger.error(f"Journey step could not be saved because the trigger event '{trigger_ev_id}' was not persisted in event_history.")
            return None

    # 5. Capture after state
    after_state = capture_entity_state(entity_id)
    
    # 6. Build step record
    step_dict = {
        "scenario_id": scenario_id,
        "step_order": next_order,
        "entity_id": entity_id,
        "stage_name": stage["stage_name"],
        "trigger_event_type": ", ".join(stage["trigger_events"]),
        "trigger_event_id": trigger_ev_id,
        "before_dynamic_class": before_state["dynamic_class"],
        "after_dynamic_class": after_state["dynamic_class"],
        "before_segment": before_state["customer_segment"],
        "after_segment": after_state["customer_segment"],
        "before_persona": before_state["customer_persona"],
        "after_persona": after_state["customer_persona"],
        "before_clv_amount": before_state["clv_amount"],
        "after_clv_amount": after_state["clv_amount"],
        "before_rfm_score": before_state["rfm_score"],
        "after_rfm_score": after_state["rfm_score"],
        "before_churn_risk": before_state["churn_risk"],
        "after_churn_risk": after_state["churn_risk"],
        "llm_explanation_fr": stage["explanation_fr"],
        "llm_explanation_en": stage["explanation_en"],
        "llm_recommendation_fr": stage["recommendation_fr"],
        "llm_recommendation_en": stage["recommendation_en"],
        "node_status": "Completed"
    }
    
    step_id = insert_journey_step(step_dict)
    if not step_id:
        logger.error(f"Journey step could not be saved because insert_journey_step failed for stage '{stage['stage_name']}'.")
        return None
        
    step_dict["step_id"] = step_id
    
    # If final stage, mark scenario completed
    if next_order == len(DEFAULT_STAGES):
        update_journey_scenario_status(scenario_id, "Completed")
        
    logger.info(f"Executed Journey Step #{next_order} for Scenario #{scenario_id} (Entity [{entity_id}]). Step ID: {step_id}")
    return step_dict

def run_full_journey(scenario_id, use_llm=False):
    """
    Runs all remaining steps of a scenario in sequence.
    Optionally calls LLM for each step if use_llm=True.
    Stops immediately if a step fails.
    """
    results = []
    for _ in range(len(DEFAULT_STAGES)):
        step = run_next_journey_step(scenario_id)
        if not step or not step.get("step_id"):
            logger.error("Run Full Journey stopped due to a failed or missing journey step.")
            break
        if use_llm:
            generate_llm_journey_explanation(step)
        results.append(step)
    return results


def generate_llm_journey_explanation(step_dict):
    """
    OPTIONAL & BUTTON-TRIGGERED ONLY!
    Generates local LLM explanations for a specific journey transition.
    """
    try:
        from llm.llm_client import generate_json
        from llm.llm_config import is_llm_enabled
        
        if not is_llm_enabled():
            return step_dict
            
        prompt = f"""
You are an expert CRM Data Scientist analyzing a Digital Twin customer lifecycle transition.

Context:
Stage Name: {step_dict.get('stage_name')}
Trigger Events: {step_dict.get('trigger_event_type')}
Before Dynamic Class: {step_dict.get('before_dynamic_class')} -> After Dynamic Class: {step_dict.get('after_dynamic_class')}
Before Segment: {step_dict.get('before_segment')} -> After Segment: {step_dict.get('after_segment')}
Before Persona: {step_dict.get('before_persona')} -> After Persona: {step_dict.get('after_persona')}
Before CLV: {step_dict.get('before_clv_amount')} MAD -> After CLV: {step_dict.get('after_clv_amount')} MAD
Before RFM: {step_dict.get('before_rfm_score')} -> After RFM: {step_dict.get('after_rfm_score')}
Before Churn Risk: {step_dict.get('before_churn_risk')} -> After Churn Risk: {step_dict.get('after_churn_risk')}

Respond ONLY with valid JSON matching these keys:
{{
  "explanation_fr": "Description analytique en français du changement de comportement et de l'évolution du Digital Twin.",
  "explanation_en": "Analytical summary in English of the behavioral shift and Digital Twin evolution.",
  "recommendation_fr": "Action marketing stratégique recommandée en français.",
  "recommendation_en": "Strategic recommended marketing action in English."
}}
        """
        res = generate_json(prompt, temperature=0.2)
        if res and "explanation_fr" in res:
            step_dict["llm_explanation_fr"] = res["explanation_fr"]
            step_dict["llm_explanation_en"] = res.get("explanation_en")
            step_dict["llm_recommendation_fr"] = res.get("recommendation_fr")
            step_dict["llm_recommendation_en"] = res.get("recommendation_en")
    except Exception as e:
        logger.warning(f"Optional LLM journey explanation failed: {e}")
        
    return step_dict
