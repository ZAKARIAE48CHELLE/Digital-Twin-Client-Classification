"""
OSMOS Multi-Agent Supervision Layer — Agent Debate Tests (Phase 8.4)
===================================================================
Unit test suite verifying agent statements, conflict detection routines,
consensus building, priority action selection, and read-only safety.
"""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

from agents.agent_schemas import AgentOutput, OrchestratorOutput
from agents.debate_schemas import AgentDebateStatement, AgentConflict, AgentConsensus, DebateOutput
from agents.debate_engine import build_agent_statements, run_deterministic_debate
from agents.conflict_detector import (
    detect_all_conflicts,
    detect_priority_conflicts,
    detect_status_conflicts,
    detect_data_quality_conflicts,
)
from agents.consensus_builder import (
    build_consensus,
    compute_consensus_status,
    choose_priority_action,
    compute_debate_confidence,
)
from agents.orchestrator_agent import OrchestratorAgent, run_orchestrated_analysis


class TestAgentDebatePhase84(unittest.TestCase):

    def setUp(self):
        self.clv_output = AgentOutput(
            agent_id="clv",
            agent_name="CLV Agent",
            agent_role="Lifetime Value",
            status="OK",
            summary="High CLV entity with premium expansion potential.",
            opportunities=["Eligible for VIP luxury tier upgrade."],
            recommendations=["Offer VIP concierge upgrade."],
            confidence_score=0.90,
        )

        self.churn_output = AgentOutput(
            agent_id="churn",
            agent_name="Churn Risk Agent",
            agent_role="Retention",
            status="Critical",
            summary="Critical churn risk detected due to complaint surge.",
            risks=["85% probability of churn in next 30 days."],
            recommendations=["Launch urgent service recovery outreach."],
            confidence_score=0.92,
        )

        self.db_output = AgentOutput(
            agent_id="database_audit",
            agent_name="Database Audit Agent",
            agent_role="Data Integrity",
            status="Critical",
            summary="Missing event references in digital twin snapshot.",
            risks=["Database record discrepancy."],
            recommendations=["Audit database schema before presentation."],
            confidence_score=0.95,
        )

    def test_build_agent_statements(self):
        """Verifies build_agent_statements returns one statement per agent."""
        statements = build_agent_statements([self.clv_output, self.churn_output])
        self.assertEqual(len(statements), 2)
        self.assertEqual(statements[0].agent_id, "clv")
        self.assertEqual(statements[1].agent_id, "churn")
        self.assertEqual(statements[1].concern_level, "Critical")

    def test_conflict_detector_priority_clash(self):
        """Verifies conflict detector catches CLV opportunity vs Churn risk priority conflict."""
        conflicts = detect_priority_conflicts([self.clv_output, self.churn_output])
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0].conflict_type, "Risk vs Opportunity Priority")
        self.assertIn("clv", conflicts[0].agents_involved)
        self.assertIn("churn", conflicts[0].agents_involved)

    def test_conflict_detector_status_disagreement(self):
        """Verifies conflict detector catches Status Disagreement between OK and Critical agents."""
        conflicts = detect_status_conflicts([self.clv_output, self.churn_output])
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0].conflict_type, "Status Disagreement")

    def test_conflict_detector_data_quality_override(self):
        """Verifies DB audit alerts create Data Quality Override conflict."""
        conflicts = detect_data_quality_conflicts([self.clv_output, self.db_output])
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0].conflict_type, "Data Quality Override")

    def test_consensus_builder_strong_consensus(self):
        """Verifies consensus status is Strong Consensus when no conflicts exist."""
        ok_agent = AgentOutput(
            agent_id="digital_twin",
            agent_name="Digital Twin Agent",
            agent_role="State",
            status="OK",
            summary="Profile complete.",
            confidence_score=0.95,
        )
        consensus = build_consensus([ok_agent], conflicts=[])
        self.assertEqual(consensus.consensus_status, "Strong Consensus")

    def test_consensus_builder_priority_action_retention_first(self):
        """Verifies priority action selects retention/recovery before upsell when churn is high."""
        conflicts = detect_all_conflicts([self.clv_output, self.churn_output])
        priority = choose_priority_action([self.clv_output, self.churn_output], conflicts)
        self.assertIn("SERVICE RECOVERY", priority)

    def test_debate_confidence_decreases_with_conflicts(self):
        """Verifies debate confidence score decreases when conflicts exist."""
        conflicts = detect_all_conflicts([self.clv_output, self.churn_output])
        conf_with_clash = compute_debate_confidence([self.clv_output, self.churn_output], conflicts)
        conf_no_clash = compute_debate_confidence([self.clv_output], [])
        self.assertLess(conf_with_clash, conf_no_clash)

    def test_orchestrator_debate_mode_on_and_off(self):
        """Verifies Orchestrator works cleanly with debate_mode=True and debate_mode=False."""
        sample_df = pd.DataFrame([{"entity_id": "P_DEMO_001", "entity_type": "Prospect", "recency_days": 10}])

        # 1. debate_mode=True
        report_with_deb = run_orchestrated_analysis("P_DEMO_001", df=sample_df, debate_mode=True)
        self.assertIsNotNone(report_with_deb.debate_output)
        self.assertIn("consensus", report_with_deb.debate_output)

        # 2. debate_mode=False
        report_no_deb = run_orchestrated_analysis("P_DEMO_001", df=sample_df, debate_mode=False)
        self.assertIsNone(report_no_deb.debate_output)

    def test_approval_actions_use_debate_context(self):
        """Verifies prepare_approval_actions incorporates debate consensus status when debate mode is ON."""
        sample_df = pd.DataFrame([{"entity_id": "P_DEMO_001", "entity_type": "Prospect", "recency_days": 10}])
        orchestrator = OrchestratorAgent()

        report = orchestrator.analyze_entity("P_DEMO_001", df=sample_df, debate_mode=True)
        actions = orchestrator.prepare_approval_actions(report)

        self.assertGreater(len(actions), 0)
        self.assertEqual(actions[0]["proposed_action_type"], "Debate Next Best Action")
        self.assertIn("[Debate Consensus:", actions[0]["proposed_action_description"])


if __name__ == "__main__":
    unittest.main()
