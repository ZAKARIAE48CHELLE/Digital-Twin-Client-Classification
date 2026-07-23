-- ============================================================
-- OSMOS Database Schema
-- ============================================================

-- A. Entities
CREATE TABLE IF NOT EXISTS entities (
    entity_id VARCHAR(50) PRIMARY KEY,
    entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('Client', 'Prospect')),
    original_entity_type VARCHAR(20) CHECK (original_entity_type IN ('Client', 'Prospect', NULL)),
    created_at VARCHAR(50),
    converted_at VARCHAR(50),
    conversion_event_id VARCHAR(50),
    completed_client_profile BOOLEAN,
    region VARCHAR(100),
    source_channel VARCHAR(100),
    segment VARCHAR(100),
    persona VARCHAR(100),
    age_group VARCHAR(20),
    preferred_device VARCHAR(50),
    preferred_category VARCHAR(100),
    marketing_consent BOOLEAN,
    price_sensitivity NUMERIC(5, 4),
    income_power_score NUMERIC(5, 4),
    initial_interest_score NUMERIC(5, 4),
    basic_profile_score NUMERIC(5, 4) DEFAULT 0.5,
    created_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- B. Customer Profiles
-- Note: This table contains personal data (PII). Encryption and strict access control are required in production.
CREATE TABLE IF NOT EXISTS customer_profiles (
    entity_id VARCHAR(50) PRIMARY KEY REFERENCES entities(entity_id) ON DELETE CASCADE,
    age INTEGER,
    sex VARCHAR(20),
    email VARCHAR(255),
    customer_type VARCHAR(20) CHECK (customer_type IN ('B2C', 'B2B', NULL)),
    household_size INTEGER,
    phone_number VARCHAR(50),
    company_name VARCHAR(255),
    job_title VARCHAR(255),
    city VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE customer_profiles IS 'Contains personal data. Encryption and access controls are required in production deployments.';

-- C. Digital Twin Snapshots
CREATE TABLE IF NOT EXISTS digital_twin_snapshots (
    entity_id VARCHAR(50) PRIMARY KEY REFERENCES entities(entity_id) ON DELETE CASCADE,
    snapshot_date VARCHAR(50),
    recency_days NUMERIC(10, 2),
    visits_30d NUMERIC(10, 2),
    product_views_30d NUMERIC(10, 2),
    cart_additions_30d NUMERIC(10, 2),
    purchases_90d NUMERIC(10, 2),
    total_spent_90d_mad NUMERIC(12, 2),
    avg_order_value_mad NUMERIC(12, 2),
    email_open_rate NUMERIC(5, 4),
    email_click_rate NUMERIC(5, 4),
    complaint_count_90d NUMERIC(10, 2),
    review_score_avg NUMERIC(3, 2),
    social_mentions_30d NUMERIC(10, 2),
    social_sentiment_avg NUMERIC(5, 4),
    conversion_probability NUMERIC(5, 4),
    churn_risk_score NUMERIC(5, 4),
    rfm_score NUMERIC(5, 4),
    behavioral_engagement_score NUMERIC(5, 4),
    predictive_value_score NUMERIC(5, 4),
    decision_priority_score NUMERIC(5, 4),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- D. Event History
CREATE TABLE IF NOT EXISTS event_history (
    event_id VARCHAR(50) PRIMARY KEY,
    entity_id VARCHAR(50) NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    old_class VARCHAR(100),
    new_class VARCHAR(100),
    class_changed BOOLEAN,
    old_entity_type VARCHAR(20),
    new_entity_type VARCHAR(20),
    prospect_to_client_conversion BOOLEAN,
    completed_client_profile BOOLEAN,
    changed_variables JSONB,
    before_values JSONB,
    after_values JSONB,
    old_clv_amount_mad NUMERIC(12, 2),
    new_clv_amount_mad NUMERIC(12, 2),
    old_clv_score NUMERIC(6, 2),
    new_clv_score NUMERIC(6, 2),
    old_clv_segment VARCHAR(100),
    new_clv_segment VARCHAR(100),
    clv_changed BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_event_history_entity_id ON event_history(entity_id);
CREATE INDEX IF NOT EXISTS idx_event_history_event_date ON event_history(event_date);
CREATE INDEX IF NOT EXISTS idx_event_history_event_type ON event_history(event_type);

-- E. RFM-ES Scores (Historical/Versioned)
CREATE TABLE IF NOT EXISTS rfm_es_scores (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(50) NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    event_id VARCHAR(50) REFERENCES event_history(event_id) ON DELETE SET NULL,
    R_raw NUMERIC(12, 4),
    F_raw NUMERIC(12, 4),
    M_raw NUMERIC(12, 4),
    E_raw NUMERIC(12, 4),
    S_raw NUMERIC(12, 4),
    rfm_recency_score INTEGER,
    rfm_frequency_score INTEGER,
    rfm_monetary_score INTEGER,
    rfm_engagement_score INTEGER,
    rfm_sentiment_score INTEGER,
    rfm_score_raw_1_to_5 NUMERIC(6, 4),
    rfm_score NUMERIC(5, 4),
    ahp_weight_R NUMERIC(6, 5),
    ahp_weight_F NUMERIC(6, 5),
    ahp_weight_M NUMERIC(6, 5),
    ahp_weight_E NUMERIC(6, 5),
    ahp_weight_S NUMERIC(6, 5),
    ahp_group_CR NUMERIC(8, 6),
    ahp_group_CI NUMERIC(8, 6),
    ahp_expert_count INTEGER,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rfm_es_scores_entity_id ON rfm_es_scores(entity_id);

-- I. Model Registry
CREATE TABLE IF NOT EXISTS model_registry (
    id SERIAL PRIMARY KEY,
    model_type VARCHAR(50) NOT NULL, -- 'classification', 'clv_amount', 'clv_segment', etc.
    model_name VARCHAR(100) NOT NULL,
    artifact_path VARCHAR(500),
    entity_type_format VARCHAR(50),
    rfm_version VARCHAR(100),
    selection_metric VARCHAR(100),
    feature_count INTEGER,
    metrics JSONB,
    export_date VARCHAR(50),
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- F. Classification Predictions (Historical/Versioned)
CREATE TABLE IF NOT EXISTS classification_predictions (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(50) NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    event_id VARCHAR(50) REFERENCES event_history(event_id) ON DELETE SET NULL,
    dynamic_class VARCHAR(100) NOT NULL,
    confidence NUMERIC(5, 4),
    top_3_probs JSONB,
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    model_registry_id INTEGER REFERENCES model_registry(id) ON DELETE SET NULL,
    predicted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_class_pred_entity_id ON classification_predictions(entity_id);
CREATE INDEX IF NOT EXISTS idx_class_pred_predicted_at ON classification_predictions(predicted_at);
CREATE INDEX IF NOT EXISTS idx_class_pred_dynamic_class ON classification_predictions(dynamic_class);

-- G. CLV Predictions (Historical/Versioned)
CREATE TABLE IF NOT EXISTS clv_predictions (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(50) NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    event_id VARCHAR(50) REFERENCES event_history(event_id) ON DELETE SET NULL,
    predicted_clv_amount_mad NUMERIC(12, 2),
    predicted_clv_score NUMERIC(6, 2),
    predicted_clv_segment VARCHAR(100),
    clv_model_name VARCHAR(100),
    clv_segment_model_name VARCHAR(100),
    clv_method_used VARCHAR(100),
    ml_predicted_clv_amount_mad NUMERIC(12, 2),
    math_clv_amount_mad NUMERIC(12, 2),
    clv_segment_prediction_source VARCHAR(100),
    clv_segment_confidence NUMERIC(5, 4),
    clv_segment_top_3 JSONB,
    model_registry_id INTEGER REFERENCES model_registry(id) ON DELETE SET NULL,
    predicted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clv_pred_entity_id ON clv_predictions(entity_id);
CREATE INDEX IF NOT EXISTS idx_clv_pred_predicted_at ON clv_predictions(predicted_at);
CREATE INDEX IF NOT EXISTS idx_clv_pred_segment ON clv_predictions(predicted_clv_segment);

-- H. Customer Segments & Personas (Historical/Versioned)
CREATE TABLE IF NOT EXISTS customer_segments (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(50) NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    event_id VARCHAR(50) REFERENCES event_history(event_id) ON DELETE SET NULL,
    customer_segment VARCHAR(100),
    customer_persona VARCHAR(100),
    persona_description TEXT,
    persona_recommended_action TEXT,
    segmentation_method VARCHAR(100),
    ml_cluster_id INTEGER,
    ml_cluster_label VARCHAR(100),
    cluster_persona VARCHAR(100),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cust_segments_entity_id ON customer_segments(entity_id);

-- J. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(50),
    event_id VARCHAR(50),
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- K. LLM Action Recommendations
CREATE TABLE IF NOT EXISTS llm_action_recommendations (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(50) REFERENCES entities(entity_id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    alert_source TEXT,
    alert_level TEXT,
    summary_fr TEXT,
    summary_en TEXT,
    risk_explanation_fr TEXT,
    risk_explanation_en TEXT,
    priority TEXT,
    recommended_action_fr TEXT,
    recommended_action_en TEXT,
    suggested_channel TEXT,
    message_draft_fr TEXT,
    message_draft_en TEXT,
    admin_guidance_fr TEXT,
    admin_guidance_en TEXT,
    confidence TEXT,
    status TEXT DEFAULT 'Pending' CHECK (status IN ('Pending', 'In Progress', 'Resolved', 'Ignored')),
    llm_model TEXT,
    llm_provider TEXT,
    input_context JSONB,
    raw_llm_output JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_rec_entity_id ON llm_action_recommendations(entity_id);
CREATE INDEX IF NOT EXISTS idx_llm_rec_alert_type ON llm_action_recommendations(alert_type);
CREATE INDEX IF NOT EXISTS idx_llm_rec_alert_level ON llm_action_recommendations(alert_level);
CREATE INDEX IF NOT EXISTS idx_llm_rec_priority ON llm_action_recommendations(priority);
CREATE INDEX IF NOT EXISTS idx_llm_rec_status ON llm_action_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_llm_rec_created_at ON llm_action_recommendations(created_at);

-- L. Persona Library
CREATE TABLE IF NOT EXISTS persona_library (
    persona_id SERIAL PRIMARY KEY,
    segment_name TEXT UNIQUE NOT NULL,
    persona_name TEXT NOT NULL,
    description_fr TEXT,
    description_en TEXT,
    behavior_profile_fr TEXT,
    behavior_profile_en TEXT,
    value_profile_fr TEXT,
    value_profile_en TEXT,
    risk_profile_fr TEXT,
    risk_profile_en TEXT,
    recommended_action_fr TEXT,
    recommended_action_en TEXT,
    preferred_channel TEXT,
    priority_level TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_persona_lib_segment ON persona_library(segment_name);
CREATE INDEX IF NOT EXISTS idx_persona_lib_persona ON persona_library(persona_name);
CREATE INDEX IF NOT EXISTS idx_persona_lib_priority ON persona_library(priority_level);
CREATE INDEX IF NOT EXISTS idx_persona_lib_active ON persona_library(is_active);

-- M. Campaign Dispatches
CREATE TABLE IF NOT EXISTS campaign_dispatches (
    campaign_id SERIAL PRIMARY KEY,
    recommendation_id INTEGER NULL REFERENCES llm_action_recommendations(id) ON DELETE SET NULL,
    entity_id TEXT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    campaign_type TEXT NOT NULL,
    campaign_channel TEXT,
    campaign_title TEXT,
    campaign_message_fr TEXT,
    campaign_message_en TEXT,
    action_source TEXT,
    priority TEXT,
    status TEXT DEFAULT 'Draft' CHECK (status IN ('Draft', 'Approved', 'Simulated Dispatch', 'Responded', 'No Response', 'Cancelled')),
    created_by TEXT DEFAULT 'admin',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    dispatched_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_camp_disp_entity_id ON campaign_dispatches(entity_id);
CREATE INDEX IF NOT EXISTS idx_camp_disp_rec_id ON campaign_dispatches(recommendation_id);
CREATE INDEX IF NOT EXISTS idx_camp_disp_type ON campaign_dispatches(campaign_type);
CREATE INDEX IF NOT EXISTS idx_camp_disp_channel ON campaign_dispatches(campaign_channel);
CREATE INDEX IF NOT EXISTS idx_camp_disp_priority ON campaign_dispatches(priority);
CREATE INDEX IF NOT EXISTS idx_camp_disp_status ON campaign_dispatches(status);
CREATE INDEX IF NOT EXISTS idx_camp_disp_dispatched_at ON campaign_dispatches(dispatched_at);
CREATE INDEX IF NOT EXISTS idx_camp_disp_created_at ON campaign_dispatches(created_at);

-- N. Campaign Responses
CREATE TABLE IF NOT EXISTS campaign_responses (
    response_id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaign_dispatches(campaign_id) ON DELETE CASCADE,
    entity_id TEXT REFERENCES entities(entity_id) ON DELETE CASCADE,
    response_type TEXT CHECK (response_type IN ('Opened', 'Clicked', 'Purchased', 'Ignored', 'Unsubscribed', 'Complained', 'Positive Feedback', 'Negative Feedback')),
    response_score NUMERIC(5, 4),
    response_event_id TEXT NULL REFERENCES event_history(event_id) ON DELETE SET NULL,
    response_details JSONB,
    simulated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_camp_resp_campaign_id ON campaign_responses(campaign_id);
CREATE INDEX IF NOT EXISTS idx_camp_resp_entity_id ON campaign_responses(entity_id);
CREATE INDEX IF NOT EXISTS idx_camp_resp_type ON campaign_responses(response_type);
CREATE INDEX IF NOT EXISTS idx_camp_resp_simulated_at ON campaign_responses(simulated_at);

-- O. Digital Twin Journey Scenarios
CREATE TABLE IF NOT EXISTS journey_scenarios (
    scenario_id SERIAL PRIMARY KEY,
    scenario_name TEXT NOT NULL,
    description TEXT,
    entity_id TEXT,
    status TEXT DEFAULT 'Draft' CHECK (status IN ('Draft', 'Running', 'Completed', 'Failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_j_scen_entity_id ON journey_scenarios(entity_id);
CREATE INDEX IF NOT EXISTS idx_j_scen_status ON journey_scenarios(status);

-- P. Digital Twin Journey Steps
CREATE TABLE IF NOT EXISTS journey_steps (
    step_id SERIAL PRIMARY KEY,
    scenario_id INTEGER REFERENCES journey_scenarios(scenario_id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    entity_id TEXT REFERENCES entities(entity_id) ON DELETE CASCADE,
    stage_name TEXT,
    trigger_event_type TEXT,
    trigger_event_id TEXT NULL REFERENCES event_history(event_id) ON DELETE SET NULL,
    before_dynamic_class TEXT,
    after_dynamic_class TEXT,
    before_segment TEXT,
    after_segment TEXT,
    before_persona TEXT,
    after_persona TEXT,
    before_clv_amount NUMERIC(12, 2),
    after_clv_amount NUMERIC(12, 2),
    before_rfm_score NUMERIC(5, 4),
    after_rfm_score NUMERIC(5, 4),
    before_churn_risk NUMERIC(5, 4),
    after_churn_risk NUMERIC(5, 4),
    llm_explanation_fr TEXT,
    llm_explanation_en TEXT,
    llm_recommendation_fr TEXT,
    llm_recommendation_en TEXT,
    node_status TEXT DEFAULT 'Completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_j_steps_scenario_id ON journey_steps(scenario_id);
CREATE INDEX IF NOT EXISTS idx_j_steps_entity_id ON journey_steps(entity_id);
CREATE INDEX IF NOT EXISTS idx_j_steps_stage_name ON journey_steps(stage_name);
CREATE INDEX IF NOT EXISTS idx_j_steps_step_order ON journey_steps(step_order);




