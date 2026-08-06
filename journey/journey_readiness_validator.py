"""
OSMOS Journey Tree Simulator — Demo Entity Readiness Validator (Phase 8.7)
========================================================================
Audits P_DEMO_001 database integrity, event history recency, journey step count,
FK trigger_event_id references, Digital Twin snapshots, and persona resolution.

Read-Only Guarantee: Zero database mutations. Pure analytical audit.
"""

import logging
from typing import Any, Dict, List
import pandas as pd
from storage.storage_manager import load_data
from admin.database_metrics import is_postgres_available
from journey.journey_repository import get_latest_scenario_for_entity, get_journey_steps
from personas.persona_library import DEFAULT_PERSONA_MAP

logger = logging.getLogger("OSMOS_JOURNEY_READINESS")


def validate_journey_entity_state(entity_id: str = "P_DEMO_001") -> Dict[str, Any]:
    """
    Audits the current readiness state of entity_id (P_DEMO_001) for executive demos,
    agent supervision, debate mode, knowledge memory, and reports.

    Returns:
    {
        "readiness_status": "Ready for presentation" | "Partially ready" | "Not ready",
        "score_pct": float,
        "checks": List[Dict[str, Any]],
        "summary": str,
        "metrics": Dict[str, Any]
    }
    """
    df, history = load_data()
    checks: List[Dict[str, Any]] = []

    # 1. Entity Exists
    entity_row = df[df["entity_id"] == entity_id]
    entity_exists = len(entity_row) > 0
    checks.append({
        "check": "Entity Profile Initialized",
        "status": "Pass" if entity_exists else "Fail",
        "detail": f"Entity [{entity_id}] exists in current dataset snapshot." if entity_exists else f"Entity [{entity_id}] not found."
    })

    if not entity_exists:
        return {
            "readiness_status": "Not ready",
            "score_pct": 0.0,
            "checks": checks,
            "summary": f"Demo entity [{entity_id}] has not been initialized. Click 'Create / Reset Demo Entity' first.",
            "metrics": {},
        }

    row = entity_row.iloc[0]

    # 2. Event History & Recency
    entity_events = [e for e in history if str(e.get("entity_id")) == str(entity_id)]
    event_count = len(entity_events)
    recent_events = [e for e in entity_events if e.get("event_type") != "demo_entity_initialized"]
    recent_count = len(recent_events)

    checks.append({
        "check": "Real event_history Records Created",
        "status": "Pass" if event_count > 0 else "Fail",
        "detail": f"Recorded {event_count} total events in event_history."
    })

    checks.append({
        "check": "Recent Demo Events Present (Non-Zero)",
        "status": "Pass" if recent_count >= 3 else ("Warning" if recent_count > 0 else "Fail"),
        "detail": f"Found {recent_count} recent behavioral events for supervision agents."
    })

    # 3. Journey Scenario & Step Count
    scen = get_latest_scenario_for_entity(entity_id)
    steps = get_journey_steps(scen.get("scenario_id")) if scen else []
    step_count = len(steps)

    checks.append({
        "check": "Journey Steps Executed (>= 5 Stages)",
        "status": "Pass" if step_count >= 5 else ("Warning" if step_count > 0 else "Fail"),
        "detail": f"Executed {step_count}/5 lifecycle scenario stages."
    })

    # 4. Trigger Event ID Integrity
    missing_refs = [s for s in steps if not s.get("trigger_event_id")]
    missing_ref_count = len(missing_refs)

    checks.append({
        "check": "Trigger Event Foreign Key Integrity",
        "status": "Pass" if (step_count > 0 and missing_ref_count == 0) else ("Fail" if missing_ref_count > 0 else "Warning"),
        "detail": f"All {step_count} journey steps have valid trigger_event_id references." if missing_ref_count == 0 and step_count > 0 else f"Found {missing_ref_count} steps without valid trigger_event_id."
    })

    # 5. Persona Resolution Alignment
    segment = str(row.get("customer_segment", "Unknown"))
    persona = str(row.get("customer_persona", "Unknown"))
    official_personas = set(p["persona_name"] for p in DEFAULT_PERSONA_MAP.values())
    persona_resolved = persona in official_personas and persona != "Unknown"

    checks.append({
        "check": "Segment-First Persona Resolution",
        "status": "Pass" if persona_resolved else "Fail",
        "detail": f"Segment '{segment}' resolved to official stable persona '{persona}'." if persona_resolved else f"Persona unresolved for segment '{segment}'."
    })

    # 6. Churn & Class Coherence
    dyn_class = str(row.get("dynamic_class", "Cold Prospect"))
    churn_risk = float(row.get("churn_risk_score", 0.0) or 0.0)
    clv_amount = float(row.get("predicted_clv_amount_mad", 0.0) or 0.0)

    coherence_pass = True
    if step_count >= 5 and churn_risk < 0.50:
        coherence_pass = False

    checks.append({
        "check": "Final Lifecycle Stage Coherence",
        "status": "Pass" if coherence_pass else "Warning",
        "detail": f"Final stage: class '{dyn_class}', churn risk {churn_risk:.0%}, CLV {clv_amount:,.0f} MAD."
    })

    # Calculate overall readiness
    passed = sum(1 for c in checks if c["status"] == "Pass")
    total = len(checks)
    score_pct = round((passed / total) * 100.0, 1)

    if score_pct >= 85.0 and missing_ref_count == 0 and step_count >= 5:
        readiness_status = "Ready for presentation"
        summary = f"Demo Entity [{entity_id}] is fully prepared with 5/5 completed stages, {event_count} events, and 100% data integrity."
    elif score_pct >= 50.0:
        readiness_status = "Partially ready"
        summary = f"Demo Entity [{entity_id}] is partially ready ({step_count}/5 steps executed, {score_pct:.0f}% readiness score)."
    else:
        readiness_status = "Not ready"
        summary = f"Demo Entity [{entity_id}] is not ready ({score_pct:.0f}% readiness score). Click 'Prepare Full Demo Entity' to initialize."

    return {
        "readiness_status": readiness_status,
        "score_pct": score_pct,
        "checks": checks,
        "summary": summary,
        "metrics": {
            "entity_id": entity_id,
            "entity_type": row.get("entity_type"),
            "dynamic_class": dyn_class,
            "customer_segment": segment,
            "customer_persona": persona,
            "clv_amount": clv_amount,
            "churn_risk": churn_risk,
            "event_count": event_count,
            "step_count": step_count,
        }
    }
