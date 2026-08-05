"""
OSMOS Agent Knowledge Base — Decision Memory (Phase 8.5)
=========================================================
Historical decision memory helper retrieving prior agent supervision runs,
approval queue outcomes, and detecting repeated or previously rejected recommendations.

Read-Only Guarantee: Pure analytical inspection. Zero database or DataFrame mutations.
"""

import logging
from typing import Any, Dict, List, Optional
from knowledge.knowledge_schemas import DecisionMemoryItem
from agents.agent_repository import get_agent_runs, get_approval_queue, is_agent_db_available

logger = logging.getLogger("OSMOS_DECISION_MEMORY")


def get_entity_decision_memory(entity_id: str) -> List[DecisionMemoryItem]:
    """Retrieves full decision memory items (runs and approval queue actions) for an entity."""
    if not is_agent_db_available() or not entity_id:
        return []

    items: List[DecisionMemoryItem] = []

    # 1. Fetch Supervision Runs
    runs = get_agent_runs(entity_id=entity_id, limit=20)
    for r in runs:
        items.append(
            DecisionMemoryItem(
                entity_id=entity_id,
                run_id=r.get("run_id"),
                decision_type="Supervision Run",
                status=r.get("global_status", "OK"),
                recommendation=r.get("recommended_next_best_action", ""),
                outcome=f"Storage: {r.get('storage_mode')} | Conf: {float(r.get('confidence_score', 0.8))*100:.0f}%",
                created_at=str(r.get("created_at")),
            )
        )

    # 2. Fetch Approval Queue Items
    appr_items = get_approval_queue(entity_id=entity_id, limit=30)
    for a in appr_items:
        items.append(
            DecisionMemoryItem(
                entity_id=entity_id,
                run_id=a.get("run_id"),
                decision_type="Approval Item",
                status=a.get("status", "Pending"),
                recommendation=a.get("proposed_action_title", ""),
                outcome=a.get("admin_comment") or f"Status: {a.get('status')}",
                created_at=str(a.get("created_at")),
            )
        )

    items.sort(key=lambda x: x.created_at, reverse=True)
    return items


def get_previous_recommendations(entity_id: str) -> List[str]:
    """Retrieves all previous next best actions recommended for an entity."""
    memory = get_entity_decision_memory(entity_id)
    recs = [m.recommendation.strip() for m in memory if m.recommendation and m.recommendation.strip()]
    return list(dict.fromkeys(recs))  # Deduplicate preserving order


def get_rejected_recommendations(entity_id: str) -> List[str]:
    """Retrieves recommendations that were previously Rejected by an administrator."""
    memory = get_entity_decision_memory(entity_id)
    return [m.recommendation.strip() for m in memory if m.status == "Rejected" and m.recommendation]


def get_approved_recommendations(entity_id: str) -> List[str]:
    """Retrieves recommendations that were previously Approved by an administrator."""
    memory = get_entity_decision_memory(entity_id)
    return [m.recommendation.strip() for m in memory if m.status in {"Approved", "Converted to Campaign Draft"} and m.recommendation]


def get_approval_outcomes(entity_id: str) -> Dict[str, Any]:
    """Returns summary stats of approval outcomes for an entity."""
    memory = get_entity_decision_memory(entity_id)
    appr_items = [m for m in memory if m.decision_type == "Approval Item"]

    return {
        "total_approval_items": len(appr_items),
        "pending": sum(1 for m in appr_items if m.status == "Pending"),
        "approved": sum(1 for m in appr_items if m.status == "Approved"),
        "rejected": sum(1 for m in appr_items if m.status == "Rejected"),
        "converted": sum(1 for m in appr_items if m.status == "Converted to Campaign Draft"),
    }


def check_if_action_was_previously_rejected(entity_id: str, proposed_action: str) -> bool:
    """Checks whether a similar proposed action was previously Rejected by an admin."""
    rejected = get_rejected_recommendations(entity_id)
    p_lower = proposed_action.lower()
    for r in rejected:
        if r.lower() in p_lower or p_lower in r.lower():
            return True
    return False


def detect_repeated_recommendation(entity_id: str, proposed_action: str) -> Optional[Dict[str, Any]]:
    """Detects if an action was previously recommended and returns historical details."""
    memory = get_entity_decision_memory(entity_id)
    p_lower = proposed_action.lower()

    for m in memory:
        if m.recommendation and (m.recommendation.lower() in p_lower or p_lower in m.recommendation.lower()):
            return {
                "repeated": True,
                "previous_status": m.status,
                "previous_decision_type": m.decision_type,
                "previous_date": m.created_at,
                "outcome": m.outcome,
            }
    return None


def summarize_decision_history(entity_id: str) -> str:
    """Generates a concise textual overview of an entity's decision memory."""
    memory = get_entity_decision_memory(entity_id)
    if not memory:
        return f"No previous supervision runs or approval decisions recorded for Entity [{entity_id}]."

    outcomes = get_approval_outcomes(entity_id)
    return (
        f"Entity [{entity_id}] Decision History: {len(memory)} total memory entries. "
        f"Approval Queue: {outcomes['approved']} Approved, {outcomes['rejected']} Rejected, "
        f"{outcomes['pending']} Pending."
    )
