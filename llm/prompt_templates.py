JSON_SCHEMA_INSTRUCTIONS = """
You MUST respond with a single valid JSON object containing exactly the following keys:
{
  "summary_fr": "Brief summary in French",
  "summary_en": "Brief summary in English",
  "risk_explanation_fr": "Detailed explanation of risk in French",
  "risk_explanation_en": "Detailed explanation of risk in English",
  "priority": "Low | Medium | High | Critical",
  "recommended_action_fr": "Recommended marketing/operational action in French",
  "recommended_action_en": "Recommended marketing/operational action in English",
  "suggested_channel": "Email | Phone | SMS | Dashboard Follow-up | Manual Review",
  "message_draft_fr": "Draft of a personalized message to the customer in French",
  "message_draft_en": "Draft of a personalized message to the customer in English",
  "admin_guidance_fr": "Guidance for the admin user in French",
  "admin_guidance_en": "Guidance for the admin user in English",
  "confidence": "Low | Medium | High"
}

Do NOT output any markdown tags (like ```json ... ```), extra intro, or trailing text. Output ONLY the JSON block.
"""

def explain_clv_alert_prompt(alert_context):
    return f"""
Analyze the following Customer Lifetime Value (CLV) drop alert:
{alert_context}

{JSON_SCHEMA_INSTRUCTIONS}
"""

def explain_segment_transition_prompt(transition_context):
    return f"""
Analyze the following customer segment cohort transition:
{transition_context}

{JSON_SCHEMA_INSTRUCTIONS}
"""

def explain_prediction_drift_prompt(drift_context):
    return f"""
Analyze the following machine learning model prediction distribution drift report:
{drift_context}

{JSON_SCHEMA_INSTRUCTIONS}
"""

def generate_action_recommendation_prompt(context):
    return f"""
Generate an action recommendation for the customer based on this context:
{context}

{JSON_SCHEMA_INSTRUCTIONS}
"""

def generate_customer_summary_prompt(entity_context):
    return f"""
Analyze the customer's historical profile and evolutionary journey:
{entity_context}

{JSON_SCHEMA_INSTRUCTIONS}
"""

def generate_marketing_message_prompt(context):
    return f"""
Generate a highly targeted, personalized marketing message draft:
{context}

{JSON_SCHEMA_INSTRUCTIONS}
"""
