import unittest
from unittest.mock import patch, MagicMock
from journey.journey_scenarios import DEFAULT_STAGES, get_default_scenario_definition
from journey.journey_repository import (
    create_journey_scenario,
    get_journey_scenarios,
    get_journey_scenario_by_id,
    insert_journey_step,
    get_journey_steps,
    delete_journey_scenario
)
from journey.journey_runner import (
    DEMO_ENTITY_ID,
    create_demo_entity,
    reset_demo_journey,
    capture_entity_state,
    run_next_journey_step,
    run_full_journey,
    generate_llm_journey_explanation
)
from journey.journey_tree import render_journey_tree_mermaid, get_stage_icon

class TestJourneySimulator(unittest.TestCase):

    @patch("journey.journey_repository.is_postgres_available", return_value=False)
    def test_excel_mode_graceful_handling(self, mock_pg):
        """Test that scenario creation returns None gracefully in Excel fallback mode without crashing."""
        res = create_journey_scenario({"scenario_name": "Test Scenario"})
        self.assertIsNone(res)
        
        scens = get_journey_scenarios()
        self.assertEqual(len(scens), 0)

    def test_default_scenario_definition(self):
        """Verify default 5-stage scenario definition has correct order and stages."""
        scen_def = get_default_scenario_definition()
        self.assertEqual(len(scen_def["stages"]), 5)
        self.assertEqual(scen_def["stages"][0]["stage_name"], "1. New Prospect")
        self.assertEqual(scen_def["stages"][4]["stage_name"], "5. At-Risk Premium Client / Churn Risk")

    @patch("journey.journey_runner.save_entity_snapshot")
    def test_create_demo_entity(self, mock_save_snap):
        """Test creating/resetting demo entity P_DEMO_001 in memory."""
        df = create_demo_entity("P_DEMO_001")
        self.assertIsNotNone(df)
        
        matches = df[df["entity_id"] == "P_DEMO_001"]
        self.assertEqual(len(matches), 1)
        row = matches.iloc[0]
        self.assertEqual(row["entity_type"], "Prospect")
        self.assertEqual(row["dynamic_class"], "Cold Prospect")
        mock_save_snap.assert_called_once()

    @patch("journey.journey_repository.is_postgres_available", return_value=True)
    @patch("journey.journey_repository.get_cursor")
    def test_create_scenario_repository(self, mock_cursor, mock_pg):
        """Test scenario repository creation query execution."""
        cursor_inst = MagicMock()
        cursor_inst.fetchone.return_value = {"scenario_id": 42}
        mock_cursor.return_value.__enter__.return_value = cursor_inst
        
        scen_id = create_journey_scenario({
            "scenario_name": "Test Scenario",
            "entity_id": "P_DEMO_001",
            "status": "Draft"
        })
        self.assertEqual(scen_id, 42)

    @patch("journey.journey_runner.get_journey_scenario_by_id")
    @patch("journey.journey_runner.get_journey_steps")
    @patch("journey.journey_runner.update_journey_scenario_status")
    @patch("journey.journey_runner.apply_journey_stage_events")
    @patch("journey.journey_runner.capture_entity_state")
    @patch("journey.journey_runner.insert_journey_step")
    def test_run_next_journey_step(
        self, mock_ins_step, mock_capture, mock_apply_ev, mock_upd_status, mock_get_steps, mock_get_scen
    ):
        """Test executing next journey step without LLM calls."""
        mock_get_scen.return_value = {"scenario_id": 10, "entity_id": "P_DEMO_001", "status": "Draft"}
        mock_get_steps.return_value = []
        mock_apply_ev.return_value = "E0000001"
        mock_ins_step.return_value = 101
        
        mock_capture.side_effect = [
            {
                "entity_id": "P_DEMO_001",
                "entity_type": "Prospect",
                "dynamic_class": "Cold Prospect",
                "customer_segment": "Prospect",
                "customer_persona": "New Explorer",
                "clv_amount": 0.0,
                "rfm_score": 0.15,
                "churn_risk": 0.10
            },
            {
                "entity_id": "P_DEMO_001",
                "entity_type": "Prospect",
                "dynamic_class": "Warm Prospect",
                "customer_segment": "Prospect",
                "customer_persona": "New Explorer",
                "clv_amount": 0.0,
                "rfm_score": 0.35,
                "churn_risk": 0.10
            }
        ]
        
        step = run_next_journey_step(10)
        self.assertIsNotNone(step)
        self.assertEqual(step["step_order"], 1)
        self.assertEqual(step["stage_name"], "1. New Prospect")
        self.assertEqual(step["before_dynamic_class"], "Cold Prospect")
        self.assertEqual(step["after_dynamic_class"], "Warm Prospect")
        mock_upd_status.assert_called_with(10, "Running")

    def test_render_journey_tree_mermaid(self):
        """Test generating Mermaid flowchart string for 5-stage tree."""
        mock_steps = [
            {"step_order": 1, "stage_name": "1. New Prospect", "after_dynamic_class": "Warm Prospect", "after_segment": "Prospect", "after_persona": "New Explorer"},
            {"step_order": 2, "stage_name": "2. Warm Prospect", "after_dynamic_class": "Warm Prospect", "after_segment": "Prospect", "after_persona": "New Explorer"}
        ]
        mermaid_str = render_journey_tree_mermaid(mock_steps)
        self.assertIn("flowchart TD", mermaid_str)
        self.assertIn("1. New Prospect", mermaid_str)
        self.assertIn("N1 --> N2", mermaid_str)

    @patch("llm.llm_client.is_llm_enabled", return_value=False)
    def test_generate_llm_journey_explanation_optional(self, mock_llm):
        """Test that LLM explanation generator is optional and returns untouched step if LLM disabled."""
        step = {"stage_name": "1. New Prospect", "before_dynamic_class": "Cold Prospect"}
        res = generate_llm_journey_explanation(step)
        self.assertEqual(res, step)

if __name__ == "__main__":
    unittest.main()
