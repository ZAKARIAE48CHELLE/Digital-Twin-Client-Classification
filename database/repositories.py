import json
import psycopg2.extras
from database.db import get_cursor

# Helper to serialize values to JSONB safely using psycopg2.extras.Json
def safe_json(val):
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return psycopg2.extras.Json(val)
    if isinstance(val, str):
        val_str = val.strip()
        if (val_str.startswith('{') and val_str.endswith('}')) or (val_str.startswith('[') and val_str.endswith(']')):
            try:
                parsed = json.loads(val_str)
                return psycopg2.extras.Json(parsed)
            except Exception:
                pass
    return psycopg2.extras.Json(val)


# Helper to parse JSON values safely
def safe_parse_json(val):
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return val

# ============================================================
# 1. Entity Repositories
# ============================================================

def upsert_entity(entity_dict):
    """Inserts or updates a core entity record."""
    query = """
        INSERT INTO entities (
            entity_id, entity_type, original_entity_type, created_at, converted_at, 
            conversion_event_id, completed_client_profile, region, source_channel, 
            segment, persona, age_group, preferred_device, preferred_category, 
            marketing_consent, price_sensitivity, income_power_score, 
            initial_interest_score, basic_profile_score, updated_timestamp
        ) VALUES (
            %(entity_id)s, %(entity_type)s, %(original_entity_type)s, %(created_at)s, %(converted_at)s, 
            %(conversion_event_id)s, %(completed_client_profile)s, %(region)s, %(source_channel)s, 
            %(segment)s, %(persona)s, %(age_group)s, %(preferred_device)s, %(preferred_category)s, 
            %(marketing_consent)s, %(price_sensitivity)s, %(income_power_score)s, 
            %(initial_interest_score)s, %(basic_profile_score)s, NOW()
        )
        ON CONFLICT (entity_id) DO UPDATE SET
            entity_type = EXCLUDED.entity_type,
            original_entity_type = EXCLUDED.original_entity_type,
            converted_at = EXCLUDED.converted_at,
            conversion_event_id = EXCLUDED.conversion_event_id,
            completed_client_profile = EXCLUDED.completed_client_profile,
            region = EXCLUDED.region,
            source_channel = EXCLUDED.source_channel,
            segment = EXCLUDED.segment,
            persona = EXCLUDED.persona,
            age_group = EXCLUDED.age_group,
            preferred_device = EXCLUDED.preferred_device,
            preferred_category = EXCLUDED.preferred_category,
            marketing_consent = EXCLUDED.marketing_consent,
            price_sensitivity = EXCLUDED.price_sensitivity,
            income_power_score = EXCLUDED.income_power_score,
            initial_interest_score = EXCLUDED.initial_interest_score,
            basic_profile_score = EXCLUDED.basic_profile_score,
            updated_timestamp = NOW()
        RETURNING entity_id;
    """
    with get_cursor() as cur:
        cur.execute(query, entity_dict)
        res = cur.fetchone()
        return res['entity_id'] if res else None

def get_entity(entity_id):
    """Retrieves a single entity by ID."""
    query = "SELECT * FROM entities WHERE entity_id = %s;"
    with get_cursor(commit=False) as cur:
        cur.execute(query, (entity_id,))
        return cur.fetchone()

def get_all_entities():
    """Retrieves all entities."""
    query = "SELECT * FROM entities;"
    with get_cursor(commit=False) as cur:
        cur.execute(query)
        return cur.fetchall()

def update_entity_lifecycle(entity_id, lifecycle_dict):
    """Updates lifecycle columns on entity conversion."""
    query = """
        UPDATE entities SET
            entity_type = %(entity_type)s,
            original_entity_type = %(original_entity_type)s,
            converted_at = %(converted_at)s,
            conversion_event_id = %(conversion_event_id)s,
            completed_client_profile = %(completed_client_profile)s,
            updated_timestamp = NOW()
        WHERE entity_id = %(entity_id)s
        RETURNING entity_id;
    """
    params = dict(lifecycle_dict)
    params['entity_id'] = entity_id
    with get_cursor() as cur:
        cur.execute(query, params)
        res = cur.fetchone()
        return res['entity_id'] if res else None


# ============================================================
# 2. Customer Profile Repositories
# ============================================================

def upsert_customer_profile(profile_dict):
    """Inserts or updates customer demographic profile."""
    query = """
        INSERT INTO customer_profiles (
            entity_id, age, sex, email, customer_type, household_size, 
            phone_number, company_name, job_title, city, address, updated_at
        ) VALUES (
            %(entity_id)s, %(age)s, %(sex)s, %(email)s, %(customer_type)s, %(household_size)s, 
            %(phone_number)s, %(company_name)s, %(job_title)s, %(city)s, %(address)s, NOW()
        )
        ON CONFLICT (entity_id) DO UPDATE SET
            age = EXCLUDED.age,
            sex = EXCLUDED.sex,
            email = EXCLUDED.email,
            customer_type = EXCLUDED.customer_type,
            household_size = EXCLUDED.household_size,
            phone_number = EXCLUDED.phone_number,
            company_name = EXCLUDED.company_name,
            job_title = EXCLUDED.job_title,
            city = EXCLUDED.city,
            address = EXCLUDED.address,
            updated_at = NOW()
        RETURNING entity_id;
    """
    with get_cursor() as cur:
        cur.execute(query, profile_dict)
        res = cur.fetchone()
        return res['entity_id'] if res else None

def get_customer_profile(entity_id):
    """Retrieves profile of a customer."""
    query = "SELECT * FROM customer_profiles WHERE entity_id = %s;"
    with get_cursor(commit=False) as cur:
        cur.execute(query, (entity_id,))
        return cur.fetchone()


# ============================================================
# 3. Digital Twin Snapshot Repositories
# ============================================================

def upsert_digital_twin_snapshot(snapshot_dict):
    """Inserts or updates the latest digital twin state snapshot."""
    query = """
        INSERT INTO digital_twin_snapshots (
            entity_id, snapshot_date, recency_days, visits_30d, product_views_30d, 
            cart_additions_30d, purchases_90d, total_spent_90d_mad, avg_order_value_mad, 
            email_open_rate, email_click_rate, complaint_count_90d, review_score_avg, 
            social_mentions_30d, social_sentiment_avg, conversion_probability, 
            churn_risk_score, rfm_score, behavioral_engagement_score, 
            predictive_value_score, decision_priority_score, updated_at
        ) VALUES (
            %(entity_id)s, %(snapshot_date)s, %(recency_days)s, %(visits_30d)s, %(product_views_30d)s, 
            %(cart_additions_30d)s, %(purchases_90d)s, %(total_spent_90d_mad)s, %(avg_order_value_mad)s, 
            %(email_open_rate)s, %(email_click_rate)s, %(complaint_count_90d)s, %(review_score_avg)s, 
            %(social_mentions_30d)s, %(social_sentiment_avg)s, %(conversion_probability)s, 
            %(churn_risk_score)s, %(rfm_score)s, %(behavioral_engagement_score)s, 
            %(predictive_value_score)s, %(decision_priority_score)s, NOW()
        )
        ON CONFLICT (entity_id) DO UPDATE SET
            snapshot_date = EXCLUDED.snapshot_date,
            recency_days = EXCLUDED.recency_days,
            visits_30d = EXCLUDED.visits_30d,
            product_views_30d = EXCLUDED.product_views_30d,
            cart_additions_30d = EXCLUDED.cart_additions_30d,
            purchases_90d = EXCLUDED.purchases_90d,
            total_spent_90d_mad = EXCLUDED.total_spent_90d_mad,
            avg_order_value_mad = EXCLUDED.avg_order_value_mad,
            email_open_rate = EXCLUDED.email_open_rate,
            email_click_rate = EXCLUDED.email_click_rate,
            complaint_count_90d = EXCLUDED.complaint_count_90d,
            review_score_avg = EXCLUDED.review_score_avg,
            social_mentions_30d = EXCLUDED.social_mentions_30d,
            social_sentiment_avg = EXCLUDED.social_sentiment_avg,
            conversion_probability = EXCLUDED.conversion_probability,
            churn_risk_score = EXCLUDED.churn_risk_score,
            rfm_score = EXCLUDED.rfm_score,
            behavioral_engagement_score = EXCLUDED.behavioral_engagement_score,
            predictive_value_score = EXCLUDED.predictive_value_score,
            decision_priority_score = EXCLUDED.decision_priority_score,
            updated_at = NOW()
        RETURNING entity_id;
    """
    with get_cursor() as cur:
        cur.execute(query, snapshot_dict)
        res = cur.fetchone()
        return res['entity_id'] if res else None

def get_digital_twin_snapshot(entity_id):
    """Gets latest snapshot state for entity including identity, predictions, CLV, and segment."""
    from admin.database_metrics import is_postgres_available
    if not is_postgres_available():
        from storage.storage_manager import load_data
        df, _ = load_data()
        if df is not None and not df.empty and "entity_id" in df.columns:
            match = df[df["entity_id"] == entity_id]
            if not match.empty:
                return match.iloc[0].to_dict()
        return None
        
    query = """
        SELECT 
            s.*,
            e.entity_type,
            e.created_at,
            e.converted_at,
            e.completed_client_profile,
            c.dynamic_class,
            clv.predicted_clv_amount_mad,
            clv.predicted_clv_score,
            clv.predicted_clv_segment,
            seg.customer_segment,
            seg.customer_persona
        FROM digital_twin_snapshots s
        LEFT JOIN entities e ON s.entity_id = e.entity_id
        LEFT JOIN (
            SELECT DISTINCT ON (entity_id) entity_id, dynamic_class
            FROM classification_predictions
            ORDER BY entity_id, predicted_at DESC
        ) c ON s.entity_id = c.entity_id
        LEFT JOIN (
            SELECT DISTINCT ON (entity_id) entity_id, predicted_clv_amount_mad, predicted_clv_score, predicted_clv_segment
            FROM clv_predictions
            ORDER BY entity_id, predicted_at DESC
        ) clv ON s.entity_id = clv.entity_id
        LEFT JOIN (
            SELECT DISTINCT ON (entity_id) entity_id, customer_segment, customer_persona
            FROM customer_segments
            ORDER BY entity_id, assigned_at DESC
        ) seg ON s.entity_id = seg.entity_id
        WHERE s.entity_id = %s;
    """
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query, (entity_id,))
            res = cur.fetchone()
            if res:
                return dict(res)
    except Exception as e:
        logger.error(f"Failed to fetch digital twin snapshot for {entity_id}: {e}")
        
    from storage.storage_manager import load_data
    df, _ = load_data()
    if df is not None and not df.empty and "entity_id" in df.columns:
        match = df[df["entity_id"] == entity_id]
        if not match.empty:
            return match.iloc[0].to_dict()
            
    return None


def get_all_digital_twins():
    """Gets all digital twins snapshots."""
    query = "SELECT * FROM digital_twin_snapshots;"
    with get_cursor(commit=False) as cur:
        cur.execute(query)
        return cur.fetchall()


# ============================================================
# 4. Event History Repositories
# ============================================================

def insert_event_history(event_dict):
    """Inserts a new event record into history log."""
    query = """
        INSERT INTO event_history (
            event_id, entity_id, event_type, event_date, old_class, new_class, 
            class_changed, old_entity_type, new_entity_type, prospect_to_client_conversion, 
            completed_client_profile, changed_variables, before_values, after_values, 
            old_clv_amount_mad, new_clv_amount_mad, old_clv_score, new_clv_score, 
            old_clv_segment, new_clv_segment, clv_changed, created_at
        ) VALUES (
            %(event_id)s, %(entity_id)s, %(event_type)s, %(event_date)s, %(old_class)s, %(new_class)s, 
            %(class_changed)s, %(old_entity_type)s, %(new_entity_type)s, %(prospect_to_client_conversion)s, 
            %(completed_client_profile)s, %(changed_variables)s, %(before_values)s, %(after_values)s, 
            %(old_clv_amount_mad)s, %(new_clv_amount_mad)s, %(old_clv_score)s, %(new_clv_score)s, 
            %(old_clv_segment)s, %(new_clv_segment)s, %(clv_changed)s, NOW()
        )
        RETURNING event_id;
    """
    params = dict(event_dict)
    params['changed_variables'] = safe_json(params.get('changed_variables'))
    params['before_values'] = safe_json(params.get('before_values'))
    params['after_values'] = safe_json(params.get('after_values'))
    
    with get_cursor() as cur:
        cur.execute(query, params)
        res = cur.fetchone()
        return res['event_id'] if res else None

def get_event_history(entity_id=None):
    """Retrieves event history for one or all entities."""
    if entity_id:
        query = "SELECT * FROM event_history WHERE entity_id = %s ORDER BY event_date DESC;"
        params = (entity_id,)
    else:
        query = "SELECT * FROM event_history ORDER BY event_date DESC;"
        params = ()
        
    with get_cursor(commit=False) as cur:
        cur.execute(query, params)
        records = cur.fetchall()
        for r in records:
            r['changed_variables'] = safe_parse_json(r['changed_variables'])
            r['before_values'] = safe_parse_json(r['before_values'])
            r['after_values'] = safe_parse_json(r['after_values'])
        return records


# ============================================================
# 5. RFM-ES Score Repositories
# ============================================================

def insert_rfm_es_score(rfm_dict):
    """Inserts a versioned RFM-ES score."""
    query = """
        INSERT INTO rfm_es_scores (
            entity_id, event_id, R_raw, F_raw, M_raw, E_raw, S_raw, 
            rfm_recency_score, rfm_frequency_score, rfm_monetary_score, 
            rfm_engagement_score, rfm_sentiment_score, rfm_score_raw_1_to_5, 
            rfm_score, ahp_weight_R, ahp_weight_F, ahp_weight_M, ahp_weight_E, 
            ahp_weight_S, ahp_group_CR, ahp_group_CI, ahp_expert_count, calculated_at
        ) VALUES (
            %(entity_id)s, %(event_id)s, %(R_raw)s, %(F_raw)s, %(M_raw)s, %(E_raw)s, %(S_raw)s, 
            %(rfm_recency_score)s, %(rfm_frequency_score)s, %(rfm_monetary_score)s, 
            %(rfm_engagement_score)s, %(rfm_sentiment_score)s, %(rfm_score_raw_1_to_5)s, 
            %(rfm_score)s, %(ahp_weight_R)s, %(ahp_weight_F)s, %(ahp_weight_M)s, %(ahp_weight_E)s, 
            %(ahp_weight_S)s, %(ahp_group_CR)s, %(ahp_group_CI)s, %(ahp_expert_count)s, NOW()
        )
        RETURNING id;
    """
    with get_cursor() as cur:
        cur.execute(query, rfm_dict)
        res = cur.fetchone()
        return res['id'] if res else None

def get_latest_rfm_es_score(entity_id):
    """Retrieves the latest score calculation for entity."""
    query = "SELECT * FROM rfm_es_scores WHERE entity_id = %s ORDER BY calculated_at DESC LIMIT 1;"
    with get_cursor(commit=False) as cur:
        cur.execute(query, (entity_id,))
        return cur.fetchone()


# ============================================================
# 6. Classification Prediction Repositories
# ============================================================

def insert_classification_prediction(prediction_dict):
    """Inserts classification prediction historically."""
    query = """
        INSERT INTO classification_predictions (
            entity_id, event_id, dynamic_class, confidence, top_3_probs, 
            model_name, model_version, model_registry_id, predicted_at
        ) VALUES (
            %(entity_id)s, %(event_id)s, %(dynamic_class)s, %(confidence)s, %(top_3_probs)s, 
            %(model_name)s, %(model_version)s, %(model_registry_id)s, NOW()
        )
        RETURNING id;
    """
    params = dict(prediction_dict)
    params['top_3_probs'] = safe_json(params.get('top_3_probs'))
    
    with get_cursor() as cur:
        cur.execute(query, params)
        res = cur.fetchone()
        return res['id'] if res else None

def get_latest_classification_prediction(entity_id):
    """Retrieves the latest classification prediction."""
    query = "SELECT * FROM classification_predictions WHERE entity_id = %s ORDER BY predicted_at DESC LIMIT 1;"
    with get_cursor(commit=False) as cur:
        cur.execute(query, (entity_id,))
        res = cur.fetchone()
        if res:
            res['top_3_probs'] = safe_parse_json(res['top_3_probs'])
        return res


# ============================================================
# 7. CLV Prediction Repositories
# ============================================================

def insert_clv_prediction(clv_dict):
    """Inserts CLV predictions historically."""
    query = """
        INSERT INTO clv_predictions (
            entity_id, event_id, predicted_clv_amount_mad, predicted_clv_score, 
            predicted_clv_segment, clv_model_name, clv_segment_model_name, 
            clv_method_used, ml_predicted_clv_amount_mad, math_clv_amount_mad, 
            clv_segment_prediction_source, clv_segment_confidence, clv_segment_top_3, 
            model_registry_id, predicted_at
        ) VALUES (
            %(entity_id)s, %(event_id)s, %(predicted_clv_amount_mad)s, %(predicted_clv_score)s, 
            %(predicted_clv_segment)s, %(clv_model_name)s, %(clv_segment_model_name)s, 
            %(clv_method_used)s, %(ml_predicted_clv_amount_mad)s, %(math_clv_amount_mad)s, 
            %(clv_segment_prediction_source)s, %(clv_segment_confidence)s, %(clv_segment_top_3)s, 
            %(model_registry_id)s, NOW()
        )
        RETURNING id;
    """
    params = dict(clv_dict)
    params['clv_segment_top_3'] = safe_json(params.get('clv_segment_top_3'))
    
    with get_cursor() as cur:
        cur.execute(query, params)
        res = cur.fetchone()
        return res['id'] if res else None

def get_latest_clv_prediction(entity_id):
    """Gets latest clv predictions."""
    query = "SELECT * FROM clv_predictions WHERE entity_id = %s ORDER BY predicted_at DESC LIMIT 1;"
    with get_cursor(commit=False) as cur:
        cur.execute(query, (entity_id,))
        res = cur.fetchone()
        if res:
            res['clv_segment_top_3'] = safe_parse_json(res['clv_segment_top_3'])
        return res


# ============================================================
# 8. Customer Segment/Persona Repositories
# ============================================================

def insert_customer_segment(segment_dict):
    """Inserts segment tracking record historically."""
    query = """
        INSERT INTO customer_segments (
            entity_id, event_id, customer_segment, customer_persona, 
            persona_description, persona_recommended_action, segmentation_method, 
            ml_cluster_id, ml_cluster_label, cluster_persona, assigned_at
        ) VALUES (
            %(entity_id)s, %(event_id)s, %(customer_segment)s, %(customer_persona)s, 
            %(persona_description)s, %(persona_recommended_action)s, %(segmentation_method)s, 
            %(ml_cluster_id)s, %(ml_cluster_label)s, %(cluster_persona)s, NOW()
        )
        RETURNING id;
    """
    with get_cursor() as cur:
        cur.execute(query, segment_dict)
        res = cur.fetchone()
        return res['id'] if res else None

def get_latest_customer_segment(entity_id):
    """Gets latest segments/personas assigned."""
    query = "SELECT * FROM customer_segments WHERE entity_id = %s ORDER BY assigned_at DESC LIMIT 1;"
    with get_cursor(commit=False) as cur:
        cur.execute(query, (entity_id,))
        return cur.fetchone()


# ============================================================
# 9. Model Registry Repositories
# ============================================================

def register_model(model_dict):
    """Inserts a model registry entry."""
    query = """
        INSERT INTO model_registry (
            model_type, model_name, artifact_path, entity_type_format, 
            rfm_version, selection_metric, feature_count, metrics, export_date, registered_at, is_active
        ) VALUES (
            %(model_type)s, %(model_name)s, %(artifact_path)s, %(entity_type_format)s, 
            %(rfm_version)s, %(selection_metric)s, %(feature_count)s, %(metrics)s, %(export_date)s, NOW(), TRUE
        )
        RETURNING id;
    """
    params = dict(model_dict)
    params['metrics'] = safe_json(params.get('metrics'))
    
    with get_cursor() as cur:
        cur.execute(query, params)
        res = cur.fetchone()
        return res['id'] if res else None

def get_active_model(model_type):
    """Gets active model artifact information."""
    query = "SELECT * FROM model_registry WHERE model_type = %s AND is_active = TRUE ORDER BY registered_at DESC LIMIT 1;"
    with get_cursor(commit=False) as cur:
        cur.execute(query, (model_type,))
        res = cur.fetchone()
        if res:
            res['metrics'] = safe_parse_json(res['metrics'])
        return res


# ============================================================
# 10. Audit Log Repositories
# ============================================================

def insert_audit_log(action_type, details, entity_id=None, event_id=None):
    """Appends an event tracking action into audit logs."""
    query = """
        INSERT INTO audit_logs (
            action_type, entity_id, event_id, details, created_at
        ) VALUES (
            %s, %s, %s, %s, NOW()
        )
        RETURNING id;
    """
    with get_cursor() as cur:
        cur.execute(query, (action_type, entity_id, event_id, safe_json(details)))
        res = cur.fetchone()
        return res['id'] if res else None
