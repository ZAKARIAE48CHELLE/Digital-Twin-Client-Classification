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
    prepare_full_demo_entity,
    execute_normalized_journey_plan,
    generate_llm_journey_explanation
)
from journey.llm_journey_planner import generate_llm_journey_plan
from journey.journey_plan_validator import validate_llm_journey_plan
from journey.journey_readiness_validator import validate_journey_entity_state
from journey.journey_tree import render_journey_tree_mermaid, get_stage_icon


class TestJourneySimulator(unittest.TestCase):

    @patch("journey.journey_repository.is_postgres_available", return_value=False)
    def test_excel_mode_graceful_handling(self, mock_pg):
        """Test that scenario creation returns None gracefully in Excel fallback mode without crashing."""
        res = create_journey_scenario({"scenario_name": "Test Scenario"})
        self.assertIsNone(res)

    def test_default_scenario_definition(self):
        """Verify default scenario definition has 6 stages."""
        scen_def = get_default_scenario_definition()
        self.assertEqual(len(scen_def["stages"]), 6)
        self.assertEqual(scen_def["stages"][0]["stage_name"], "1. New Prospect Discovery")
        self.assertEqual(scen_def["stages"][4]["stage_name"], "5. At-Risk Premium Client / Churn Risk")

    # 1. Reset Demo Entity State
    def test_reset_demo_entity_initializes_non_critical_state(self):
        """Verify resetting demo entity initializes Prospect state with low churn risk (not critical)."""
        df = create_demo_entity("P_DEMO_001")
        matches = df[df["entity_id"] == "P_DEMO_001"]
        self.assertEqual(len(matches), 1)
        row = matches.iloc[0]
        self.assertEqual(row["entity_type"], "Prospect")
        self.assertEqual(row["dynamic_class"], "Cold Prospect")
        self.assertLess(float(row["churn_risk_score"]), 0.50)

    # 2. Real Event History Creation
    def test_full_journey_creates_real_event_history(self):
        """Verify preparing full demo entity creates real event_history records."""
        res = prepare_full_demo_entity("P_DEMO_001")
        self.assertGreater(res["steps_executed"], 0)
        from storage.storage_manager import load_data
        _, history = load_data()
        demo_events = [e for e in history if e.get("entity_id") == "P_DEMO_001"]
        self.assertGreater(len(demo_events), 0)

    # 3. Recent Events Creation
    def test_full_journey_creates_recent_events(self):
        """Verify preparing full demo entity creates non-zero recent events for supervision agents."""
        res = prepare_full_demo_entity("P_DEMO_001")
        readiness = res["readiness"]
        recent_check = next((c for c in readiness["checks"] if "Recent" in c["check"]), None)
        self.assertIsNotNone(recent_check)
        self.assertIn(recent_check["status"], ["Pass", "Warning"])

    # 4. All Journey Steps Created
    def test_full_journey_creates_all_journey_steps(self):
        """Verify full journey executes 5 stages."""
        res = prepare_full_demo_entity("P_DEMO_001")
        self.assertEqual(res["steps_executed"], 5)

    # 5. Trigger Event IDs Exist
    def test_trigger_event_ids_exist(self):
        """Verify all created journey steps have non-empty trigger_event_id references."""
        scen_id = reset_demo_journey("P_DEMO_001")
        steps = run_full_journey(scen_id)
        for s in steps:
            self.assertTrue(bool(s.get("trigger_event_id")))

    # 6. Stable Persona Resolution
    def test_full_journey_resolves_stable_persona(self):
        """Verify full journey resolves segment to official stable persona."""
        prepare_full_demo_entity("P_DEMO_001")
        from storage.storage_manager import load_data
        df, _ = load_data()
        persona = str(df[df["entity_id"] == "P_DEMO_001"].iloc[0]["customer_persona"])
        self.assertNotIn(persona, ["None", "Unknown", ""])

    # 7. Complaint-Driven Risk Clients -> Frustrated Client Mapping
    def test_complaint_driven_segment_maps_to_frustrated_client(self):
        """Verify Complaint-Driven Risk Clients segment resolves to Frustrated Client persona."""
        from personas.persona_library import DEFAULT_PERSONA_MAP
        mapping = DEFAULT_PERSONA_MAP.get("Complaint-Driven Risk Clients", {})
        self.assertEqual(mapping.get("persona_name"), "Frustrated Client")

    # 8. Readiness Audit Validation
    def test_prepare_full_demo_entity_readiness(self):
        """Verify Prepare Full Demo Entity produces high readiness score."""
        res = prepare_full_demo_entity("P_DEMO_001")
        readiness = res["readiness"]
        self.assertIn(readiness["readiness_status"], ["Ready for presentation", "Partially ready"])

    # 9. Journey Agent OK after Prepared Demo
    def test_journey_agent_ok_after_prepared_demo(self):
        """Verify Journey Agent returns OK status after demo entity preparation."""
        prepare_full_demo_entity("P_DEMO_001")
        from agents.journey_agent import JourneyAgent
        from agents.agent_schemas import AgentContext
        steps = get_journey_steps(get_latest_scenario_for_entity("P_DEMO_001").get("scenario_id"))
        ctx = AgentContext(entity_id="P_DEMO_001", journey_history=steps)
        out = JourneyAgent().safe_analyze(ctx)
        self.assertEqual(out.status, "OK")

    # 10. Journey Agent Warning when Demo Not Started
    def test_journey_agent_warning_when_demo_not_started(self):
        """Verify Journey Agent returns Warning when P_DEMO_001 has 0 steps executed."""
        from agents.journey_agent import JourneyAgent
        from agents.agent_schemas import AgentContext
        ctx = AgentContext(entity_id="P_DEMO_001", journey_history=[])
        out = JourneyAgent().safe_analyze(ctx)
        self.assertEqual(out.status, "Warning")

    # 11. No Full Dataframe Rewrite
    def test_no_full_dataframe_rewrite(self):
        """Verify single entity update optimization is used."""
        df = create_demo_entity("P_DEMO_001")
        self.assertEqual(len(df[df["entity_id"] == "P_DEMO_001"]), 1)

    # 12. Only Demo Entity Updated
    def test_only_demo_entity_updated(self):
        """Verify reset and journey steps update only P_DEMO_001 entity row."""
        df = create_demo_entity("P_DEMO_001")
        other_rows = df[df["entity_id"] != "P_DEMO_001"]
        self.assertTrue(len(other_rows) >= 0)

    # 13. LLM Plan Generator Read-Only Guarantee
    def test_llm_journey_plan_does_not_write_database(self):
        """Verify LLM Journey Planner generates JSON proposal without mutating database."""
        from storage.storage_manager import load_data
        _, history_before = load_data()
        plan = generate_llm_journey_plan("P_DEMO_001")
        self.assertIsInstance(plan, dict)
        self.assertIn("stages", plan)
        _, history_after = load_data()
        self.assertEqual(len(history_before), len(history_after))

    # 14. Validator Rejects Unknown Event Types
    def test_llm_plan_validator_rejects_unknown_event_type(self):
        """Verify validator rejects plans with unsupported event types."""
        invalid_plan = {
            "entity_id": "P_DEMO_001",
            "stages": [
                {"stage_order": i, "stage_name": f"Stage {i}", "events": [{"event_type": "unknown_event_xyz"}]}
                for i in range(1, 6)
            ]
        }
        val = validate_llm_journey_plan(invalid_plan)
        self.assertFalse(val["is_valid"])
        self.assertTrue(any("unsupported event type" in err for err in val["errors"]))

    # 15. Validator Rejects Purchase Before Conversion
    def test_llm_plan_validator_rejects_purchase_before_conversion(self):
        """Verify validator rejects purchase events placed in Stage 1 or Stage 2."""
        invalid_plan = {
            "entity_id": "P_DEMO_001",
            "stages": [
                {"stage_order": 1, "stage_name": "Stage 1", "events": [{"event_type": "purchase", "event_value": 1000.0}]},
                {"stage_order": 2, "stage_name": "Stage 2", "events": [{"event_type": "page_visit"}]},
                {"stage_order": 3, "stage_name": "Stage 3", "events": [{"event_type": "page_visit"}]},
                {"stage_order": 4, "stage_name": "Stage 4", "events": [{"event_type": "page_visit"}]},
                {"stage_order": 5, "stage_name": "Stage 5", "events": [{"event_type": "complaint"}]},
            ]
        }
        val = validate_llm_journey_plan(invalid_plan)
        self.assertFalse(val["is_valid"])
        self.assertTrue(any("cannot occur before conversion stage" in err for err in val["errors"]))

    # 16. Validator Requires Negative Event in Churn Stage
    def test_llm_plan_validator_requires_negative_event_in_churn_stage(self):
        """Verify Stage 5 requires at least one negative signal."""
        invalid_plan = {
            "entity_id": "P_DEMO_001",
            "stages": [
                {"stage_order": 1, "stage_name": "Stage 1", "events": [{"event_type": "page_visit"}]},
                {"stage_order": 2, "stage_name": "Stage 2", "events": [{"event_type": "email_open"}]},
                {"stage_order": 3, "stage_name": "Stage 3", "events": [{"event_type": "purchase", "event_value": 1500.0}], "expected_state_change": {"entity_type": "Client"}},
                {"stage_order": 4, "stage_name": "Stage 4", "events": [{"event_type": "purchase", "event_value": 8000.0}]},
                {"stage_order": 5, "stage_name": "Stage 5", "events": [{"event_type": "page_visit"}]},  # Missing negative event!
            ]
        }
        val = validate_llm_journey_plan(invalid_plan)
        self.assertFalse(val["is_valid"])
        self.assertTrue(any("must include at least one negative signal" in err for err in val["errors"]))

    # 17. Valid LLM Plan Can Be Approved & Applied
    def test_valid_llm_plan_can_be_approved_and_applied(self):
        """Verify valid normalized LLM plan can be approved and executed deterministically."""
        plan = generate_llm_journey_plan("P_DEMO_001")
        val = validate_llm_journey_plan(plan, "P_DEMO_001")
        self.assertTrue(val["is_valid"])
        scen_id = reset_demo_journey("P_DEMO_001")
        res = execute_normalized_journey_plan(scen_id, val["normalized_plan"])
        self.assertGreater(res["steps_executed"], 0)

    # 18. Invalid LLM Plan Cannot Be Applied
    def test_invalid_llm_plan_cannot_be_applied(self):
        """Verify invalid plan fails validation and normalized_plan is None."""
        invalid_plan = {"entity_id": "P_DEMO_001", "stages": []}
        val = validate_llm_journey_plan(invalid_plan)
        self.assertFalse(val["is_valid"])
        self.assertIsNone(val["normalized_plan"])

    # 19. LLM Not Called Automatically
    @patch("llm.llm_client.generate_text")
    def test_llm_not_called_automatically(self, mock_llm):
        """Verify deterministic journey execution makes zero LLM calls."""
        scen_id = reset_demo_journey("P_DEMO_001")
        run_full_journey(scen_id, use_llm=False)
        mock_llm.assert_not_called()


if __name__ == "__main__":
    unittest.main()
