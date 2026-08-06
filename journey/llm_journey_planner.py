"""
OSMOS Journey Tree Simulator — LLM Journey Scenario Planner (Phase 8.7)
======================================================================
Button-triggered LLM planner proposing structured customer lifecycle scenario plans.
Supports iterative plan regeneration with deterministic validation feedback.

Read-Only Guarantee: Proposes JSON plan ONLY. Zero database writes.
All execution is handled deterministically after admin review and approval.
"""

import logging
from typing import Any, Dict, List, Optional
from llm.llm_client import check_llm_available, generate_text, extract_and_parse_json

logger = logging.getLogger("OSMOS_LLM_JOURNEY_PLANNER")


def generate_llm_journey_plan(
    entity_id: str = "P_DEMO_001",
    target_lifecycle: str = "Prospect -> Warm Prospect -> Client -> VIP -> Churn Risk -> Service Recovery",
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
Propose a structured 6-stage customer lifecycle scenario plan for entity '{entity_id}'.

CRITICAL CONSTRAINTS:
1. Target Entity ID MUST BE: "{entity_id}"
2. Lifecycle story MUST follow: {target_lifecycle}
3. Output STRICT JSON ONLY. Do NOT wrap in markdown fences. Do NOT add explanation text outside JSON.
4. Use JSON lowercase `null` ONLY (NEVER use `NULL` or `None`).
5. Allowed event types ONLY:
   - "page_visit", "product_view", "email_open", "email_click", "add_to_cart", "purchase"
   - "complaint", "negative_review", "positive_review", "inactivity_period"
   - "social_positive_mention", "social_negative_mention"
   - "service_recovery_contact", "retention_offer_sent"
6. Stage 3 conversion purchase: 500 to 5000 MAD.
7. Stage 4 VIP purchases: 5000 to 20000 MAD.
8. Stage 5 (Churn Deterioration) MUST include AT LEAST 2 negative signals (e.g. "complaint" and "negative_review").
9. Stage 6 (Service Recovery) MUST simulate retention outreach ("service_recovery_contact", "retention_offer_sent").
10. Event offset days: -20, -14, -10, -6, -1, 0.

Return ONLY valid JSON matching this exact structure:
{{
  "entity_id": "{entity_id}",
  "scenario_name": "Prospect to VIP to Churn Risk & Service Recovery",
  "description": "Comprehensive 6-stage customer lifecycle progression illustrating Digital Twin evolution.",
  "stages": [
    {{
      "stage_order": 1,
      "stage_name": "1. New Prospect Discovery",
      "goal": "Initial exploratory brand discovery",
      "events": [
        {{"event_type": "page_visit", "event_offset_days": -20, "event_value": null}},
        {{"event_type": "product_view", "event_offset_days": -20, "event_value": null}},
        {{"event_type": "email_open", "event_offset_days": -20, "event_value": null}}
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
        {{"event_type": "product_view", "event_offset_days": -14, "event_value": null}},
        {{"event_type": "email_click", "event_offset_days": -14, "event_value": null}},
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
      "goal": "First purchase completed and conversion to Client",
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
      "goal": "Complaint filed and sentiment drop creating churn risk",
      "events": [
        {{"event_type": "complaint", "event_offset_days": -1, "event_value": null}},
        {{"event_type": "negative_review", "event_offset_days": -1, "event_value": null}},
        {{"event_type": "inactivity_period", "event_offset_days": -1, "event_value": null}}
      ],
      "expected_state_change": {{
        "entity_type": "Client",
        "dynamic_class": "At-Risk Client",
        "segment": "Complaint-Driven Risk Clients",
        "persona": "Frustrated Client"
      }}
    }},
    {{
      "stage_order": 6,
      "stage_name": "6. Service Recovery / Retention Simulation",
      "goal": "Retention outreach and commercial recovery gesture",
      "events": [
        {{"event_type": "service_recovery_contact", "event_offset_days": 0, "event_value": null}},
        {{"event_type": "retention_offer_sent", "event_offset_days": 0, "event_value": null}},
        {{"event_type": "email_click", "event_offset_days": 0, "event_value": null}}
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


def regenerate_llm_journey_plan_with_feedback(
    previous_plan: Dict[str, Any],
    validation_result: Dict[str, Any],
    entity_id: str = "P_DEMO_001",
) -> Dict[str, Any]:
    """
    OPTIONAL & BUTTON-TRIGGERED ONLY!
    Passes validation errors and warnings back to the LLM to regenerate an improved plan.
    STRICTLY READ-ONLY: Returns JSON dict proposal only. Zero database writes.
    """
    available, reason = check_llm_available()
    if not available:
        logger.info(f"LLM unavailable ({reason}); returning fallback repaired plan.")
        return get_fallback_llm_journey_plan(entity_id)

    errors_str = "\n".join(f"- {e}" for e in validation_result.get("errors", []))
    warnings_str = "\n".join(f"- {w}" for w in validation_result.get("warnings", []))

    prompt = f"""
You are the OSMOS CRM Journey Scenario Architect.
Regenerate and repair a customer lifecycle scenario proposal for entity '{entity_id}'.

PREVIOUS PROPOSAL VALIDATION FEEDBACK:
ERRORS TO FIX:
{errors_str if errors_str else "None"}

WARNINGS TO ADDRESS:
{warnings_str if warnings_str else "None"}

CRITICAL CONSTRAINTS:
1. Target Entity ID MUST BE: "{entity_id}"
2. Output STRICT JSON ONLY. Do NOT wrap in markdown fences.
3. Use JSON lowercase `null` ONLY (NEVER use `NULL` or `None`).
4. Exactly 6 stages covering New Prospect -> Warm Prospect -> Conversion -> VIP -> Churn Risk -> Service Recovery.
5. Stage 5 MUST contain at least 2 negative signals ("complaint", "negative_review", "inactivity_period").
6. Allowed event types ONLY: "page_visit", "product_view", "email_open", "email_click", "add_to_cart", "purchase", "complaint", "negative_review", "positive_review", "inactivity_period", "social_positive_mention", "social_negative_mention", "service_recovery_contact", "retention_offer_sent".

Return ONLY valid JSON matching the 6-stage format.
"""
    try:
        raw = generate_text(prompt, temperature=0.2)
        parsed = extract_and_parse_json(raw)
        if parsed and isinstance(parsed, dict) and "stages" in parsed:
            parsed["entity_id"] = entity_id
            return parsed
    except Exception as e:
        logger.error(f"Failed to regenerate LLM journey plan with feedback: {e}")

    return get_fallback_llm_journey_plan(entity_id)


def get_fallback_llm_journey_plan(entity_id: str = "P_DEMO_001") -> Dict[str, Any]:
    """Returns a valid deterministic fallback proposal when LLM is disabled or offline."""
    return {
        "entity_id": entity_id,
        "scenario_name": "Prospect to VIP to Churn Risk & Service Recovery (Deterministic Plan)",
        "description": "Structured 6-stage customer lifecycle scenario generated by OSMOS Journey Planner fallback.",
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
            {
                "stage_order": 6,
                "stage_name": "6. Service Recovery / Retention Simulation",
                "goal": "Retention outreach and commercial recovery gesture",
                "events": [
                    {"event_type": "service_recovery_contact", "event_offset_days": 0, "event_value": None},
                    {"event_type": "retention_offer_sent", "event_offset_days": 0, "event_value": None},
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
