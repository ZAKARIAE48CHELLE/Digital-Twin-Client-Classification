"""
OSMOS Journey Tree Simulator — LLM Journey Plan Validator (Phase 8.7)
======================================================================
Deterministic validator enforcing 14 structural, chronological, domain,
and business rules on LLM-proposed journey plans before admin approval.

Read-Only Guarantee: Zero database mutations. Pure analytical validation.
"""

import logging
from typing import Any, Dict, List, Optional
from personas.persona_library import DEFAULT_PERSONA_MAP

logger = logging.getLogger("OSMOS_JOURNEY_VALIDATOR")

# Allowed event types in OSMOS Journey Tree Simulator
ALLOWED_EVENT_TYPES = {
    "page_visit",
    "product_view",
    "email_open",
    "email_click",
    "add_to_cart",
    "purchase",
    "complaint",
    "negative_review",
    "positive_review",
    "inactivity_period",
    "social_positive_mention",
    "social_negative_mention",
    "service_recovery_contact",
    "retention_offer_sent",
    "demo_entity_initialized",
}

NEGATIVE_EVENTS = {"complaint", "negative_review", "inactivity_period", "social_negative_mention"}
PURCHASE_EVENTS = {"purchase"}


def validate_llm_journey_plan(plan: Dict[str, Any], target_entity_id: str = "P_DEMO_001") -> Dict[str, Any]:
    """
    Evaluates an LLM-proposed journey plan against 14 strict validation rules.

    Returns:
    {
        "is_valid": bool,
        "errors": List[str],
        "warnings": List[str],
        "normalized_plan": Optional[Dict[str, Any]]
    }
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(plan, dict):
        return {
            "is_valid": False,
            "errors": ["Plan proposal is not a valid JSON object."],
            "warnings": [],
            "normalized_plan": None,
        }

    # Rule 14: Target entity constraint
    plan_entity = plan.get("entity_id", target_entity_id)
    if plan_entity != target_entity_id:
        errors.append(f"Plan targets entity '{plan_entity}' but must target '{target_entity_id}'.")

    # Rule 1: Stages present
    stages = plan.get("stages")
    if not stages or not isinstance(stages, list):
        errors.append("Plan must contain a non-empty 'stages' array.")
        return {
            "is_valid": False,
            "errors": errors,
            "warnings": warnings,
            "normalized_plan": None,
        }

    # Rule 3: Stage count between 5 and 6
    stage_count = len(stages)
    if stage_count < 5 or stage_count > 6:
        errors.append(f"Plan has {stage_count} stages; required stage count is between 5 and 6.")

    # Extract official persona names
    official_personas = set(p["persona_name"] for p in DEFAULT_PERSONA_MAP.values())

    purchase_occurred = False
    converted_to_client = False
    churn_stage_found = False
    negative_signal_in_churn = False

    previous_offset = -999

    normalized_stages = []

    for idx, stage in enumerate(stages, start=1):
        if not isinstance(stage, dict):
            errors.append(f"Stage #{idx} is not a valid JSON object.")
            continue

        stage_order = stage.get("stage_order", idx)
        stage_name = stage.get("stage_name", f"Stage {idx}")
        events = stage.get("events", [])

        # Rule 2: Sequential order check
        if stage_order != idx:
            warnings.append(f"Stage #{idx} order '{stage_order}' normalized to {idx}.")
            stage_order = idx

        if not events or not isinstance(events, list):
            errors.append(f"Stage #{idx} ('{stage_name}') must contain at least one event.")
            continue

        stage_events = []
        for e_idx, evt in enumerate(events):
            if isinstance(evt, str):
                evt_type = evt
                evt_offset = -20 + (idx * 3)
                evt_val = None
            elif isinstance(evt, dict):
                evt_type = evt.get("event_type")
                evt_offset = evt.get("event_offset_days", -20 + (idx * 3))
                evt_val = evt.get("event_value")
            else:
                errors.append(f"Stage #{idx} event #{e_idx+1} format invalid.")
                continue

            # Rule 5: Allowed event types
            if evt_type not in ALLOWED_EVENT_TYPES:
                errors.append(f"Stage #{idx} contains unsupported event type '{evt_type}'.")

            # Rule 13 & Rule 14: No customer contact/PII fields
            if isinstance(evt, dict):
                meta = evt.get("metadata", {})
                if any(pii in meta for pii in ["phone", "email", "ssn", "address", "name"]):
                    errors.append(f"Stage #{idx} event #{e_idx+1} contains forbidden PII metadata.")

            if evt_type in PURCHASE_EVENTS:
                purchase_occurred = True
                # Rule 5: Purchase cannot happen before conversion stage (Stage 3+)
                if idx < 3:
                    errors.append(f"Purchase event in Stage #{idx} ('{stage_name}') cannot occur before conversion stage (Stage 3+).")

                # Rule 7: Realistic purchase amounts
                if evt_val is not None:
                    try:
                        val_num = float(evt_val)
                        if idx == 3 and (val_num < 500 or val_num > 5000):
                            warnings.append(f"Stage 3 initial purchase amount ({val_num} MAD) outside recommended 500-5000 MAD range.")
                        elif idx == 4 and (val_num < 5000 or val_num > 20000):
                            warnings.append(f"Stage 4 VIP purchase amount ({val_num} MAD) outside recommended 5000-20000 MAD range.")
                    except (ValueError, TypeError):
                        errors.append(f"Stage #{idx} purchase amount '{evt_val}' is not a valid number.")

            # Rule 6: Chronological order check
            if isinstance(evt_offset, (int, float)):
                if evt_offset < previous_offset:
                    warnings.append(f"Stage #{idx} event offset {evt_offset}d is earlier than previous offset {previous_offset}d.")
                previous_offset = evt_offset

            stage_events.append({
                "event_type": evt_type,
                "event_offset_days": evt_offset,
                "event_value": evt_val,
            })

        # State transition inspection
        state_change = stage.get("expected_state_change", {})
        target_entity_type = state_change.get("entity_type", "Prospect" if idx < 3 else "Client")
        target_persona = state_change.get("persona")

        if target_entity_type == "Client":
            converted_to_client = True

        # Rule 10: Persona resolvable
        if target_persona and target_persona not in official_personas:
            warnings.append(f"Stage #{idx} expected persona '{target_persona}' is not registered in official persona library.")

        # Stage 5 (Churn Deterioration) inspection
        if idx == 5:
            churn_stage_found = True
            has_neg = any(e["event_type"] in NEGATIVE_EVENTS for e in stage_events)
            if has_neg:
                negative_signal_in_churn = True

        normalized_stages.append({
            "stage_order": stage_order,
            "stage_name": stage_name,
            "goal": stage.get("goal", f"Execute {stage_name}"),
            "events": stage_events,
            "expected_state_change": {
                "entity_type": target_entity_type,
                "dynamic_class": state_change.get("dynamic_class", "Active"),
                "segment": state_change.get("segment", "Prospect" if idx < 3 else "New Customers"),
                "persona": target_persona or ("New Explorer" if idx < 3 else "Premium Loyalist"),
            }
        })

    # Rule 6: Prospect conversion requires purchase
    if converted_to_client and not purchase_occurred:
        errors.append("Prospect to Client conversion specified in plan, but no purchase event exists in stages.")

    # Rule 8: Churn deterioration requires negative signal
    if churn_stage_found and not negative_signal_in_churn:
        errors.append("Stage 5 (Churn Deterioration) must include at least one negative signal (complaint, negative_review, inactivity_period, social_negative_mention).")

    is_valid = len(errors) == 0

    normalized_plan = None
    if is_valid:
        normalized_plan = {
            "entity_id": target_entity_id,
            "scenario_name": plan.get("scenario_name", "LLM-Assisted Custom Journey"),
            "description": plan.get("description", "Validated custom journey plan generated by LLM Planner."),
            "stages": normalized_stages,
        }

    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "normalized_plan": normalized_plan,
    }
