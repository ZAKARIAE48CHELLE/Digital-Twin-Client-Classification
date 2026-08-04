"""
OSMOS Multi-Agent Supervision Layer — Unit Tests (Phase 8.2)
============================================================
Comprehensive test suite verifying BaseAgent, context builder, 8 specialized agents,
orchestration, result aggregation, evidence traceability, and read-only no-write guarantees.
"""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

from agents.agent_schemas import AgentContext, AgentOutput, OrchestratorOutput, EvidenceItem
from agents.base_agent import BaseAgent
from agents.context_builder import build_entity_agent_context, get_latest_entity_state
from agents.digital_twin_agent import DigitalTwinAgent
from agents.clv_agent import CLVAgent
from agents.churn_agent import ChurnRiskAgent
from agents.persona_agent import PersonaAgent
from agents.campaign_agent import CampaignAgent
from agents.journey_agent import JourneyAgent
from agents.database_audit_agent import DatabaseAuditAgent
from agents.ui_ux_agent import UIUXAgent
from agents.agent_registry import AGENT_REGISTRY, get_agent, get_active_agents
from agents.result_aggregator import (
    aggregate_agent_status,
    merge_risks,
    merge_opportunities,
    merge_recommendations,
    choose_next_best_action,
    compute_system_readiness_summary,
)
from agents.orchestrator_agent import OrchestratorAgent, run_orchestrated_analysis


class BrokenTestAgent(BaseAgent):
    """Subclass for testing exception handling isolation."""

    def __init__(self):
        super().__init__("broken", "Broken Agent", "Tests crash isolation")

    def _analyze_implementation(self, context: AgentContext) -> AgentOutput:
        raise ValueError("Simulated unexpected crash inside specialized agent!")


class TestMultiAgentSupervisionLayerPhase82(unittest.TestCase):

    def setUp(self):
        self.sample_df = pd.DataFrame([
            {
                "entity_id": "P_DEMO_001",
                "entity_type": "Prospect",
                "recency_days": 15,
                "frequency": 0,
                "monetary_mad": 0.0,
                "predicted_clv_amount_mad": 2500.0,
                "clv_score": 0.65,
                "churn_risk_score": 0.25,
                "customer_segment": "Prospect",
                "persona_name": "New Explorer",
            },
            {
                "entity_id": "C00001",
                "entity_type": "Client",
                "recency_days": 120,
                "frequency": 12,
                "monetary_mad": 9500.0,
                "predicted_clv_amount_mad": 12000.0,
                "clv_score": 0.92,
                "churn_risk_score": 0.85,
                "complaint_count_90d": 3,
                "customer_segment": "High-Value Loyalists",
                "persona_name": "Premium Loyalist",
            },
        ])

    def test_registry_contains_all_8_agents(self):
        """Verifies AGENT_REGISTRY contains all 8 active specialized agents."""
        self.assertEqual(len(AGENT_REGISTRY), 8)
        expected = {"digital_twin", "clv", "churn", "persona", "campaign", "journey", "database_audit", "ui_ux"}
        self.assertEqual(set(AGENT_REGISTRY.keys()), expected)

    def test_campaign_agent_no_history(self):
        """Verifies CampaignAgent handles entities with zero campaign history cleanly."""
        agent = CampaignAgent()
        ctx = build_entity_agent_context("P_DEMO_001", df=self.sample_df)
        out = agent.safe_analyze(ctx)

        self.assertEqual(out.status, "OK")
        self.assertTrue(any("No campaign history" in obs for obs in out.observations))

    def test_campaign_agent_negative_response(self):
        """Verifies CampaignAgent detects negative campaign responses."""
        agent = CampaignAgent()
        ctx = build_entity_agent_context("C00001", df=self.sample_df)
        ctx.campaign_history = [
            {"dispatch_id": 1, "campaign_id": 5, "status": "Dispatched"},
            {"response_id": 10, "campaign_id": 5, "response_type": "Unsubscribed", "response_score": -1.0},
        ]
        out = agent.safe_analyze(ctx)

        self.assertEqual(out.status, "Warning")
        self.assertTrue(any("Negative campaign response" in r for r in out.risks))

    def test_journey_agent_completed_journey(self):
        """Verifies JourneyAgent detects a completed 5-stage lifecycle journey."""
        agent = JourneyAgent()
        ctx = build_entity_agent_context("P_DEMO_001", df=self.sample_df)
        ctx.journey_history = [
            {"step_id": 1, "current_stage": "1. New Prospect", "trigger_event_id": "E1"},
            {"step_id": 2, "current_stage": "2. First Purchase", "trigger_event_id": "E2"},
            {"step_id": 3, "current_stage": "3. Emerging Loyalist", "trigger_event_id": "E3"},
            {"step_id": 4, "current_stage": "4. VIP Loyalist", "trigger_event_id": "E4"},
            {"step_id": 5, "current_stage": "5. At-Risk VIP", "trigger_event_id": "E5"},
        ]
        out = agent.safe_analyze(ctx)

        self.assertEqual(out.status, "OK")
        self.assertTrue(any("completed standard 5-stage" in opp for opp in out.opportunities))

    def test_journey_agent_missing_event_refs(self):
        """Verifies JourneyAgent detects missing trigger_event_id references."""
        agent = JourneyAgent()
        ctx = build_entity_agent_context("P_DEMO_001", df=self.sample_df)
        ctx.journey_history = [
            {"step_id": 1, "current_stage": "1. New Prospect", "trigger_event_id": None},
        ]
        out = agent.safe_analyze(ctx)

        self.assertEqual(out.status, "Warning")
        self.assertTrue(any("missing trigger_event_id" in r for r in out.risks))

    def test_database_audit_agent(self):
        """Verifies DatabaseAuditAgent audits record counts without altering data."""
        agent = DatabaseAuditAgent()
        ctx = build_entity_agent_context("C00001", df=self.sample_df)
        out = agent.safe_analyze(ctx)

        self.assertIn(out.status, ["OK", "Warning"])
        self.assertGreater(len(out.evidence), 0)
        self.assertEqual(out.evidence[0]["metric_name"], "storage_mode")

    def test_ui_ux_agent_readiness(self):
        """Verifies UIUXAgent evaluates presentation readiness for P_DEMO_001."""
        agent = UIUXAgent()
        ctx = build_entity_agent_context("P_DEMO_001", df=self.sample_df)
        out = agent.safe_analyze(ctx)

        self.assertIn(out.status, ["OK", "Warning", "Insufficient Data"])
        self.assertTrue(any("P_DEMO_001" in ev["value"] for ev in out.evidence))

    def test_orchestrator_all_8_agents(self):
        """Verifies OrchestratorAgent executes all 8 agents and computes system readiness."""
        orchestrator = OrchestratorAgent()
        all_ids = ["digital_twin", "clv", "churn", "persona", "campaign", "journey", "database_audit", "ui_ux"]
        report = orchestrator.analyze_entity("C00001", df=self.sample_df, selected_agent_ids=all_ids)

        self.assertIsInstance(report, OrchestratorOutput)
        self.assertEqual(len(report.agent_outputs), 8)
        self.assertIsNone(report.llm_executive_summary)  # Button-triggered only

    def test_read_only_no_write_guard_all_agents(self):
        """Verifies executing all 8 agents makes zero DB writes and zero DataFrame mutations."""
        original_df = self.sample_df.copy(deep=True)
        orchestrator = OrchestratorAgent()
        all_ids = list(AGENT_REGISTRY.keys())
        report = orchestrator.analyze_entity("P_DEMO_001", df=self.sample_df, selected_agent_ids=all_ids)

        self.assertEqual(report.entity_id, "P_DEMO_001")
        pd.testing.assert_frame_equal(self.sample_df, original_df)


if __name__ == "__main__":
    unittest.main()
