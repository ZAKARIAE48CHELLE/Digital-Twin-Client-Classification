"""
OSMOS Journey Tree Simulator — LLM Journey Scenario Planner (Phase 8.7)
======================================================================
Button-triggered LLM planner proposing structured customer lifecycle scenario plans.

Read-Only Guarantee: Proposes JSON plan ONLY. Zero database writes.
All execution is handled deterministically after admin review and approval.
"""

import logging
from typing import Any, Dict, List, Optional
from llm.llm_client import check_llm_available, generate_json, extract_and_parse_json, generate_text

logger = logging.getLogger("OSMOS_LLM_JOURNEY_PLANNER")


def generate_llm_journey_plan(
    entity_id: str = "P_DEMO_001",
    target_lifecycle: str = "Prospect -> Warm Prospect -> Client -> VIP -> Churn Risk",
) -> Dict[str, Any]:
    """
    OPTIONAL & BUTTON-TRIGGERED ONLY!
    Calls LLM to generate a structured 5-stage or 6-stage journey plan proposal.
    STRICTLY READ-ONLY: Returns JSON dict proposal only. Zero database writes.
    """
    available, reason = check_llm_available()
    if not available:
        logger.info(f"LLM unavailable ({reason}); returning fallback structured journey plan.")
        return get_fallback_llm_journey_plan(entity_id)

    prompt = f"""
You are the OSMOS CRM Journey Scenario Architect.
Propose a structured 5-stage customer lifecycle scenario plan for entity '{entity_id}'.

STRICT CONSTRAINTS:
1. Target Entity ID MUST BE: "{entity_id}"
2. Lifecycle story MUST follow: {target_lifecycle}
3. Allowed event types ONLY:
   - "page_visit", "product_view", "email_open", "email_click", "add_to_cart", "purchase"
   - "complaint", "negative_review", "positive_review", "inactivity_period"
   - "social_positive_mention", "social_negative_mention"
   - "service_recovery_contact", "retention_offer_sent"
4. Purchase events:
   - Initial purchase (Stage 3): 500 to 5000 MAD
   - VIP purchases (Stage 4): 5000 to 20000 MAD
5. Stage 5 (Churn Deterioration) MUST include at least one negative event ("complaint", "negative_review", "inactivity_period", or "social_negative_mention").
6. Timestamps: Use event_offset_days relative to today:
   - Stage 1: -20
   - Stage 2: -14
   - Stage 3: -10
   - Stage 4: -6
   - Stage 5: -1
7. DO NOT include any personal contact info or real email/SMS sending instructions.

Return ONLY valid JSON matching this exact structure:
{{
  "entity_id": "{entity_id}",
  "scenario_name": "Prospect to VIP to Churn Risk",
  "description": "Comprehensive customer lifecycle progression illustrating Digital Twin evolution.",
  "stages": [
    {{
      "stage_order": 1,
      "stage_name": "1. New Prospect Discovery",
      "goal": "Initial exploratory brand discovery",
      "events": [
        {{"event_type": "page_visit", "event_offset_days": -20, "event_value": null}},
        {{"event_type": "product_view", "event_offset_days": -20, "event_value": null}}
      ],
      "expected_state_change": {{
        "entity_type": "Prospect",
        "dynamic_class": "Cold Prospect",
        "segment": "Prospect",
        "persona": "New Explorer"
      }}
    }},
    {{
      "stage_order": 2,
      "stage_name": "2. Warm Prospect Engagement",
      "goal": "Increased engagement prior to purchase",
      "events": [
        {{"event_type": "email_open", "event_offset_days": -14, "event_value": null}},
        {{"event_type": "add_to_cart", "event_offset_days": -14, "event_value": null}}
      ],
      "expected_state_change": {{
        "entity_type": "Prospect",
        "dynamic_class": "Warm Prospect",
        "segment": "Prospect",
        "persona": "New Explorer"
      }}
    }},
    {{
      "stage_order": 3,
      "stage_name": "3. New Client Conversion",
      "goal": "First successful purchase and client conversion",
      "events": [
        {{"event_type": "purchase", "event_offset_days": -10, "event_value": 1800.0}}
      ],
      "expected_state_change": {{
        "entity_type": "Client",
        "dynamic_class": "New Client",
        "segment": "New Customers",
        "persona": "New Explorer"
      }}
    }},
    {{
      "stage_order": 4,
      "stage_name": "4. VIP Client / Premium Loyalist",
      "goal": "High-value order volume and VIP loyalty",
      "events": [
        {{"event_type": "purchase", "event_offset_days": -6, "event_value": 8500.0}},
        {{"event_type": "purchase", "event_offset_days": -5, "event_value": 12000.0}},
        {{"event_type": "positive_review", "event_offset_days": -5, "event_value": null}}
      ],
      "expected_state_change": {{
        "entity_type": "Client",
        "dynamic_class": "VIP Client",
        "segment": "High-Value Loyalists",
        "persona": "Premium Loyalist"
      }}
    }},
    {{
      "stage_order": 5,
      "stage_name": "5. At-Risk Premium Client / Churn Risk",
      "goal": "Service disruption complaint and churn risk spike",
      "events": [
        {{"event_type": "complaint", "event_offset_days": -1, "event_value": null}},
        {{"event_type": "negative_review", "event_offset_days": -1, "event_value": null}}
      ],
      "expected_state_change": {{
        "entity_type": "Client",
        "dynamic_class": "At-Risk Client",
        "segment": "Complaint-Driven Risk Clients",
        "persona": "Frustrated Client"
      }}
    }}
  ]
}}
"""
    try:
        raw = generate_text(prompt, temperature=0.2)
        parsed = extract_and_parse_json(raw)
        if parsed and isinstance(parsed, dict) and "stages" in parsed:
            parsed["entity_id"] = entity_id
            return parsed
    except Exception as e:
        logger.error(f"Failed to generate LLM journey plan: {e}")

    return get_fallback_llm_journey_plan(entity_id)


def get_fallback_llm_journey_plan(entity_id: str = "P_DEMO_001") -> Dict[str, Any]:
    """Returns a valid deterministic fallback proposal when LLM is disabled or offline."""
    return {
        "entity_id": entity_id,
        "scenario_name": "Prospect to VIP to Churn Risk (Deterministic Plan)",
        "description": "Structured 5-stage customer lifecycle scenario generated by OSMOS Journey Planner fallback.",
        "stages": [
            {
                "stage_order": 1,
                "stage_name": "1. New Prospect Discovery",
                "goal": "Initial exploratory brand discovery",
                "events": [
                    {"event_type": "page_visit", "event_offset_days": -20, "event_value": None},
                    {"event_type": "product_view", "event_offset_days": -20, "event_value": None},
                    {"event_type": "email_open", "event_offset_days": -20, "event_value": None},
                ],
                "expected_state_change": {
                    "entity_type": "Prospect",
                    "dynamic_class": "Cold Prospect",
                    "segment": "Prospect",
                    "persona": "New Explorer",
                },
            },
            {
                "stage_order": 2,
                "stage_name": "2. Warm Prospect Engagement",
                "goal": "Increased engagement and cart addition prior to conversion",
                "events": [
                    {"event_type": "product_view", "event_offset_days": -14, "event_value": None},
                    {"event_type": "email_click", "event_offset_days": -14, "event_value": None},
                    {"event_type": "add_to_cart", "event_offset_days": -14, "event_value": None},
                    {"event_type": "social_positive_mention", "event_offset_days": -14, "event_value": None},
                ],
                "expected_state_change": {
                    "entity_type": "Prospect",
                    "dynamic_class": "Warm Prospect",
                    "segment": "Prospect",
                    "persona": "New Explorer",
                },
            },
            {
                "stage_order": 3,
                "stage_name": "3. New Client Conversion",
                "goal": "First purchase completed and conversion to Client",
                "events": [
                    {"event_type": "purchase", "event_offset_days": -10, "event_value": 1800.0},
                ],
                "expected_state_change": {
                    "entity_type": "Client",
                    "dynamic_class": "New Client",
                    "segment": "New Customers",
                    "persona": "New Explorer",
                },
            },
            {
                "stage_order": 4,
                "stage_name": "4. VIP Client / Premium Loyalist",
                "goal": "High-value repeated purchases and positive reviews",
                "events": [
                    {"event_type": "purchase", "event_offset_days": -6, "event_value": 8500.0},
                    {"event_type": "purchase", "event_offset_days": -5, "event_value": 12000.0},
                    {"event_type": "positive_review", "event_offset_days": -5, "event_value": None},
                    {"event_type": "social_positive_mention", "event_offset_days": -5, "event_value": None},
                ],
                "expected_state_change": {
                    "entity_type": "Client",
                    "dynamic_class": "VIP Client",
                    "segment": "High-Value Loyalists",
                    "persona": "Premium Loyalist",
                },
            },
            {
                "stage_order": 5,
                "stage_name": "5. At-Risk Premium Client / Churn Risk",
                "goal": "Complaint filed and sentiment drop creating churn risk",
                "events": [
                    {"event_type": "complaint", "event_offset_days": -1, "event_value": None},
                    {"event_type": "negative_review", "event_offset_days": -1, "event_value": None},
                    {"event_type": "inactivity_period", "event_offset_days": -1, "event_value": None},
                ],
                "expected_state_change": {
                    "entity_type": "Client",
                    "dynamic_class": "At-Risk Client",
                    "segment": "Complaint-Driven Risk Clients",
                    "persona": "Frustrated Client",
                },
            },
        ],
    }
