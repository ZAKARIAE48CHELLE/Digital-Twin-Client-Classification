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
    ) -> OrchestratorOutput:
        """
        Main deterministic analysis entrypoint.
        1. Builds AgentContext (Read-Only).
        2. Executes selected specialized agents.
        3. Aggregates outputs, risks, opportunities, recommendations.
        4. Selects deterministic Next Best Action.
        5. Returns structured OrchestratorOutput.
        """
        context = build_entity_agent_context(entity_id=entity_id, df=df, history_df=history_df)
        agent_outputs = self.run_agents(context, selected_agent_ids)

        global_status = aggregate_agent_status(agent_outputs)
        consolidated_risks = merge_risks(agent_outputs)
        consolidated_opps = merge_opportunities(agent_outputs)
        consolidated_recs = merge_recommendations(agent_outputs)
        confidence = compute_global_confidence(agent_outputs)
        next_best_action = choose_next_best_action(agent_outputs, entity_type=context.entity_type)

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


def run_orchestrated_analysis(
    entity_id: str,
    df: Optional[pd.DataFrame] = None,
    history_df: Optional[pd.DataFrame] = None,
    selected_agent_ids: Optional[List[str]] = None,
) -> OrchestratorOutput:
    """Convenience functional wrapper for executing multi-agent orchestrated supervision."""
    orchestrator = OrchestratorAgent()
    return orchestrator.analyze_entity(
        entity_id=entity_id,
        df=df,
        history_df=history_df,
        selected_agent_ids=selected_agent_ids,
    )
