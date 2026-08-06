"""
OSMOS Journey Tree Simulator — LLM Journey Plan Validator & Quality Scorer (Phase 8.7)
====================================================================================
Deterministic validator & scoring engine evaluating LLM-proposed journey plans.
Includes automatic normalizer/repair execution, 14 validation rules, quality scoring (0-100),
and quality labeling ("Excellent", "Acceptable", "Weak", "Invalid").

Read-Only Guarantee: Zero database mutations.
"""

import logging
from typing import Any, Dict, List
from personas.persona_library import DEFAULT_PERSONA_MAP
from journey.journey_plan_normalizer import normalize_and_repair_json_plan

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


def validate_llm_journey_plan(raw_plan: Any, target_entity_id: str = "P_DEMO_001") -> Dict[str, Any]:
    """
    Normalizes, repairs, and evaluates an LLM-proposed journey plan against 14 strict rules.
    Computes quality score (0-100) and quality label ("Excellent", "Acceptable", "Weak", "Invalid").

    Returns:
    {
        "is_valid": bool,
        "errors": List[str],
        "warnings": List[str],
        "repair_warnings": List[str],
        "quality_score": float,
        "quality_label": str,
        "normalized_plan": Dict[str, Any] or None
    }
    """
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Normalize and repair raw JSON input
    normalized_plan, repair_warnings = normalize_and_repair_json_plan(raw_plan)
    warnings.extend(repair_warnings)

    if not normalized_plan:
        return {
            "is_valid": False,
            "errors": ["Failed to decode or parse LLM journey plan JSON structure."] + repair_warnings,
            "warnings": [],
            "repair_warnings": repair_warnings,
            "quality_score": 0.0,
            "quality_label": "Invalid",
            "normalized_plan": None,
        }

    # Target entity check
    plan_entity = normalized_plan.get("entity_id", target_entity_id)
    if plan_entity != target_entity_id:
        errors.append(f"Plan targets entity '{plan_entity}' but must target '{target_entity_id}'.")

    stages = normalized_plan.get("stages", [])
    stage_count = len(stages)

    if stage_count < 5 or stage_count > 6:
        errors.append(f"Plan has {stage_count} stages; required stage count is between 5 and 6.")

    official_personas = set(p["persona_name"] for p in DEFAULT_PERSONA_MAP.values())

    purchase_occurred = False
    converted_to_client = False
    churn_stage_found = False
    negative_event_count_in_churn = 0
    vip_high_val_purchase = False
    recovery_stage_present = False
    recent_offset_found = False

    previous_offset = -999

    for idx, stage in enumerate(stages, start=1):
        stage_order = stage.get("stage_order", idx)
        stage_name = stage.get("stage_name", f"Stage {idx}")
        events = stage.get("events", [])

        if stage_order != idx:
            warnings.append(f"Stage #{idx} order '{stage_order}' normalized to {idx}.")

        if not events:
            errors.append(f"Stage #{idx} ('{stage_name}') must contain at least one event.")
            continue

        for e_idx, evt in enumerate(events):
            evt_type = evt.get("event_type")
            evt_offset = evt.get("event_offset_days", -20 + (idx * 3))
            evt_val = evt.get("event_value")

            if evt_type not in ALLOWED_EVENT_TYPES:
                errors.append(f"Stage #{idx} contains unsupported event type '{evt_type}'.")

            if evt_type in PURCHASE_EVENTS:
                purchase_occurred = True
                if idx < 3:
                    errors.append(f"Purchase event in Stage #{idx} ('{stage_name}') cannot occur before conversion stage (Stage 3+).")
                if idx == 4 and evt_val and float(evt_val) >= 5000.0:
                    vip_high_val_purchase = True

            if evt_offset and evt_offset >= -3:
                recent_offset_found = True

            if evt_offset and evt_offset < previous_offset:
                warnings.append(f"Stage #{idx} event offset {evt_offset}d is earlier than previous offset {previous_offset}d.")
            if evt_offset:
                previous_offset = evt_offset

        state_change = stage.get("expected_state_change", {})
        target_entity_type = state_change.get("entity_type", "Prospect" if idx < 3 else "Client")
        target_persona = state_change.get("persona")

        if target_entity_type == "Client":
            converted_to_client = True

        if target_persona and target_persona not in official_personas:
            warnings.append(f"Stage #{idx} expected persona '{target_persona}' is not in official persona library.")

        if idx == 5:
            churn_stage_found = True
            negative_event_count_in_churn = sum(1 for e in events if e.get("event_type") in NEGATIVE_EVENTS)

        if idx == 6 or "recovery" in stage_name.lower() or "retention" in stage_name.lower():
            recovery_stage_present = True

    if converted_to_client and not purchase_occurred:
        errors.append("Prospect to Client conversion specified in plan, but no purchase event exists in stages.")

    if churn_stage_found and negative_event_count_in_churn == 0:
        errors.append("Stage 5 (Churn Deterioration) must include at least one negative signal (complaint, negative_review, inactivity_period, social_negative_mention).")
    elif churn_stage_found and negative_event_count_in_churn < 2:
        warnings.append("Stage 5 (Churn Deterioration) has only 1 negative signal; adding a 2nd negative signal (e.g. negative_review + inactivity_period) is recommended.")

    is_valid = len(errors) == 0

    # 4. Plan Quality Scoring (0 - 100)
    if not is_valid:
        quality_score = 0.0
        quality_label = "Invalid"
    else:
        score = 65.0  # Base passing score for valid structure

        if recovery_stage_present or stage_count == 6:
            score += 10.0
        if vip_high_val_purchase:
            score += 10.0
        if negative_event_count_in_churn >= 2:
            score += 10.0
        if recent_offset_found:
            score += 5.0

        # Deductions for warnings
        score -= len(warnings) * 4.0
        quality_score = max(40.0, min(100.0, score))

        if quality_score >= 85.0:
            quality_label = "Excellent"
        elif quality_score >= 65.0:
            quality_label = "Acceptable"
        else:
            quality_label = "Weak"

    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "repair_warnings": repair_warnings,
        "quality_score": round(quality_score, 1),
        "quality_label": quality_label,
        "normalized_plan": normalized_plan if is_valid else None,
    }
