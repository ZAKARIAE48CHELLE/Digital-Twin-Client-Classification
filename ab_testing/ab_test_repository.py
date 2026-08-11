"""
OSMOS A/B Test Repository (Phase 8.8)
=====================================
Database persistence methods for saving and querying A/B test experiments, variants,
simulated responses, and recommendations in PostgreSQL with Excel fallback.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from database.db import get_connection, execute_query
from storage.storage_manager import get_storage_backend
from ab_testing.ab_test_schemas import (
    ABExperiment,
    ABVariant,
    SimulatedResponse,
    ABRecommendation,
    ABEvaluationResult,
)

logger = logging.getLogger("OSMOS_AB_TEST_REPO")


def ensure_ab_test_tables_exist():
    """Checks and creates A/B testing tables in PostgreSQL if missing."""
    if get_storage_backend() != "postgres":
        return
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ab_test_experiments (
                experiment_id SERIAL PRIMARY KEY,
                entity_id VARCHAR(50) REFERENCES entities(entity_id) ON DELETE CASCADE,
                experiment_name TEXT NOT NULL,
                admin_question TEXT NOT NULL,
                objective TEXT NOT NULL,
                target_segment TEXT,
                target_persona TEXT,
                status TEXT DEFAULT 'Draft' CHECK (status IN ('Draft', 'Simulated', 'Converted to Campaign', 'Archived')),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_by TEXT DEFAULT 'admin',
                storage_mode TEXT DEFAULT 'postgres',
                llm_generated BOOLEAN DEFAULT FALSE,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS ab_test_variants (
                variant_id SERIAL PRIMARY KEY,
                experiment_id INTEGER REFERENCES ab_test_experiments(experiment_id) ON DELETE CASCADE,
                variant_label TEXT NOT NULL,
                variant_title TEXT NOT NULL,
                message_text TEXT NOT NULL,
                offer_type TEXT DEFAULT 'none',
                incentive_value NUMERIC(10, 2) DEFAULT 0.0,
                channel TEXT DEFAULT 'email',
                tone TEXT DEFAULT 'commercial',
                call_to_action TEXT,
                expected_behavior TEXT,
                validation_status TEXT DEFAULT 'Valid',
                validation_warnings JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS ab_test_simulated_responses (
                response_id SERIAL PRIMARY KEY,
                experiment_id INTEGER REFERENCES ab_test_experiments(experiment_id) ON DELETE CASCADE,
                variant_id INTEGER REFERENCES ab_test_variants(variant_id) ON DELETE CASCADE,
                entity_id VARCHAR(50) REFERENCES entities(entity_id) ON DELETE CASCADE,
                predicted_open_probability NUMERIC(5, 4),
                predicted_click_probability NUMERIC(5, 4),
                predicted_conversion_probability NUMERIC(5, 4),
                predicted_complaint_probability NUMERIC(5, 4),
                predicted_churn_delta NUMERIC(5, 4),
                predicted_clv_delta NUMERIC(12, 2),
                predicted_rfm_es_delta NUMERIC(5, 4),
                predicted_satisfaction_delta NUMERIC(5, 4),
                simulated_response_type TEXT,
                simulation_reason TEXT,
                response_score NUMERIC(6, 2),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS ab_test_recommendations (
                recommendation_id SERIAL PRIMARY KEY,
                experiment_id INTEGER REFERENCES ab_test_experiments(experiment_id) ON DELETE CASCADE,
                winning_variant_id INTEGER REFERENCES ab_test_variants(variant_id) ON DELETE CASCADE,
                confidence_score NUMERIC(5, 4),
                recommendation_summary TEXT,
                decision_reason TEXT,
                risk_notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Failed to verify A/B test tables: {e}")


def save_ab_experiment(evaluation_result: ABEvaluationResult) -> Optional[int]:
    """
    Saves an A/B evaluation result (experiment, variants, simulated responses, recommendation)
    to PostgreSQL. Does NOT alter customer profile tables.
    """
    if get_storage_backend() != "postgres":
        logger.info("Running in Excel mode: A/B Experiment saved in memory/session state only.")
        return 999

    ensure_ab_test_tables_exist()

    exp = evaluation_result.experiment
    variants = evaluation_result.variants
    responses = evaluation_result.responses
    rec = evaluation_result.recommendation

    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1. Insert Experiment
        cur.execute("""
            INSERT INTO ab_test_experiments (
                entity_id, experiment_name, admin_question, objective,
                target_segment, target_persona, status, created_by,
                storage_mode, llm_generated, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING experiment_id;
        """, (
            exp.entity_id, exp.experiment_name, exp.admin_question, exp.objective,
            exp.target_segment, exp.target_persona, "Simulated", exp.created_by,
            "postgres", exp.llm_generated, exp.notes
        ))
        exp_id = cur.fetchone()[0]
        exp.experiment_id = exp_id

        # 2. Insert Variants
        label_to_var_id = {}
        for var in variants:
            warnings_json = json.dumps(var.validation_warnings) if var.validation_warnings else "[]"
            cur.execute("""
                INSERT INTO ab_test_variants (
                    experiment_id, variant_label, variant_title, message_text,
                    offer_type, incentive_value, channel, tone,
                    call_to_action, expected_behavior, validation_status, validation_warnings
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING variant_id;
            """, (
                exp_id, var.variant_label, var.variant_title, var.message_text,
                var.offer_type, var.incentive_value, var.channel, var.tone,
                var.call_to_action, var.expected_behavior, var.validation_status, warnings_json
            ))
            v_id = cur.fetchone()[0]
            var.variant_id = v_id
            var.experiment_id = exp_id
            label_to_var_id[var.variant_label] = v_id

        # 3. Insert Simulated Responses
        for resp in responses:
            v_id = label_to_var_id.get(resp.variant_label)
            cur.execute("""
                INSERT INTO ab_test_simulated_responses (
                    experiment_id, variant_id, entity_id,
                    predicted_open_probability, predicted_click_probability,
                    predicted_conversion_probability, predicted_complaint_probability,
                    predicted_churn_delta, predicted_clv_delta, predicted_rfm_es_delta,
                    predicted_satisfaction_delta, simulated_response_type, simulation_reason, response_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING response_id;
            """, (
                exp_id, v_id, exp.entity_id,
                resp.predicted_open_probability, resp.predicted_click_probability,
                resp.predicted_conversion_probability, resp.predicted_complaint_probability,
                resp.predicted_churn_delta, resp.predicted_clv_delta, resp.predicted_rfm_es_delta,
                resp.predicted_satisfaction_delta, resp.simulated_response_type, resp.simulation_reason, resp.response_score
            ))
            resp_id = cur.fetchone()[0]
            resp.response_id = resp_id
            resp.experiment_id = exp_id
            resp.variant_id = v_id
            resp.entity_id = exp.entity_id

        # 4. Insert Recommendation
        winning_v_id = label_to_var_id.get(rec.winning_variant_label)
        cur.execute("""
            INSERT INTO ab_test_recommendations (
                experiment_id, winning_variant_id, confidence_score,
                recommendation_summary, decision_reason, risk_notes
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING recommendation_id;
        """, (
            exp_id, winning_v_id, rec.confidence_score,
            rec.recommendation_summary, rec.decision_reason, rec.risk_notes
        ))
        rec_id = cur.fetchone()[0]
        rec.recommendation_id = rec_id
        rec.experiment_id = exp_id
        rec.winning_variant_id = winning_v_id

        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Successfully saved A/B Experiment #{exp_id} for entity [{exp.entity_id}].")
        return exp_id
    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"Failed to save A/B experiment: {e}")
        return None


def get_ab_experiments_for_entity(entity_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetches past A/B test experiments for a specific customer entity."""
    if get_storage_backend() != "postgres":
        return []

    ensure_ab_test_tables_exist()
    query = """
        SELECT e.experiment_id, e.entity_id, e.experiment_name, e.admin_question, e.objective,
               e.status, e.llm_generated, e.created_at,
               r.winning_variant_id, r.confidence_score, r.recommendation_summary, r.decision_reason,
               v.variant_label AS winning_label, v.variant_title AS winning_title
        FROM ab_test_experiments e
        LEFT JOIN ab_test_recommendations r ON e.experiment_id = r.experiment_id
        LEFT JOIN ab_test_variants v ON r.winning_variant_id = v.variant_id
        WHERE e.entity_id = %s
        ORDER BY e.created_at DESC
        LIMIT %s;
    """
    rows = execute_query(query, (entity_id, limit))
    if not rows:
        return []
    return [dict(r) for r in rows]


def get_latest_ab_experiment_for_entity(entity_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves the most recent A/B test experiment details for an entity."""
    exps = get_ab_experiments_for_entity(entity_id, limit=1)
    if exps:
        return exps[0]
    return None


def get_ab_experiment_details(experiment_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves full details (experiment, variants, responses, recommendation) for an experiment ID."""
    if get_storage_backend() != "postgres":
        return None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM ab_test_experiments WHERE experiment_id = %s;", (experiment_id,))
        exp_row = cur.fetchone()
        if not exp_row:
            conn.close()
            return None

        exp_dict = dict(zip([desc[0] for desc in cur.description], exp_row))

        cur.execute("SELECT * FROM ab_test_variants WHERE experiment_id = %s ORDER BY variant_label ASC;", (experiment_id,))
        var_rows = cur.fetchall()
        var_dicts = [dict(zip([desc[0] for desc in cur.description], r)) for r in var_rows]

        cur.execute("SELECT * FROM ab_test_simulated_responses WHERE experiment_id = %s;", (experiment_id,))
        resp_rows = cur.fetchall()
        resp_dicts = [dict(zip([desc[0] for desc in cur.description], r)) for r in resp_rows]

        cur.execute("SELECT * FROM ab_test_recommendations WHERE experiment_id = %s;", (experiment_id,))
        rec_row = cur.fetchone()
        rec_dict = dict(zip([desc[0] for desc in cur.description], rec_row)) if rec_row else {}

        conn.close()
        return {
            "experiment": exp_dict,
            "variants": var_dicts,
            "responses": resp_dicts,
            "recommendation": rec_dict,
        }
    except Exception as e:
        conn.close()
        logger.error(f"Failed to fetch A/B experiment details #{experiment_id}: {e}")
        return None


def convert_variant_to_campaign_draft(experiment_id: int, variant_id: int) -> Optional[int]:
    """
    Converts a winning A/B test variant into a simulated campaign draft in campaign_dispatches.
    Requires explicit administrator button click. Does NOT dispatch a real campaign.
    """
    if get_storage_backend() != "postgres":
        logger.info("Excel mode: Converted winning variant to in-memory campaign draft.")
        return 999

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Fetch experiment & variant
        cur.execute("SELECT entity_id, admin_question, objective FROM ab_test_experiments WHERE experiment_id = %s;", (experiment_id,))
        exp_row = cur.fetchone()
        if not exp_row:
            conn.close()
            return None

        entity_id, admin_question, objective = exp_row

        cur.execute("SELECT variant_label, variant_title, message_text, channel, tone, incentive_value FROM ab_test_variants WHERE variant_id = %s;", (variant_id,))
        var_row = cur.fetchone()
        if not var_row:
            conn.close()
            return None

        label, title, msg, channel, tone, incentive = var_row

        campaign_title = f"A/B Winner ({label}): {title}"
        campaign_type = f"AB_TEST_{objective.upper()}"
        priority = "High" if objective in ["retention", "complaint_recovery"] else "Medium"

        cur.execute("""
            INSERT INTO campaign_dispatches (
                entity_id, campaign_type, campaign_channel, campaign_title,
                campaign_message_en, campaign_message_fr, action_source, priority, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Draft')
            RETURNING campaign_id;
        """, (
            entity_id, campaign_type, channel, campaign_title,
            msg, msg, f"A/B Experiment #{experiment_id}", priority
        ))
        campaign_id = cur.fetchone()[0]

        # Update experiment status
        cur.execute("UPDATE ab_test_experiments SET status = 'Converted to Campaign' WHERE experiment_id = %s;", (experiment_id,))

        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Successfully converted A/B Variant '{label}' to Campaign Draft #{campaign_id}.")
        return campaign_id
    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"Failed to convert A/B variant to campaign draft: {e}")
        return None


def apply_simulated_response_as_event(experiment_id: int, variant_id: int, entity_id: str) -> Optional[str]:
    """
    Optional action: Creates an event_history record for the winning simulated response.
    Requires explicit administrator button click and approval.
    """
    if get_storage_backend() != "postgres":
        return None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT r.simulated_response_type, r.response_score, r.simulation_reason,
                   v.variant_label, v.variant_title
            FROM ab_test_simulated_responses r
            JOIN ab_test_variants v ON r.variant_id = v.variant_id
            WHERE r.experiment_id = %s AND r.variant_id = %s;
        """, (experiment_id, variant_id))
        row = cur.fetchone()
        if not row:
            conn.close()
            return None

        response_type, score, reason, label, title = row
        event_id = f"EVT_AB_{experiment_id}_{int(datetime.now().timestamp())}"

        metadata = json.dumps({
            "experiment_id": experiment_id,
            "variant_id": variant_id,
            "variant_label": label,
            "variant_title": title,
            "response_score": float(score),
            "reasoning": reason,
        })

        cur.execute("""
            INSERT INTO event_history (
                event_id, entity_id, event_type, old_class, new_class, class_changed, changed_variables
            ) VALUES (%s, %s, %s, %s, %s, FALSE, %s);
        """, (
            event_id, entity_id, f"ab_test_simulated_response_{response_type.lower()}",
            "N/A", "N/A", metadata
        ))

        # Record audit log
        cur.execute("""
            INSERT INTO audit_logs (action_type, entity_id, event_id, details)
            VALUES (%s, %s, %s, %s);
        """, (
            "AB_TEST_EVENT_APPLIED", entity_id, event_id, metadata
        ))

        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Applied A/B simulated response event '{event_id}' for entity [{entity_id}].")
        return event_id
    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"Failed to apply A/B simulated response event: {e}")
        return None
