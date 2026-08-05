"""
OSMOS Multi-Agent Supervision Layer — Agent Repository (Phase 8.3)
===================================================================
Database persistence repository for saving multi-agent supervision runs,
specialized agent outputs, and managing the Human Approval Queue.

Read-Only Guarantee:
This module ONLY writes to agent_runs, agent_outputs, and agent_approval_queue.
It NEVER alters core customer data, CLV, RFM, event history, or persona models.
"""

import logging
from typing import Any, Dict, List, Optional
import psycopg2.extras

from storage.storage_manager import get_storage_backend
from admin.database_metrics import is_postgres_available
from agents.agent_schemas import OrchestratorOutput, AgentOutput

logger = logging.getLogger("OSMOS_AGENT_REPOSITORY")


def is_agent_db_available() -> bool:
    """Checks whether PostgreSQL is active and available for agent memory operations."""
    return get_storage_backend() == "postgres" and is_postgres_available()


def save_agent_run(
    orchestrator_output: OrchestratorOutput,
    selected_agents: Optional[List[str]] = None,
    storage_mode: str = "postgres",
    triggered_by: str = "admin",
) -> Optional[int]:
    """
    Saves a main Orchestrator supervision run into agent_runs table.
    Returns the generated run_id if successful, or None in Excel/fallback mode.
    """
    if not is_agent_db_available():
        logger.warning("PostgreSQL unavailable; agent supervision run cannot be saved in Excel mode.")
        return None

    try:
        from database.db import get_cursor
        selected_json = psycopg2.extras.Json(selected_agents or [])
        llm_gen = orchestrator_output.llm_executive_summary is not None

        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO agent_runs (
                    entity_id, run_type, selected_agents, global_status,
                    final_summary, recommended_next_best_action, confidence_score,
                    storage_mode, triggered_by, llm_summary_generated
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING run_id;
                """,
                (
                    orchestrator_output.entity_id,
                    "Entity Supervision",
                    selected_json,
                    orchestrator_output.global_status,
                    orchestrator_output.final_summary,
                    orchestrator_output.recommended_next_best_action,
                    float(orchestrator_output.confidence_score),
                    storage_mode,
                    triggered_by,
                    llm_gen,
                ),
            )
            row = cur.fetchone()
            if row:
                run_id = row["run_id"] if isinstance(row, dict) else row[0]
                logger.info(f"Successfully saved agent_run #{run_id} for Entity [{orchestrator_output.entity_id}].")
                return run_id
    except Exception as e:
        logger.error(f"Failed to save agent_run for {orchestrator_output.entity_id}: {e}", exc_info=True)

    return None


def save_agent_outputs(run_id: int, agent_outputs: List[Any]) -> bool:
    """
    Saves individual specialized agent outputs into agent_outputs table.
    Accepts both AgentOutput objects and raw dictionary representations.
    """
    if not is_agent_db_available() or not run_id:
        return False

    try:
        from database.db import get_cursor
        with get_cursor(commit=True) as cur:
            for out in agent_outputs or []:
                if isinstance(out, dict):
                    aid = out.get("agent_id", "unknown")
                    aname = out.get("agent_name", "Specialized Agent")
                    status = out.get("status", "OK")
                    summary = out.get("summary", "")
                    obs = psycopg2.extras.Json(out.get("observations", []))
                    risks = psycopg2.extras.Json(out.get("risks", []))
                    opps = psycopg2.extras.Json(out.get("opportunities", []))
                    recs = psycopg2.extras.Json(out.get("recommendations", []))
                    ev = psycopg2.extras.Json(out.get("evidence", []))
                    conf = float(out.get("confidence_score", 0.80))
                else:
                    aid = out.agent_id
                    aname = out.agent_name
                    status = out.status
                    summary = out.summary
                    obs = psycopg2.extras.Json(out.observations or [])
                    risks = psycopg2.extras.Json(out.risks or [])
                    opps = psycopg2.extras.Json(out.opportunities or [])
                    recs = psycopg2.extras.Json(out.recommendations or [])
                    ev = psycopg2.extras.Json(out.evidence or [])
                    conf = float(out.confidence_score)

                cur.execute(
                    """
                    INSERT INTO agent_outputs (
                        run_id, agent_id, agent_name, status, summary,
                        observations, risks, opportunities, recommendations, evidence, confidence_score
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (run_id, aid, aname, status, summary, obs, risks, opps, recs, ev, conf),
                )
        logger.info(f"Successfully saved {len(agent_outputs)} specialized outputs for run_id #{run_id}.")
        return True
    except Exception as e:
        logger.error(f"Failed to save agent_outputs for run_id #{run_id}: {e}", exc_info=True)

    return False


def get_agent_runs(entity_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves historical agent supervision runs from PostgreSQL (Read-Only)."""
    if not is_agent_db_available():
        return []

    try:
        from database.db import get_cursor
        with get_cursor(commit=False) as cur:
            if entity_id:
                cur.execute(
                    """
                    SELECT * FROM agent_runs
                    WHERE entity_id = %s
                    ORDER BY created_at DESC LIMIT %s;
                    """,
                    (str(entity_id).strip(), limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM agent_runs ORDER BY created_at DESC LIMIT %s;",
                    (limit,),
                )
            rows = cur.fetchall()
            if rows:
                return [dict(r) for r in rows]
    except Exception as e:
        logger.debug(f"Failed to retrieve agent_runs: {e}")

    return []


def get_agent_run_by_id(run_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single agent run by run_id (Read-Only)."""
    if not is_agent_db_available() or not run_id:
        return None

    try:
        from database.db import get_cursor
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT * FROM agent_runs WHERE run_id = %s;", (run_id,))
            row = cur.fetchone()
            if row:
                return dict(row)
    except Exception as e:
        logger.debug(f"Failed to retrieve agent_run #{run_id}: {e}")

    return None


def get_agent_outputs(run_id: int) -> List[Dict[str, Any]]:
    """Retrieves specialized agent outputs for a specific run_id (Read-Only)."""
    if not is_agent_db_available() or not run_id:
        return []

    try:
        from database.db import get_cursor
        with get_cursor(commit=False) as cur:
            cur.execute(
                "SELECT * FROM agent_outputs WHERE run_id = %s ORDER BY output_id ASC;",
                (run_id,),
            )
            rows = cur.fetchall()
            if rows:
                return [dict(r) for r in rows]
    except Exception as e:
        logger.debug(f"Failed to retrieve agent_outputs for run_id #{run_id}: {e}")

    return []


def get_agent_memory_for_entity(entity_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves historical agent supervision memory for a specific entity."""
    return get_agent_runs(entity_id=entity_id, limit=limit)


def create_approval_item(
    run_id: Optional[int],
    entity_id: str,
    action_dict: Dict[str, Any],
) -> Optional[int]:
    """
    Creates a new pending item in the agent_approval_queue.
    Action execution is NOT automated; item remains Pending until admin validation.
    """
    if not is_agent_db_available():
        logger.warning("PostgreSQL unavailable; approval item cannot be saved in Excel mode.")
        return None

    try:
        from database.db import get_cursor
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO agent_approval_queue (
                    run_id, entity_id, proposed_action_type, proposed_action_title,
                    proposed_action_description, source_agent, priority, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING approval_id;
                """,
                (
                    run_id,
                    str(entity_id).strip(),
                    action_dict.get("proposed_action_type", "Operational Action"),
                    action_dict.get("proposed_action_title", "Recommended Action"),
                    action_dict.get("proposed_action_description", ""),
                    action_dict.get("source_agent", "Orchestrator"),
                    action_dict.get("priority", "Medium"),
                    "Pending",
                ),
            )
            row = cur.fetchone()
            if row:
                appr_id = row["approval_id"] if isinstance(row, dict) else row[0]
                logger.info(f"Created pending approval_item #{appr_id} for Entity [{entity_id}].")
                return appr_id
    except Exception as e:
        logger.error(f"Failed to create approval item for {entity_id}: {e}", exc_info=True)

    return None


def get_approval_queue(
    status: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Retrieves items from the agent_approval_queue (Read-Only)."""
    if not is_agent_db_available():
        return []

    try:
        from database.db import get_cursor
        with get_cursor(commit=False) as cur:
            conditions = []
            params = []

            if status:
                conditions.append("status = %s")
                params.append(status)
            if entity_id:
                conditions.append("entity_id = %s")
                params.append(str(entity_id).strip())

            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            query = f"SELECT * FROM agent_approval_queue{where_clause} ORDER BY created_at DESC LIMIT %s;"
            params.append(limit)

            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            if rows:
                return [dict(r) for r in rows]
    except Exception as e:
        logger.debug(f"Failed to retrieve approval queue: {e}")

    return []


def update_approval_status(
    approval_id: int,
    status: str,
    admin_comment: Optional[str] = None,
    approved_by: str = "admin",
) -> bool:
    """
    Updates the administrative status of an item in the approval queue
    (Pending -> Approved, Rejected, Converted to Campaign Draft, or Ignored).
    This function modifies ONLY the approval status row; it does NOT alter customer data.
    """
    if not is_agent_db_available() or not approval_id:
        return False

    valid_statuses = {"Pending", "Approved", "Rejected", "Converted to Campaign Draft", "Ignored"}
    if status not in valid_statuses:
        logger.error(f"Invalid approval status '{status}'. Must be one of {valid_statuses}.")
        return False

    try:
        from database.db import get_cursor
        with get_cursor(commit=True) as cur:
            if status == "Approved":
                cur.execute(
                    """
                    UPDATE agent_approval_queue
                    SET status = %s, admin_comment = %s, approved_by = %s, approved_at = NOW()
                    WHERE approval_id = %s;
                    """,
                    (status, admin_comment, approved_by, approval_id),
                )
            elif status == "Rejected":
                cur.execute(
                    """
                    UPDATE agent_approval_queue
                    SET status = %s, admin_comment = %s, rejected_at = NOW()
                    WHERE approval_id = %s;
                    """,
                    (status, admin_comment, approval_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE agent_approval_queue
                    SET status = %s, admin_comment = %s
                    WHERE approval_id = %s;
                    """,
                    (status, admin_comment, approval_id),
                )

        logger.info(f"Updated approval_item #{approval_id} to status '{status}'.")
        return True
    except Exception as e:
        logger.error(f"Failed to update approval_item #{approval_id}: {e}", exc_info=True)

    return False


def convert_approved_action_to_campaign_draft(approval_id: int) -> Dict[str, Any]:
    """
    Optional Phase 8.3 feature:
    Converts an Approved action item into a closed-loop Campaign Draft.
    Draft creation does NOT send real messages (SMS/Email).
    """
    if not is_agent_db_available():
        return {"success": False, "reason": "PostgreSQL required for campaign draft conversion."}

    try:
        from database.db import get_cursor
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT * FROM agent_approval_queue WHERE approval_id = %s;", (approval_id,))
            item = cur.fetchone()
            if not item:
                return {"success": False, "reason": f"Approval item #{approval_id} not found."}

            item_dict = dict(item)
            if item_dict.get("status") != "Approved":
                return {"success": False, "reason": f"Approval item #{approval_id} must be 'Approved' before conversion (Current: {item_dict.get('status')})."}

        # Use campaign repository to create campaign draft safely
        from campaign.campaign_repository import create_campaign_dispatch
        campaign_id = create_campaign_dispatch(
            entity_id=item_dict.get("entity_id"),
            recommendation_id=None,
            campaign_name=f"Draft: {item_dict.get('proposed_action_title', 'Agent Recommended Campaign')}",
            campaign_type="Retention Offer",
            campaign_channel="Email",
            message_subject=f"Special Offer for {item_dict.get('entity_id')}",
            message_body=item_dict.get("proposed_action_description", "Agent recommended retention campaign draft."),
            target_segment="Supervised Action",
            priority=item_dict.get("priority", "High"),
            status="Draft",
            estimated_cost=0.0,
            expected_clv_lift=500.0,
        )

        if campaign_id:
            update_approval_status(
                approval_id=approval_id,
                status="Converted to Campaign Draft",
                admin_comment=f"Converted to Campaign Draft #{campaign_id}",
            )
            return {"success": True, "campaign_id": campaign_id, "message": f"Successfully created Campaign Draft #{campaign_id}."}

    except Exception as e:
        logger.error(f"Error converting approval item #{approval_id} to campaign draft: {e}", exc_info=True)

    return {"success": False, "reason": "Campaign draft creation failed."}
