import logging
from database.db import get_cursor
from admin.database_metrics import is_postgres_available

logger = logging.getLogger("OSMOS_JOURNEY_REPO")

def create_journey_scenario(scenario_dict):
    """Inserts a new journey scenario in PostgreSQL."""
    if not is_postgres_available():
        logger.warning("PostgreSQL unavailable; journey scenario cannot be saved in Excel mode.")
        return None
        
    query = """
        INSERT INTO journey_scenarios (
            scenario_name, description, entity_id, status, created_at, updated_at
        ) VALUES (
            %(scenario_name)s, %(description)s, %(entity_id)s, %(status)s, NOW(), NOW()
        ) RETURNING scenario_id;
    """
    params = {
        "scenario_name": scenario_dict.get("scenario_name", "Prospect to VIP to Churn Risk"),
        "description": scenario_dict.get("description", "Digital Twin 5-stage lifecycle simulation scenario."),
        "entity_id": scenario_dict.get("entity_id", "P_DEMO_001"),
        "status": scenario_dict.get("status", "Draft")
    }
    
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(query, params)
            res = cur.fetchone()
            return res['scenario_id'] if res else None
    except Exception as e:
        logger.error(f"Failed to create journey scenario: {e}")
        return None

def get_journey_scenarios(entity_id=None, limit=20):
    """Retrieves journey scenarios optionally filtered by entity_id."""
    if not is_postgres_available():
        return []
        
    query = "SELECT * FROM journey_scenarios"
    params = []
    if entity_id:
        query += " WHERE entity_id = %s"
        params.append(entity_id)
        
    query += " ORDER BY created_at DESC LIMIT %s;"
    params.append(limit)
    
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query, tuple(params))
            return cur.fetchall() or []
    except Exception as e:
        logger.error(f"Failed to fetch journey scenarios: {e}")
        return []

def get_journey_scenario_by_id(scenario_id):
    """Fetches a single journey scenario by ID."""
    if not is_postgres_available() or not scenario_id:
        return None
        
    query = "SELECT * FROM journey_scenarios WHERE scenario_id = %s;"
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query, (scenario_id,))
            return cur.fetchone()
    except Exception as e:
        logger.error(f"Failed to fetch scenario #{scenario_id}: {e}")
        return None

def update_journey_scenario_status(scenario_id, status):
    """Updates the status of a journey scenario."""
    if not is_postgres_available() or not scenario_id:
        return False
        
    query = """
        UPDATE journey_scenarios
        SET status = %s, updated_at = NOW()
        WHERE scenario_id = %s;
    """
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(query, (status, scenario_id))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to update scenario #{scenario_id} status: {e}")
        return False

def insert_journey_step(step_dict):
    """Inserts a single journey step execution record."""
    if not is_postgres_available():
        return None
        
    query = """
        INSERT INTO journey_steps (
            scenario_id, step_order, entity_id, stage_name, trigger_event_type, trigger_event_id,
            before_dynamic_class, after_dynamic_class, before_segment, after_segment,
            before_persona, after_persona, before_clv_amount, after_clv_amount,
            before_rfm_score, after_rfm_score, before_churn_risk, after_churn_risk,
            llm_explanation_fr, llm_explanation_en, llm_recommendation_fr, llm_recommendation_en,
            node_status, created_at
        ) VALUES (
            %(scenario_id)s, %(step_order)s, %(entity_id)s, %(stage_name)s, %(trigger_event_type)s, %(trigger_event_id)s,
            %(before_dynamic_class)s, %(after_dynamic_class)s, %(before_segment)s, %(after_segment)s,
            %(before_persona)s, %(after_persona)s, %(before_clv_amount)s, %(after_clv_amount)s,
            %(before_rfm_score)s, %(after_rfm_score)s, %(before_churn_risk)s, %(after_churn_risk)s,
            %(llm_explanation_fr)s, %(llm_explanation_en)s, %(llm_recommendation_fr)s, %(llm_recommendation_en)s,
            %(node_status)s, NOW()
        ) RETURNING step_id;
    """
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(query, step_dict)
            res = cur.fetchone()
            return res['step_id'] if res else None
    except Exception as e:
        logger.error(f"Failed to insert journey step: {e}")
        return None

def get_journey_steps(scenario_id):
    """Retrieves all steps for a given journey scenario ordered by step_order."""
    if not is_postgres_available() or not scenario_id:
        return []
        
    query = """
        SELECT * FROM journey_steps
        WHERE scenario_id = %s
        ORDER BY step_order ASC;
    """
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query, (scenario_id,))
            return cur.fetchall() or []
    except Exception as e:
        logger.error(f"Failed to fetch journey steps for scenario #{scenario_id}: {e}")
        return []

def delete_journey_scenario(scenario_id):
    """Deletes a journey scenario and its steps."""
    if not is_postgres_available() or not scenario_id:
        return False
        
    query = "DELETE FROM journey_scenarios WHERE scenario_id = %s;"
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(query, (scenario_id,))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to delete scenario #{scenario_id}: {e}")
        return False

def get_latest_scenario_for_entity(entity_id="P_DEMO_001"):
    """Fetches the latest scenario for a given entity."""
    scenarios = get_journey_scenarios(entity_id=entity_id, limit=1)
    return scenarios[0] if scenarios else None
