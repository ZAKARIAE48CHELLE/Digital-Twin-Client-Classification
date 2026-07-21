import logging
from digital_twin.digital_twin_builder import build_digital_twin_profile
from llm.llm_client import generate_json
from llm.prompt_templates import SYSTEM_PROMPT_ANALYST

logger = logging.getLogger("OSMOS_DIGITAL_TWIN_EXPLAINER")

def explain_risk_level(twin_profile):
    """Generates a rule-based deterministic explanation of the entity's risk level."""
    behavior = twin_profile.get("behavioral_state", {})
    scores = twin_profile.get("scores", {})
    
    recency = behavior.get("recency_days", 0)
    complaints = behavior.get("complaint_count_90d", 0)
    risk_title = scores.get("churn_risk", "Low Risk")
    
    reasons = []
    if recency > 60:
        reasons.append(f"Inactivité prolongée ({recency} jours depuis la dernière visite/achat).")
    if complaints > 0:
        reasons.append(f"Présence de réclamations récentes ({complaints} réclamation(s) sur 90j).")
    if not reasons:
        reasons.append("Activité récente et absence de signaux négatifs enregistrés.")
        
    return {
        "risk_level": risk_title,
        "primary_reasons": reasons,
        "explanation_fr": f"Niveau de risque évalué à '{risk_title}'. Facteurs clés : " + " ".join(reasons),
        "explanation_en": f"Risk level evaluated as '{risk_title}'. Key factors: " + " ".join(reasons)
    }

def explain_value_level(twin_profile):
    """Generates a rule-based deterministic explanation of the entity's customer value level."""
    behavior = twin_profile.get("behavioral_state", {})
    predictions = twin_profile.get("predictions", {})
    
    total_spent = behavior.get("total_spent_90d_mad", 0.0)
    predicted_clv = predictions.get("predicted_clv_amount_mad", 0.0)
    clv_segment = predictions.get("predicted_clv_segment", "Standard")
    
    return {
        "value_segment": clv_segment,
        "total_spent_90d_mad": total_spent,
        "predicted_clv_mad": predicted_clv,
        "explanation_fr": f"Profil de valeur '{clv_segment}' avec une dépense cumulée sur 90j de {total_spent:.2f} MAD et une CLV projetée de {predicted_clv:.2f} MAD.",
        "explanation_en": f"Value profile '{clv_segment}' with 90-day cumulative spend of {total_spent:.2f} MAD and projected CLV of {predicted_clv:.2f} MAD."
    }

def explain_engagement_level(twin_profile):
    """Generates a rule-based deterministic explanation of customer engagement."""
    behavior = twin_profile.get("behavioral_state", {})
    scores = twin_profile.get("scores", {})
    
    visits = behavior.get("visits_30d", 0)
    open_rate = behavior.get("email_open_rate", 0.0)
    eng_title = scores.get("engagement_score", "Moderate Engagement")
    
    return {
        "engagement_level": eng_title,
        "visits_30d": visits,
        "email_open_rate": f"{open_rate*100:.1f}%",
        "explanation_fr": f"Engagement évalué à '{eng_title}' ({visits} visites sur 30 jours, taux d'ouverture email {open_rate*100:.1f}%).",
        "explanation_en": f"Engagement evaluated as '{eng_title}' ({visits} visits in 30 days, email open rate {open_rate*100:.1f}%)."
    }

def explain_recommended_action(twin_profile):
    """Generates a rule-based deterministic marketing action recommendation."""
    persona_ctx = twin_profile.get("persona_context", {})
    scores = twin_profile.get("scores", {})
    
    action_fr = persona_ctx.get("recommended_action_fr") or "Maintenir l'engagement standard."
    action_en = persona_ctx.get("recommended_action_en") or "Maintain standard engagement."
    channel = persona_ctx.get("preferred_channel") or "Email"
    priority = scores.get("decision_priority_score") or "Normal"
    
    return {
        "priority": priority,
        "preferred_channel": channel,
        "recommended_action_fr": action_fr,
        "recommended_action_en": action_en,
        "explanation_fr": f"Action recommandée [{priority}] via {channel} : {action_fr}",
        "explanation_en": f"Recommended action [{priority}] via {channel}: {action_en}"
    }

def explain_digital_twin_state(twin_profile):
    """Combines all deterministic explanations for a unified Digital Twin state analysis."""
    identity = twin_profile.get("core_identity", {})
    e_id = identity.get("entity_id")
    
    return {
        "entity_id": e_id,
        "risk_explanation": explain_risk_level(twin_profile),
        "value_explanation": explain_value_level(twin_profile),
        "engagement_explanation": explain_engagement_level(twin_profile),
        "action_explanation": explain_recommended_action(twin_profile)
    }

def generate_llm_digital_twin_summary(entity_id):
    """
    On-demand LLM summary generator for a Digital Twin profile.
    CRITICAL: This function must only be executed when explicitly triggered by a user button click.
    """
    profile = build_digital_twin_profile(entity_id)
    deterministic_exp = explain_digital_twin_state(profile)
    
    prompt = f"""
    {SYSTEM_PROMPT_ANALYST}

    Please provide a executive cognitive summary of the following Digital Twin Profile:
    
    DIGITAL TWIN PROFILE:
    - Entity ID: {entity_id}
    - Type: {profile['core_identity']['entity_type']}
    - Dynamic Class: {profile['predictions']['dynamic_class']}
    - Segment: {profile['persona_context']['customer_segment']}
    - Matched Persona: {profile['persona_context']['customer_persona']}
    - CLV Amount (MAD): {profile['predictions']['predicted_clv_amount_mad']}
    - Churn Risk: {profile['scores']['churn_risk']}
    - Engagement: {profile['scores']['engagement_score']}
    - Priority: {profile['scores']['decision_priority_score']}
    
    DETERMINISTIC EXPLANATIONS:
    - Risk: {deterministic_exp['risk_explanation']['explanation_fr']}
    - Value: {deterministic_exp['value_explanation']['explanation_fr']}
    - Action: {deterministic_exp['action_explanation']['explanation_fr']}
    
    Respond STRICTLY with a valid JSON matching this schema:
    {{
      "summary_fr": "Résumé exécutif du profil jumeau numérique en Français.",
      "summary_en": "Executive summary of the digital twin profile in English.",
      "current_state_fr": "Analyse de l'état actuel en Français.",
      "current_state_en": "Current state analysis in English.",
      "risk_interpretation_fr": "Interprétation des risques en Français.",
      "risk_interpretation_en": "Risk interpretation in English.",
      "value_interpretation_fr": "Interprétation de la valeur en Français.",
      "value_interpretation_en": "Value interpretation in English.",
      "recommended_action_fr": "Action stratégique recommandée en Français.",
      "recommended_action_en": "Strategic recommended action in English.",
      "admin_guidance_fr": "Directives pratiques pour l'administrateur en Français.",
      "admin_guidance_en": "Actionable guidance for the administrator in English."
    }}
    """
    
    expected_keys = [
        "summary_fr", "summary_en", "current_state_fr", "current_state_en",
        "risk_interpretation_fr", "risk_interpretation_en", "value_interpretation_fr",
        "value_interpretation_en", "recommended_action_fr", "recommended_action_en",
        "admin_guidance_fr", "admin_guidance_en"
    ]
    
    return generate_json(prompt, temperature=0.2, expected_keys=expected_keys)
