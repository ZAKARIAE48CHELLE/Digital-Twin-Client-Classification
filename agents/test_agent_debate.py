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
        """Verifies conflict detector catches Status Disagreement between Digital Twin OK and Churn Critical agents within the same domain."""
        dt_ok = AgentOutput(
            agent_id="digital_twin", agent_name="Digital Twin Agent", agent_role="State",
            status="OK", summary="Entity state nominal.", confidence_score=0.90,
        )
        conflicts = detect_status_conflicts([dt_ok, self.churn_output])
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0].conflict_type, "Customer Intelligence Status Disagreement")

    def test_clv_ok_and_churn_critical_is_not_status_disagreement(self):
        """Verifies CLV OK vs Churn Critical is not treated as a domain status contradiction, but creates a Low CLV + High Churn Finding."""
        conflicts_stat = detect_status_conflicts([self.clv_output, self.churn_output])
        self.assertEqual(len(conflicts_stat), 0)

        conflicts_prio = detect_priority_conflicts([self.clv_output, self.churn_output])
        self.assertGreater(len(conflicts_prio), 0)
        self.assertEqual(conflicts_prio[0].conflict_type, "Low CLV + High Churn Finding")
        self.assertIn("low-cost automated retention", conflicts_prio[0].description)

    def test_conflict_detector_data_quality_override(self):
        """Verifies DB audit alerts create Data Quality Override conflict when real integrity issues exist."""
        db_integrity_issue = AgentOutput(
            agent_id="database_audit",
            agent_name="Database Audit Agent",
            agent_role="Data Integrity",
            status="Critical",
            summary="Data integrity issue: orphaned references in customer_event_history.",
            risks=["Data integrity issue: 3 orphaned event references."],
            confidence_score=0.95,
        )
        conflicts = detect_data_quality_conflicts([self.clv_output, db_integrity_issue])
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0].conflict_type, "Database Audit Override")

    def test_churn_critical_journey_ok_not_conflict(self):
        """Verifies Churn Critical and Journey OK are cross-domain and do NOT trigger a status conflict."""
        journey_ok = AgentOutput(
            agent_id="journey",
            agent_name="Journey Agent",
            agent_role="Journey Analysis",
            status="OK",
            summary="No journey scenario logged for Entity [C00001]. No journey scenario expected for this entity.",
            confidence_score=0.90,
        )
        conflicts = detect_status_conflicts([self.churn_output, journey_ok])
        self.assertEqual(len(conflicts), 0)

    def test_journey_not_started_for_demo_entity_is_warning(self):
        """Verifies Journey Agent status is Warning when P_DEMO_001 journey has 0 steps executed."""
        from agents.journey_agent import JourneyAgent
        from agents.agent_schemas import AgentContext
        ctx = AgentContext(entity_id="P_DEMO_001", journey_history=[])
        out = JourneyAgent().safe_analyze(ctx)
        self.assertEqual(out.status, "Warning")
        self.assertIn("P_DEMO_001", out.summary)

    def test_churn_critical_no_campaign_creates_campaign_gap_finding(self):
        """Verifies Churn Critical + 0 campaign dispatches creates Customer Risk + Campaign Gap conflict."""
        from agents.conflict_detector import detect_campaign_readiness_conflicts
        camp_out = AgentOutput(
            agent_id="campaign",
            agent_name="Campaign Agent",
            agent_role="Campaign Dispatch Audit",
            status="Warning",
            summary="ZERO campaign dispatches recorded for Entity [P_DEMO_001].",
            risks=["Entity has received 0 campaign dispatches."],
            confidence_score=0.90,
        )
        conflicts = detect_campaign_readiness_conflicts([self.churn_output, camp_out])
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0].conflict_type, "Customer Risk + Campaign Gap")

    def test_persona_none_with_segment_creates_mapping_conflict(self):
        """Verifies Persona Agent with valid segment and persona None creates Persona Mapping Issue conflict."""
        from agents.persona_agent import PersonaAgent
        from agents.conflict_detector import detect_persona_action_conflicts
        from agents.agent_schemas import AgentContext

        ctx = AgentContext(entity_id="P_DEMO_001", latest_segment="Complaint-Driven Risk Clients", latest_persona=None)
        p_out = PersonaAgent().safe_analyze(ctx)
        self.assertIn(p_out.status, {"Warning", "Critical"})

        conflicts = detect_persona_action_conflicts([p_out, self.churn_output])
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0].conflict_type, "Persona Mapping Issue")

    def test_database_audit_critical_overrides_domains(self):
        """Verifies Database Audit Critical overrides other domains and sets Data Quality Override conflict."""
        db_critical = AgentOutput(
            agent_id="database_audit",
            agent_name="Database Audit Agent",
            agent_role="Data Integrity",
            status="Critical",
            summary="Data integrity issue: corrupted foreign keys.",
            risks=["Data integrity issue: corrupted foreign keys."],
            confidence_score=0.95,
        )
        conflicts = detect_data_quality_conflicts([self.clv_output, db_critical])
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0].conflict_type, "Database Audit Override")
        self.assertEqual(conflicts[0].severity, "Critical")

    def test_final_recommendation_uses_osmos_specific_language(self):
        """Verifies final Next Best Action recommendation uses OSMOS-specific system language."""
        from agents.result_aggregator import choose_next_best_action
        camp_out = AgentOutput(
            agent_id="campaign", agent_name="Campaign Agent", agent_role="Campaign Audit", status="Warning",
            summary="ZERO campaign dispatches logged.", risks=["ZERO campaign dispatches."],
        )
        p_out = AgentOutput(
            agent_id="persona", agent_name="Persona Agent", agent_role="Persona Audit", status="Critical",
            summary="Segment 'Complaint-Driven Risk Clients' exists but stable persona is None.",
            risks=["Persona mapping incomplete for segment."],
        )
        j_out = AgentOutput(
            agent_id="journey", agent_name="Journey Agent", agent_role="Journey Audit", status="Warning",
            summary="Demo entity [P_DEMO_001] journey has not been started (0/5 steps executed).",
        )
        nba = choose_next_best_action([self.churn_output, camp_out, p_out, j_out], entity_id="P_DEMO_001")

        self.assertIn("Demo entity is not ready", nba)
        self.assertIn("low-cost service recovery simulation", nba)
        self.assertIn("Journey Simulator", nba)
        self.assertIn("persona mapping", nba)
        self.assertNotIn("risk management department", nba)
        self.assertNotIn("prospecting agent", nba)
        self.assertNotIn("marketing department", nba)

    def test_journey_agent_scope_does_not_evaluate_customer_health(self):
        """Verifies Journey Agent strictly evaluates journey scenario integrity and not customer churn health."""
        from agents.journey_agent import JourneyAgent
        from agents.agent_schemas import AgentContext
        ctx = AgentContext(
            entity_id="C00001",
            journey_history=[],
            latest_digital_twin={"churn_risk_score": 0.95, "churn_status": "Critical"},
        )
        out = JourneyAgent().safe_analyze(ctx)
        # Normal entity with 0 steps has status OK in Journey Agent (no customer churn status pollution)
        self.assertEqual(out.status, "OK")
        self.assertTrue(any("No journey scenario expected" in obs for obs in out.observations))

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
        self.assertTrue(any(k in priority for k in ["RETENTION", "SERVICE RECOVERY"]))

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
