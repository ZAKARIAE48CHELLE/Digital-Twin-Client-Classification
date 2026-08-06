"""
OSMOS Journey Tree Simulator — JSON Plan Normalizer & Repair Engine (Phase 8.7)
==============================================================================
Robust JSON repair and normalization module for LLM-proposed journey plans.
Strips markdown code blocks, repairs NULL literals, normalizes event strings,
and guarantees structural consistency before validation.

Read-Only Guarantee: Zero database mutations.
"""

import re
import json
import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger("OSMOS_JOURNEY_NORMALIZER")


def normalize_and_repair_json_plan(raw_input: Any) -> Tuple[Dict[str, Any], List[str]]:
    """
    Parses and repairs raw LLM output into a clean, normalized journey plan dictionary.

    Returns:
    (normalized_plan_dict or None, list_of_repair_warnings)
    """
    repair_warnings: List[str] = []

    if isinstance(raw_input, dict):
        plan_dict = raw_input
    elif isinstance(raw_input, str):
        cleaned_str = raw_input.strip()

        # Remove markdown code fences if present
        if "```" in cleaned_str:
            repair_warnings.append("Stripped markdown code fences from LLM output.")
            cleaned_str = re.sub(r"```(?:json)?", "", cleaned_str).strip()

        # Fix capital NULL or None literals in JSON string
        if re.search(r":\s*NULL\b", cleaned_str, re.IGNORECASE):
            repair_warnings.append("Replaced unquoted NULL/None literals with JSON null.")
            cleaned_str = re.sub(r":\s*NULL\b", ": null", cleaned_str, flags=re.IGNORECASE)
            cleaned_str = re.sub(r":\s*None\b", ": null", cleaned_str, flags=re.IGNORECASE)

        # Attempt JSON parsing
        try:
            plan_dict = json.loads(cleaned_str)
        except json.JSONDecodeError as e:
            # Fallback regex extraction of JSON object
            json_match = re.search(r"(\{.*\})", cleaned_str, re.DOTALL)
            if json_match:
                try:
                    plan_dict = json.loads(json_match.group(1))
                    repair_warnings.append("Extracted JSON object payload via regex match.")
                except Exception:
                    return None, [f"Fatal JSON Decode Error: {e}"]
            else:
                return None, [f"Fatal JSON Decode Error: {e}"]
    else:
        return None, ["Input is neither a JSON string nor a dictionary."]

    if not isinstance(plan_dict, dict):
        return None, ["Parsed JSON payload is not a dictionary object."]

    # Normalize fields
    entity_id = str(plan_dict.get("entity_id", "P_DEMO_001")).strip()
    if entity_id != "P_DEMO_001":
        repair_warnings.append(f"Entity ID '{entity_id}' normalized to 'P_DEMO_001'.")
        entity_id = "P_DEMO_001"

    scen_name = str(plan_dict.get("scenario_name", "Prospect to VIP to Churn Risk")).strip()
    desc = str(plan_dict.get("description", "LLM proposed customer lifecycle journey.")).strip()

    stages_raw = plan_dict.get("stages", [])
    if not isinstance(stages_raw, list):
        return None, ["Plan 'stages' field is not a valid list."]

    normalized_stages = []
    for idx, stage in enumerate(stages_raw, start=1):
        if not isinstance(stage, dict):
            repair_warnings.append(f"Skipped invalid non-dict stage #{idx}.")
            continue

        stage_order = stage.get("stage_order", idx)
        try:
            stage_order = int(stage_order)
        except Exception:
            stage_order = idx

        s_name = str(stage.get("stage_name", f"Stage {idx}")).strip()
        s_goal = str(stage.get("goal", "")).strip()

        events_raw = stage.get("events", [])
        if not isinstance(events_raw, list):
            events_raw = []

        normalized_events = []
        for e_idx, evt in enumerate(events_raw):
            if isinstance(evt, str):
                e_type = evt.strip().lower()
                e_offset = -20 + (idx * 3)
                e_val = None
            elif isinstance(evt, dict):
                e_type = str(evt.get("event_type", "")).strip().lower()
                e_offset = evt.get("event_offset_days", -20 + (idx * 3))
                e_val = evt.get("event_value")
                if e_val in ["NULL", "null", "None", "none", ""]:
                    e_val = None
                elif e_val is not None:
                    try:
                        e_val = float(e_val)
                    except (ValueError, TypeError):
                        e_val = None
                try:
                    e_offset = int(e_offset)
                except Exception:
                    e_offset = -20 + (idx * 3)
            else:
                continue

            if e_type:
                normalized_events.append({
                    "event_type": e_type,
                    "event_offset_days": e_offset,
                    "event_value": e_val,
                })

        state_chg = stage.get("expected_state_change", {})
        if not isinstance(state_chg, dict):
            state_chg = {}

        normalized_stages.append({
            "stage_order": stage_order,
            "stage_name": s_name,
            "goal": s_goal,
            "events": normalized_events,
            "expected_state_change": {
                "entity_type": str(state_chg.get("entity_type", "Prospect" if idx < 3 else "Client")).strip(),
                "dynamic_class": str(state_chg.get("dynamic_class", "Active")).strip(),
                "segment": str(state_chg.get("segment", "Prospect" if idx < 3 else "New Customers")).strip(),
                "persona": str(state_chg.get("persona", "New Explorer" if idx < 3 else "Premium Loyalist")).strip(),
            }
        })

    normalized_plan = {
        "entity_id": entity_id,
        "scenario_name": scen_name,
        "description": desc,
        "stages": normalized_stages,
    }

    return normalized_plan, repair_warnings
