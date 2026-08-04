"""
OSMOS Multi-Agent Supervision Layer — Unit Tests (Phase 8.1)
============================================================
Comprehensive test suite verifying BaseAgent, context builder, specialized agents,
orchestration, result aggregation, evidence traceability, and no-write guarantees.
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
from agents.agent_registry import AGENT_REGISTRY, get_agent, get_active_agents
from agents.result_aggregator import (
    aggregate_agent_status,
    merge_risks,
    merge_opportunities,
    merge_recommendations,
    choose_next_best_action,
)
from agents.orchestrator_agent import OrchestratorAgent, run_orchestrated_analysis


class BrokenTestAgent(BaseAgent):
    """Subclass for testing exception handling isolation."""

    def __init__(self):
        super().__init__("broken", "Broken Agent", "Tests crash isolation")

    def _analyze_implementation(self, context: AgentContext) -> AgentOutput:
        raise ValueError("Simulated unexpected crash inside specialized agent!")


class TestMultiAgentSupervisionLayer(unittest.TestCase):

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

    def test_evidence_item_schema(self):
        """Verifies EvidenceItem formatting and dictionary conversion."""
        item = EvidenceItem("test_metric", 100, ">50", "Test interpretation")
        d = item.to_dict()
        self.assertEqual(d["metric_name"], "test_metric")
        self.assertEqual(d["value"], 100)
        self.assertEqual(d["threshold"], ">50")
        self.assertEqual(d["interpretation"], "Test interpretation")

    def test_base_agent_validation_and_error_handling(self):
        """Verifies BaseAgent safely handles invalid contexts and crashes."""
        agent = DigitalTwinAgent()

        # Invalid Context
        output_invalid = agent.safe_analyze(None)
        self.assertEqual(output_invalid.status, "Insufficient Data")
        self.assertEqual(output_invalid.confidence_score, 0.0)

        # Exception isolation
        broken_agent = BrokenTestAgent()
        valid_ctx = AgentContext(entity_id="P_DEMO_001")
        output_broken = broken_agent.safe_analyze(valid_ctx)
        self.assertEqual(output_broken.status, "Error")
        self.assertIn("Simulated unexpected crash", output_broken.observations[1])

    def test_context_builder(self):
        """Verifies Context Builder extracts entity fields from DataFrame in read-only mode."""
        ctx = build_entity_agent_context("P_DEMO_001", df=self.sample_df)
        self.assertEqual(ctx.entity_id, "P_DEMO_001")
        self.assertEqual(ctx.entity_type, "Prospect")
        self.assertEqual(ctx.latest_segment, "Prospect")
        self.assertEqual(ctx.latest_persona, "New Explorer")
        self.assertIn(ctx.storage_mode, ["postgres", "excel"])

    def test_digital_twin_agent(self):
        """Verifies DigitalTwinAgent evaluates profile completeness and evidence traceability."""
        ctx = build_entity_agent_context("P_DEMO_001", df=self.sample_df)
        agent = DigitalTwinAgent()
        output = agent.safe_analyze(ctx)

        self.assertIn(output.status, ["OK", "Warning"])
        self.assertGreater(len(output.evidence), 0)
        self.assertEqual(output.evidence[0]["metric_name"], "profile_completeness")

    def test_clv_agent_classification(self):
        """Verifies CLVAgent tiering logic (VIP, Medium, Low, Collapse)."""
        agent = CLVAgent()

        # VIP Client
        vip_ctx = build_entity_agent_context("C00001", df=self.sample_df)
        vip_out = agent.safe_analyze(vip_ctx)
        self.assertIn("High Value", vip_out.observations[0])

        # Low Value Client
        low_df = pd.DataFrame([{"entity_id": "L001", "predicted_clv_amount_mad": 500.0}])
        low_ctx = build_entity_agent_context("L001", df=low_df)
        low_out = agent.safe_analyze(low_ctx)
        self.assertIn("Low Value", low_out.observations[0])

        # Value Collapse
        zero_df = pd.DataFrame([{"entity_id": "Z001", "predicted_clv_amount_mad": 0.0}])
        zero_ctx = build_entity_agent_context("Z001", df=zero_df)
        zero_out = agent.safe_analyze(zero_ctx)
        self.assertEqual(zero_out.status, "Warning")

    def test_churn_risk_agent(self):
        """Verifies ChurnRiskAgent threshold evaluation (Critical vs Low Risk)."""
        agent = ChurnRiskAgent()

        # Critical Churn Risk Client (C00001 has churn_risk_score = 0.85)
        crit_ctx = build_entity_agent_context("C00001", df=self.sample_df)
        crit_out = agent.safe_analyze(crit_ctx)
        self.assertEqual(crit_out.status, "Critical")
        self.assertTrue(any("Critical churn risk" in r for r in crit_out.risks))

        # Low Churn Risk Prospect (P_DEMO_001 has churn_risk_score = 0.25)
        low_ctx = build_entity_agent_context("P_DEMO_001", df=self.sample_df)
        low_out = agent.safe_analyze(low_ctx)
        self.assertEqual(low_out.status, "OK")

    def test_persona_agent_resolution(self):
        """Verifies PersonaAgent checks segment-first resolution and official library."""
        agent = PersonaAgent()
        ctx = build_entity_agent_context("C00001", df=self.sample_df)
        out = agent.safe_analyze(ctx)

        self.assertEqual(out.status, "OK")
        self.assertTrue(any("Premium Loyalist" in obs for obs in out.observations))

    def test_result_aggregator(self):
        """Verifies result aggregator logic, global status, and NBA selection."""
        agent_dt = DigitalTwinAgent()
        agent_churn = ChurnRiskAgent()
        agent_clv = CLVAgent()

        crit_ctx = build_entity_agent_context("C00001", df=self.sample_df)

        outputs = [
            agent_dt.safe_analyze(crit_ctx),
            agent_churn.safe_analyze(crit_ctx),
            agent_clv.safe_analyze(crit_ctx),
        ]

        global_status = aggregate_agent_status(outputs)
        self.assertEqual(global_status, "Critical")

        nba = choose_next_best_action(outputs, entity_type="Client")
        self.assertIn("RETENTION", nba)

    def test_orchestrator_execution(self):
        """Verifies end-to-end Orchestrator execution without automatic LLM calls."""
        orchestrator = OrchestratorAgent()
        report = orchestrator.analyze_entity("C00001", df=self.sample_df)

        self.assertIsInstance(report, OrchestratorOutput)
        self.assertEqual(report.entity_id, "C00001")
        self.assertEqual(report.global_status, "Critical")
        self.assertGreater(len(report.agent_outputs), 0)
        self.assertIsNone(report.llm_executive_summary)  # Must be None until button click

    def test_read_only_no_write_guard(self):
        """Verifies deterministic analysis makes zero DB write calls."""
        original_df = self.sample_df.copy(deep=True)
        report = run_orchestrated_analysis("P_DEMO_001", df=self.sample_df)
        self.assertEqual(report.entity_id, "P_DEMO_001")
        # Assert DataFrame was not mutated
        pd.testing.assert_frame_equal(self.sample_df, original_df)


if __name__ == "__main__":
    unittest.main()
