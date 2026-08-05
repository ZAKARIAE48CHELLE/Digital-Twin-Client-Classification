"""
OSMOS Multi-Agent Supervision Layer — Orchestrator Agent (Phase 8.2)
=====================================================================
Central orchestrator managing context construction, 8-agent execution,
result aggregation, system readiness synthesis, Next Best Action selection,
and optional on-demand LLM summary generation.
"""

import logging
from typing import Any, Dict, List, Optional
import pandas as pd

from agents.agent_schemas import AgentContext, AgentOutput, OrchestratorOutput
from agents.context_builder import build_entity_agent_context
from agents.agent_registry import get_active_agents, AGENT_REGISTRY
from agents.result_aggregator import (
    aggregate_agent_status,
    merge_risks,
    merge_opportunities,
    merge_recommendations,
    compute_global_confidence,
    choose_next_best_action,
    synthesize_orchestrator_summary,
    compute_system_readiness_summary,
)
from llm.llm_client import check_llm_available, generate_text
from llm.json_utils import extract_and_parse_json

logger = logging.getLogger("OSMOS_ORCHESTRATOR_AGENT")


class OrchestratorAgent:
    """
    Multi-Agent Supervision Orchestrator.
    Directs read-only entity inspection, delegates to specialized agents,
    synthesizes global supervision status, and suggests Next Best Actions.
    """

    def __init__(self, name: str = "OSMOS Orchestrator Agent"):
        self.name = name

    def detect_required_agents(self, context: AgentContext) -> List[str]:
        """Dynamically identifies relevant agent IDs based on context indicators."""
        return list(AGENT_REGISTRY.keys())

    def run_agents(
        self,
        context: AgentContext,
        selected_agent_ids: Optional[List[str]] = None,
    ) -> List[AgentOutput]:
        """
        Executes selected specialized agents safely in read-only mode.
        Ensures exception isolation so one failing agent does not crash the pipeline.
        """
        active_agents = get_active_agents(selected_agent_ids)
        outputs: List[AgentOutput] = []

        for agent in active_agents:
            try:
                # Safe execution wrapper (No DB writes, no dataframe mutations)
                output = agent.safe_analyze(context)
                outputs.append(output)
            except Exception as e:
                logger.error(f"Error running {agent.agent_name}: {e}", exc_info=True)
                outputs.append(
                    agent.format_output(
                        status="Error",
                        summary=f"{agent.agent_name} failed with unhandled exception.",
                        observations=[str(e)],
                        confidence_score=0.0,
                    )
                )

        return outputs

    def analyze_entity(
        self,
        entity_id: str,
        df: Optional[pd.DataFrame] = None,
        history_df: Optional[pd.DataFrame] = None,
        selected_agent_ids: Optional[List[str]] = None,
        debate_mode: bool = True,
        include_knowledge: bool = False,
    ) -> OrchestratorOutput:
        """
        Main deterministic analysis entrypoint with optional Agent Debate Mode & Knowledge Memory.
        1. Builds AgentContext (Read-Only) with optional knowledge retrieval.
        2. Executes selected specialized agents.
        3. Aggregates outputs, risks, opportunities, recommendations.
        4. If debate_mode=True: runs cross-review, conflict detection & consensus synthesis.
        5. Returns structured OrchestratorOutput with optional debate_output.
        """
        context = build_entity_agent_context(
            entity_id=entity_id,
            df=df,
            history_df=history_df,
            include_knowledge=include_knowledge,
        )
        agent_outputs = self.run_agents(context, selected_agent_ids)

        global_status = aggregate_agent_status(agent_outputs)
        consolidated_risks = merge_risks(agent_outputs)
        consolidated_opps = merge_opportunities(agent_outputs)
        consolidated_recs = merge_recommendations(agent_outputs)
        confidence = compute_global_confidence(agent_outputs)
        next_best_action = choose_next_best_action(agent_outputs, entity_type=context.entity_type)

        debate_dict = None
        if debate_mode and agent_outputs:
            from agents.debate_engine import run_deterministic_debate
            deb_out = run_deterministic_debate(agent_outputs, entity_id=entity_id, context=context)
            debate_dict = deb_out.to_dict()

            # Override next best action & confidence with consensus decision if available
            consensus = deb_out.consensus or {}
            if consensus.get("priority_action"):
                next_best_action = consensus.get("priority_action")
            if consensus.get("confidence_score") is not None:
                confidence = float(consensus.get("confidence_score"))

        summary = synthesize_orchestrator_summary(
            entity_id=context.entity_id,
            global_status=global_status,
            next_best_action=next_best_action,
            agent_outputs=agent_outputs,
        )

        agent_output_dicts = [out.to_dict() for out in agent_outputs]

        return OrchestratorOutput(
            entity_id=context.entity_id,
            global_status=global_status,
            final_summary=summary,
            agent_outputs=agent_output_dicts,
            consolidated_risks=consolidated_risks,
            consolidated_opportunities=consolidated_opps,
            final_recommendations=consolidated_recs,
            recommended_next_best_action=next_best_action,
            confidence_score=confidence,
            llm_executive_summary=None,  # Button-triggered only
            debate_output=debate_dict,
        )

    def generate_llm_executive_summary(self, orchestrator_output: OrchestratorOutput) -> Dict[str, Any]:
        """
        Generates a polished executive supervision summary using the local LLM across all active agents.
        STRICTLY BUTTON-TRIGGERED ONLY.
        """
        available, reason = check_llm_available()
        if not available:
            return {
                "available": False,
                "reason": reason,
                "executive_summary_fr": f"Résumé exécutif déterministe pour l'entité [{orchestrator_output.entity_id}]: {orchestrator_output.final_summary}",
                "executive_summary_en": f"Deterministic executive summary for Entity [{orchestrator_output.entity_id}]: {orchestrator_output.final_summary}",
                "suggested_admin_actions_fr": [orchestrator_output.recommended_next_best_action],
                "suggested_admin_actions_en": [orchestrator_output.recommended_next_best_action],
            }

        prompt = f"""
You are the OSMOS Multi-Agent Executive Assistant.
Synthesize the structured 8-Agent Supervision report into a bilingual executive summary (French & English).

ENTITIES METADATA:
- Entity ID: {orchestrator_output.entity_id}
- Global Supervision Status: {orchestrator_output.global_status}
- Summary: {orchestrator_output.final_summary}
- Recommended Next Best Action: {orchestrator_output.recommended_next_best_action}
- Identified Risks: {', '.join(orchestrator_output.consolidated_risks[:5]) or 'None'}
- Identified Opportunities: {', '.join(orchestrator_output.consolidated_opportunities[:5]) or 'None'}
- Agent Recommendations: {', '.join(orchestrator_output.final_recommendations[:5]) or 'None'}

Return ONLY valid JSON matching this exact schema:
{{
  "executive_summary_fr": "Description concise du statut de l'entité et des priorités opérationnelles.",
  "executive_summary_en": "Concise overview of entity status and operational priorities.",
  "final_recommendation_fr": "Action recommandee en francais.",
  "final_recommendation_en": "Recommended next best action in English.",
  "suggested_admin_actions_fr": ["Action 1", "Action 2"],
  "suggested_admin_actions_en": ["Action 1", "Action 2"]
}}
"""
        try:
            raw_response = generate_text(prompt, temperature=0.2)
            parsed = extract_and_parse_json(raw_response)
            if parsed and isinstance(parsed, dict) and "executive_summary_en" in parsed:
                parsed["available"] = True
                parsed["reason"] = "LLM Executive Supervision Summary generated successfully."
                return parsed
        except Exception as e:
            logger.error(f"Error generating LLM executive summary: {e}")

        # Deterministic Fallback if LLM call fails
        return {
            "available": False,
            "reason": "LLM output parsing fallback",
            "executive_summary_fr": f"Statut Global: {orchestrator_output.global_status}. Action Prioritaire: {orchestrator_output.recommended_next_best_action}",
            "executive_summary_en": f"Global Status: {orchestrator_output.global_status}. Next Best Action: {orchestrator_output.recommended_next_best_action}",
            "suggested_admin_actions_fr": orchestrator_output.final_recommendations[:3],
            "suggested_admin_actions_en": orchestrator_output.final_recommendations[:3],
        }

    def generate_llm_debate_summary(self, orchestrator_output: OrchestratorOutput) -> Dict[str, Any]:
        """
        Generates a bilingual LLM synthesis of the Agent Debate & Collaboration results.
        STRICTLY BUTTON-TRIGGERED ONLY.
        """
        available, reason = check_llm_available()
        deb = orchestrator_output.debate_output or {}
        consensus = deb.get("consensus", {})
        conflicts = deb.get("conflicts", [])

        if not available or not deb:
            return {
                "available": False,
                "reason": reason if not available else "Debate output unavailable",
                "debate_summary_fr": f"Résumé du débat déterministe pour [{orchestrator_output.entity_id}]: Consensus '{consensus.get('consensus_status', 'N/A')}'. Action: {consensus.get('priority_action', 'N/A')}",
                "debate_summary_en": f"Deterministic debate summary for [{orchestrator_output.entity_id}]: Consensus '{consensus.get('consensus_status', 'N/A')}'. Action: {consensus.get('priority_action', 'N/A')}",
                "final_decision_fr": consensus.get("priority_action", orchestrator_output.recommended_next_best_action),
                "final_decision_en": consensus.get("priority_action", orchestrator_output.recommended_next_best_action),
                "admin_guidance_fr": [f"Résolution des conflits: {c.get('resolution_suggestion')}" for c in conflicts if c.get("resolution_suggestion")] or ["Aucun conflit majeur."],
                "admin_guidance_en": [f"Conflict resolution: {c.get('resolution_suggestion')}" for c in conflicts if c.get("resolution_suggestion")] or ["No major conflicts."],
            }

        prompt = f"""
You are the OSMOS Agent Debate Synthesizer.
Synthesize the agent debate and conflict resolution results into a bilingual executive summary (French & English).

DEBATE METADATA:
- Entity ID: {orchestrator_output.entity_id}
- Consensus Status: {consensus.get('consensus_status')}
- Priority Action: {consensus.get('priority_action')}
- Reasoning Summary: {consensus.get('reasoning_summary')}
- Detected Conflicts ({len(conflicts)}): {', '.join([c.get('description', '') for c in conflicts]) or 'None'}

Return ONLY valid JSON matching this exact schema:
{{
  "debate_summary_fr": "Synthese du debat et du consensus atteint en francais.",
  "debate_summary_en": "Executive synthesis of agent debate and consensus reached in English.",
  "final_decision_fr": "Action prioritaire decidee apres debat en francais.",
  "final_decision_en": "Priority decision reached after debate in English.",
  "admin_guidance_fr": ["Recommandation administrateur 1", "Recommandation 2"],
  "admin_guidance_en": ["Admin guidance 1", "Admin guidance 2"]
}}
"""
        try:
            raw = generate_text(prompt, temperature=0.2)
            parsed = extract_and_parse_json(raw)
            if parsed and isinstance(parsed, dict) and "debate_summary_en" in parsed:
                parsed["available"] = True
                parsed["reason"] = "LLM Debate Summary generated successfully."
                return parsed
        except Exception as e:
            logger.error(f"Error generating LLM debate summary: {e}")

        return {
            "available": False,
            "reason": "LLM debate summary fallback",
            "debate_summary_fr": f"Consensus: {consensus.get('consensus_status')}. Action: {consensus.get('priority_action')}",
            "debate_summary_en": f"Consensus: {consensus.get('consensus_status')}. Action: {consensus.get('priority_action')}",
            "final_decision_fr": consensus.get("priority_action"),
            "final_decision_en": consensus.get("priority_action"),
            "admin_guidance_fr": ["Procéder à la validation administrative."],
            "admin_guidance_en": ["Proceed with administrative validation."],
        }

    def prepare_approval_actions(self, orchestrator_output: OrchestratorOutput) -> List[Dict[str, Any]]:
        """
        Converts consolidated recommendations into structured approval action items.
        Includes debate consensus status and conflict alerts when debate output exists.
        Action execution is NEVER automated; items remain Pending until administrative review.
        """
        items: List[Dict[str, Any]] = []
        deb = orchestrator_output.debate_output or {}
        consensus = deb.get("consensus", {})
        conflicts = deb.get("conflicts", [])

        c_status = consensus.get("consensus_status", "Standard")
        desc_prefix = f"[Debate Consensus: {c_status}] " if deb else ""

        if conflicts:
            conflict_warn = f" (Warning: {len(conflicts)} conflict(s) resolved during debate)"
        else:
            conflict_warn = ""

        # 1. Primary Next Best Action item
        if orchestrator_output.recommended_next_best_action:
            nba = orchestrator_output.recommended_next_best_action
            prio = "High" if orchestrator_output.global_status in {"Critical", "Warning"} or conflicts else "Medium"
            items.append(
                {
                    "proposed_action_type": "Debate Next Best Action" if deb else "Next Best Action",
                    "proposed_action_title": f"Action for {orchestrator_output.entity_id}",
                    "proposed_action_description": f"{desc_prefix}{nba}{conflict_warn}",
                    "source_agent": "Agent Debate Engine" if deb else "Orchestrator",
                    "priority": prio,
                }
            )

        # 2. Individual recommendations
        for rec in orchestrator_output.final_recommendations[:4]:
            if rec != orchestrator_output.recommended_next_best_action:
                items.append(
                    {
                        "proposed_action_type": "Supervision Recommendation",
                        "proposed_action_title": rec[:60] + "..." if len(rec) > 60 else rec,
                        "proposed_action_description": f"{desc_prefix}{rec}",
                        "source_agent": "Specialized Agents",
                        "priority": "Medium",
                    }
                )

        return items

    def save_supervision_run(
        self,
        orchestrator_output: OrchestratorOutput,
        selected_agents: Optional[List[str]] = None,
        storage_mode: str = "postgres",
    ) -> Optional[int]:
        """
        Persists supervision run and outputs into PostgreSQL via agent_repository.
        Executed strictly when requested by explicit admin button click.
        """
        from agents.agent_repository import save_agent_run, save_agent_outputs

        run_id = save_agent_run(
            orchestrator_output=orchestrator_output,
            selected_agents=selected_agents,
            storage_mode=storage_mode,
            triggered_by="admin",
        )

        if run_id:
            save_agent_outputs(run_id, orchestrator_output.agent_outputs)

        return run_id


def run_orchestrated_analysis(
    entity_id: str,
    df: Optional[pd.DataFrame] = None,
    history_df: Optional[pd.DataFrame] = None,
    selected_agent_ids: Optional[List[str]] = None,
    debate_mode: bool = True,
    include_knowledge: bool = False,
) -> OrchestratorOutput:
    """Convenience functional wrapper for executing multi-agent orchestrated supervision with debate and knowledge."""
    orchestrator = OrchestratorAgent()
    return orchestrator.analyze_entity(
        entity_id=entity_id,
        df=df,
        history_df=history_df,
        selected_agent_ids=selected_agent_ids,
        debate_mode=debate_mode,
        include_knowledge=include_knowledge,
    )
