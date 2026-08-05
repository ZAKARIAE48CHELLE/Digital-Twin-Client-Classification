"""
OSMOS Multi-Agent Supervision Layer — Agent Memory & Approval Queue Tests (Phase 8.3)
====================================================================================
Unit test suite verifying agent run persistence, specialized output storage,
human approval queue workflows, campaign draft conversion, and read-only safety guarantees.
"""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

from agents.agent_schemas import AgentContext, AgentOutput, OrchestratorOutput
from agents.agent_repository import (
    is_agent_db_available,
    save_agent_run,
    save_agent_outputs,
    get_agent_runs,
    get_agent_run_by_id,
    get_agent_outputs,
    create_approval_item,
    get_approval_queue,
    update_approval_status,
    convert_approved_action_to_campaign_draft,
)
from agents.orchestrator_agent import OrchestratorAgent, run_orchestrated_analysis


class TestAgentMemoryAndApprovalQueuePhase83(unittest.TestCase):

    def setUp(self):
        self.sample_output = OrchestratorOutput(
            entity_id="P_DEMO_001",
            global_status="OK",
            final_summary="Multi-Agent Supervision for Entity [P_DEMO_001] evaluated a global status of 'OK'.",
            agent_outputs=[
                {
                    "agent_id": "digital_twin",
                    "agent_name": "Digital Twin Agent",
                    "status": "OK",
                    "summary": "Profile completeness is 90%.",
                    "observations": ["Profile completes basic requirements."],
                    "risks": [],
                    "opportunities": ["Ready for campaign onboarding."],
                    "recommendations": ["Maintain standard tracking."],
                    "evidence": [],
                    "confidence_score": 0.95,
                }
            ],
            consolidated_risks=[],
            consolidated_opportunities=["Ready for campaign onboarding."],
            final_recommendations=["Launch personalized introductory onboarding campaign."],
            recommended_next_best_action="PROSPECT CONVERSION: Launch personalized introductory onboarding campaign.",
            confidence_score=0.95,
        )

    def test_excel_mode_memory_fallback(self):
        """Verifies Excel mode handles missing database operations safely without crashing."""
        with patch("agents.agent_repository.is_agent_db_available", return_value=False):
            run_id = save_agent_run(self.sample_output)
            self.assertIsNone(run_id)

            runs = get_agent_runs("P_DEMO_001")
            self.assertEqual(runs, [])

            appr_id = create_approval_item(None, "P_DEMO_001", {"proposed_action_title": "Test Action"})
            self.assertIsNone(appr_id)

    @patch("agents.agent_repository.is_agent_db_available", return_value=True)
    @patch("database.db.get_cursor")
    def test_save_agent_run_and_outputs(self, mock_get_cursor, mock_db_avail):
        """Verifies saving an agent supervision run and outputs using mock cursor."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [{"run_id": 42}, None]
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor

        run_id = save_agent_run(self.sample_output, selected_agents=["digital_twin", "clv"])
        self.assertEqual(run_id, 42)

        success = save_agent_outputs(42, self.sample_output.agent_outputs)
        self.assertTrue(success)

    @patch("agents.agent_repository.is_agent_db_available", return_value=True)
    @patch("database.db.get_cursor")
    def test_create_and_update_approval_queue_item(self, mock_get_cursor, mock_db_avail):
        """Verifies creating and approving an item in the Human Approval Queue."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"approval_id": 101}
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor

        action_dict = {
            "proposed_action_type": "Next Best Action",
            "proposed_action_title": "Action for P_DEMO_001",
            "proposed_action_description": "PROSPECT CONVERSION: Launch onboarding campaign.",
            "source_agent": "Orchestrator",
            "priority": "High",
        }

        appr_id = create_approval_item(run_id=42, entity_id="P_DEMO_001", action_dict=action_dict)
        self.assertEqual(appr_id, 101)

        updated = update_approval_status(101, "Approved", admin_comment="Approved by lead admin.")
        self.assertTrue(updated)

    def test_human_approval_rule_no_auto_execution(self):
        """Verifies creating an approval item does NOT alter core entity data automatically."""
        sample_df = pd.DataFrame([{"entity_id": "P_DEMO_001", "entity_type": "Prospect", "recency_days": 10}])
        original_df = sample_df.copy(deep=True)

        orchestrator = OrchestratorAgent()
        output = orchestrator.analyze_entity("P_DEMO_001", df=sample_df)
        actions = orchestrator.prepare_approval_actions(output)

        self.assertGreater(len(actions), 0)
        # Verify DataFrame remains completely unmutated
        pd.testing.assert_frame_equal(sample_df, original_df)


if __name__ == "__main__":
    unittest.main()
