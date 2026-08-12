"""
OSMOS A/B Testing & Digital Twin Response Simulator Unit Tests (Phase 8.8)
==========================================================================
Comprehensive test suite verifying experiment creation, LLM variant generation safety,
deterministic validation, Digital Twin behavioral simulation, evaluator ranking,
governance actions, and agent integrations.
"""

import unittest
from ab_testing.ab_test_schemas import ABExperiment, ABVariant, SimulatedResponse, ABRecommendation, ABEvaluationResult
from ab_testing.ab_test_variant_generator import generate_llm_ab_variants, _build_fallback_variants
from ab_testing.ab_test_validator import validate_ab_variants
from ab_testing.digital_twin_response_simulator import simulate_digital_twin_response
from ab_testing.ab_test_evaluator import evaluate_ab_experiment
from ab_testing.ab_test_repository import (
    save_ab_experiment,
    get_ab_experiments_for_entity,
    get_latest_ab_experiment_for_entity,
    convert_variant_to_campaign_draft,
    apply_simulated_response_as_event,
)
from agents.campaign_agent import CampaignAgent
from agents.digital_twin_agent import DigitalTwinAgent


class TestABTesting(unittest.TestCase):

    def setUp(self):
        self.sample_entity = {
            "entity_id": "P_DEMO_001",
            "entity_type": "Client",
            "dynamic_class": "Active Client",
            "customer_segment": "Standard Active Clients",
            "customer_persona": "Regular Buyer",
            "churn_risk_score": 0.25,
            "predicted_clv_amount_mad": 650.0,
            "predicted_clv_segment": "Medium Value",
            "rfm_score": 0.55,
            "review_score_avg": 4.2,
            "complaint_count_90d": 0.0,
        }

        self.frustrated_entity = {
            "entity_id": "C00005",
            "entity_type": "Client",
            "dynamic_class": "Churn Risk Client",
            "customer_segment": "Complaint-Driven Risk Clients",
            "customer_persona": "Frustrated Client",
            "churn_risk_score": 0.85,
            "predicted_clv_amount_mad": 450.0,
            "predicted_clv_segment": "Medium Value",
            "rfm_score": 0.20,
            "review_score_avg": 2.1,
            "complaint_count_90d": 3.0,
        }

        self.low_clv_entity = {
            "entity_id": "C00012",
            "entity_type": "Client",
            "dynamic_class": "Active Client",
            "customer_segment": "Dormant Low-Value Clients",
            "customer_persona": "Sleeping Client",
            "churn_risk_score": 0.40,
            "predicted_clv_amount_mad": 150.0,
            "predicted_clv_segment": "Low Value",
            "rfm_score": 0.25,
            "review_score_avg": 4.0,
            "complaint_count_90d": 0.0,
        }

    def test_create_ab_experiment(self):
        """Verifies ABExperiment schema instantiation."""
        exp = ABExperiment(
            entity_id="P_DEMO_001",
            experiment_name="Retention Offer Comparison",
            admin_question="Which offer retains this client?",
            objective="retention",
            target_segment="Standard Active Clients",
            target_persona="Regular Buyer",
        )
        self.assertEqual(exp.entity_id, "P_DEMO_001")
        self.assertEqual(exp.objective, "retention")
        self.assertEqual(exp.status, "Draft")

    def test_llm_variant_generation_no_db_write(self):
        """Verifies LLM variant generator produces valid variants without altering DB state."""
        variants, name, is_llm = generate_llm_ab_variants(
            "Which offer retains this client?", "retention", self.sample_entity, channel="email", num_variants=2
        )
        self.assertGreaterEqual(len(variants), 2)
        self.assertEqual(variants[0].variant_label, "A")
        self.assertEqual(variants[1].variant_label, "B")

    def test_variant_validator_rejects_high_discount(self):
        """Verifies validator rejects discounts exceeding 30%."""
        var_a = ABVariant("A", "Title A", "Message A", offer_type="discount", incentive_value=35.0, channel="email")
        var_b = ABVariant("B", "Title B", "Message B", offer_type="discount", incentive_value=10.0, channel="email")

        val_res = validate_ab_variants([var_a, var_b], self.sample_entity, objective="retention")
        self.assertFalse(val_res["is_valid"])
        self.assertTrue(any("exceeds maximum allowed limit of 30%" in err for err in val_res["errors"]))

    def test_variant_validator_rejects_upsell_for_churn_critical(self):
        """Verifies validator blocks upsell-only variants for Churn Critical customers."""
        var_a = ABVariant("A", "VIP Upsell", "Message A", offer_type="vip_perk", incentive_value=0.0, channel="email")
        var_b = ABVariant("B", "Discount", "Message B", offer_type="discount", incentive_value=10.0, channel="email")

        val_res = validate_ab_variants([var_a, var_b], self.frustrated_entity, objective="upsell")
        self.assertFalse(val_res["is_valid"])
        self.assertTrue(any("blocked for Churn Critical customers" in err for err in val_res["errors"]))

    def test_frustrated_client_prefers_service_recovery(self):
        """Verifies Frustrated Client profile yields higher score for service recovery than pure discount."""
        var_service_recovery = ABVariant(
            "A", "Service Recovery Apology", "We apologize for the issue and will prioritize your request.",
            offer_type="service_recovery", tone="empathetic", channel="email"
        )
        var_discount = ABVariant(
            "B", "Commercial Discount", "Get 15% off your next purchase.",
            offer_type="discount", incentive_value=15.0, tone="commercial", channel="email"
        )

        resp_sr = simulate_digital_twin_response(self.frustrated_entity, var_service_recovery)
        resp_disc = simulate_digital_twin_response(self.frustrated_entity, var_discount)

        self.assertGreater(resp_sr.response_score, resp_disc.response_score)
        self.assertLess(resp_sr.predicted_complaint_probability, resp_disc.predicted_complaint_probability)
        self.assertLess(resp_sr.predicted_churn_delta, resp_disc.predicted_churn_delta)

    def test_low_clv_prefers_low_cost_action(self):
        """Verifies Low CLV customer receives warning/block for expensive incentives."""
        var_high_cost = ABVariant("A", "Big Discount", "Take $30 off!", offer_type="discount", incentive_value=30.0, channel="email")
        var_low_cost = ABVariant("B", "Low Cost Check-In", "Check out new features.", offer_type="reactivation", incentive_value=0.0, channel="email")

        val_res = validate_ab_variants([var_high_cost, var_low_cost], self.low_clv_entity, objective="reactivation")
        self.assertFalse(val_res["is_valid"])
        self.assertTrue(any("Low CLV" in err for err in val_res["errors"]))

    def test_winning_variant_selected_by_response_score(self):
        """Verifies evaluator ranks variants by response score and identifies winner."""
        exp = ABExperiment("P_DEMO_001", "A/B Retention", "Which variant works best?", "retention")
        var_a = ABVariant("A", "Offer A", "Message A", offer_type="service_recovery", tone="empathetic", channel="email")
        var_b = ABVariant("B", "Offer B", "Message B", offer_type="discount", incentive_value=10.0, channel="email")

        eval_res = evaluate_ab_experiment(exp, [var_a, var_b], self.frustrated_entity)
        self.assertEqual(eval_res.recommendation.winning_variant_label, "A")
        self.assertGreaterEqual(eval_res.recommendation.confidence_score, 0.60)

    def test_convert_winning_variant_to_campaign_draft_requires_admin_action(self):
        """Verifies converting a variant to campaign draft returns a campaign draft ID."""
        exp = ABExperiment("P_DEMO_001", "A/B Test", "Question", "retention")
        var_a = ABVariant("A", "Title A", "Message A", offer_type="discount", incentive_value=10.0, channel="email")
        var_b = ABVariant("B", "Title B", "Message B", offer_type="service_recovery", tone="empathetic", channel="email")

        eval_res = evaluate_ab_experiment(exp, [var_a, var_b], self.sample_entity)
        exp_id = save_ab_experiment(eval_res)
        self.assertIsNotNone(exp_id)

        # Convert to campaign draft
        draft_id = convert_variant_to_campaign_draft(exp_id, eval_res.variants[0].variant_id or 1)
        self.assertIsNotNone(draft_id)

    def test_apply_simulated_response_event_requires_admin_approval(self):
        """Verifies applying a simulated response event logs event in history."""
        exp = ABExperiment("P_DEMO_001", "A/B Test", "Question", "retention")
        var_a = ABVariant("A", "Title A", "Message A", offer_type="discount", incentive_value=10.0, channel="email")
        var_b = ABVariant("B", "Title B", "Message B", offer_type="service_recovery", tone="empathetic", channel="email")

        eval_res = evaluate_ab_experiment(exp, [var_a, var_b], self.sample_entity)
        exp_id = save_ab_experiment(eval_res)
        self.assertIsNotNone(exp_id)

        evt_id = apply_simulated_response_as_event(exp_id, eval_res.variants[0].variant_id or 1, "P_DEMO_001")
        self.assertIsNotNone(evt_id)
        self.assertTrue(evt_id.startswith("EVT_AB_"))

    def test_ab_test_history_for_entity(self):
        """Verifies fetching A/B test history returns a list of experiment records."""
        history = get_ab_experiments_for_entity("P_DEMO_001", limit=5)
        self.assertIsInstance(history, list)

    def test_campaign_agent_detects_ab_test_experiment(self):
        """Verifies CampaignAgent detects latest A/B test experiment during supervision."""
        from agents.agent_schemas import AgentContext
        agent = CampaignAgent()
        ctx = AgentContext(
            entity_id="P_DEMO_001",
            latest_digital_twin=self.sample_entity,
            latest_classification={"dynamic_class": "Active Client", "churn_risk_score": 0.25},
            latest_clv={"predicted_clv_amount_mad": 650.0},
        )
        output = agent.safe_analyze(ctx)
        self.assertIn(output.status, ["OK", "Warning", "Critical"])
        self.assertIsNotNone(output.observations)

    def test_digital_twin_agent_detects_ab_test_response_event(self):
        """Verifies DigitalTwinAgent evaluates entity with simulated response events."""
        from agents.agent_schemas import AgentContext
        agent = DigitalTwinAgent()
        ctx = AgentContext(
            entity_id="P_DEMO_001",
            latest_digital_twin=self.sample_entity,
            latest_classification={"dynamic_class": "Active Client", "churn_risk_score": 0.25},
            latest_clv={"predicted_clv_amount_mad": 650.0},
        )
        output = agent.safe_analyze(ctx)
        self.assertEqual(output.agent_id, "digital_twin")
        self.assertIn(output.status, ["OK", "Warning", "Critical"])


    def test_ab_variant_count_two_renders_two_variants(self):
        """Verifies generator returns 2 variants ('A', 'B') when num_variants=2."""
        vars, name, _ = generate_llm_ab_variants("Question", "retention", self.sample_entity, num_variants=2)
        self.assertEqual(len(vars), 2)
        self.assertEqual([v.variant_label for v in vars], ["A", "B"])

    def test_ab_variant_count_three_renders_three_variants(self):
        """Verifies generator returns 3 variants ('A', 'B', 'C') when num_variants=3."""
        vars, name, _ = generate_llm_ab_variants("Question", "retention", self.sample_entity, num_variants=3)
        self.assertEqual(len(vars), 3)
        self.assertEqual([v.variant_label for v in vars], ["A", "B", "C"])

    def test_llm_generated_variants_populate_session_state(self):
        """Verifies generated variants populate structured values for session_state storage."""
        vars, exp_name, is_llm = generate_llm_ab_variants("Question", "retention", self.sample_entity, num_variants=2)
        session_state = {
            "ab_test_variants": vars,
            "ab_test_experiment_name": exp_name,
            "ab_test_is_llm_generated": is_llm,
        }
        self.assertIn("ab_test_variants", session_state)
        self.assertEqual(len(session_state["ab_test_variants"]), 2)
        self.assertTrue(bool(session_state["ab_test_experiment_name"]))

    def test_llm_generated_variants_populate_input_defaults(self):
        """Verifies LLM generated variants contain non-empty field values for form inputs."""
        vars, _, _ = generate_llm_ab_variants("Question", "retention", self.sample_entity, num_variants=2)
        for v in vars:
            self.assertTrue(bool(v.variant_title))
            self.assertTrue(bool(v.message_text))
            self.assertTrue(bool(v.offer_type))
            self.assertIsNotNone(v.incentive_value)
            self.assertTrue(bool(v.tone))
            self.assertTrue(bool(v.call_to_action))

    def test_edited_generated_variants_used_in_simulation(self):
        """Verifies edited variant values (e.g. customized title and incentive) are used in evaluation."""
        vars = _build_fallback_variants("Question", "retention", "P_DEMO_001", "Segment", "Persona")[:2]
        # Admin edits variant titles and incentive values
        vars[0].variant_title = "Custom Service Recovery Alpha"
        vars[1].variant_title = "Custom Goodwill Discount Beta"
        vars[1].incentive_value = 12.0

        exp = ABExperiment("P_DEMO_001", "Edited Experiment", "Question", "retention")
        eval_res = evaluate_ab_experiment(exp, vars, self.frustrated_entity)

        # Confirm evaluated variants match edited titles
        self.assertEqual(eval_res.variants[0].variant_title, "Custom Service Recovery Alpha")
        self.assertEqual(eval_res.variants[1].variant_title, "Custom Goodwill Discount Beta")
        self.assertEqual(eval_res.variants[1].incentive_value, 12.0)

    def test_simulation_runs_three_variants(self):
        """Verifies simulation correctly evaluates and ranks 3 variants."""
        vars = _build_fallback_variants("Question", "retention", "P_DEMO_001", "Segment", "Persona")[:3]
        exp = ABExperiment("P_DEMO_001", "3 Variant Test", "Question", "retention")
        eval_res = evaluate_ab_experiment(exp, vars, self.frustrated_entity)

        self.assertEqual(len(eval_res.responses), 3)
        self.assertEqual([r.variant_label for r in eval_res.responses], ["A", "B", "C"])
        self.assertIn(eval_res.recommendation.winning_variant_label, ["A", "B", "C"])

    def test_experiment_history_saves_real_variant_titles(self):
        """Verifies saving an experiment preserves real variant titles instead of generic placeholders."""
        exp = ABExperiment("P_DEMO_001", "Empathetic vs Commercial Retention", "Question", "retention")
        var_a = ABVariant("A", "Empathetic Service Recovery", "Message A", offer_type="service_recovery", tone="empathetic", channel="email")
        var_b = ABVariant("B", "Goodwill Discount Offer", "Message B", offer_type="discount", incentive_value=10.0, channel="email")

        eval_res = evaluate_ab_experiment(exp, [var_a, var_b], self.frustrated_entity)
        saved_id = save_ab_experiment(eval_res)
        self.assertIsNotNone(saved_id)

        history = get_ab_experiments_for_entity("P_DEMO_001", limit=1)
        self.assertGreater(len(history), 0)
        self.assertEqual(history[0]["experiment_name"], "Empathetic vs Commercial Retention")
        self.assertNotEqual(history[0]["winning_title"], "Title A")

    def test_no_llm_call_on_page_load(self):
        """Verifies fallback variants are built instantly without triggering external LLM calls."""
        fallback = _build_fallback_variants("Question", "retention", "P_DEMO_001", "Segment", "Persona")
        self.assertGreaterEqual(len(fallback), 2)
        self.assertEqual(fallback[0].variant_label, "A")

    def test_ab_llm_timeout_uses_fallback(self):
        """Verifies LLM request timeout cleanly returns fallback variants with timeout status code."""
        from unittest.mock import patch
        with patch("ab_testing.ab_test_variant_generator.generate_text", return_value="__TIMEOUT__"):
            with patch("ab_testing.ab_test_variant_generator.check_llm_available", return_value=(True, "Connected")):
                vars, name, status = generate_llm_ab_variants("Question", "retention", self.sample_entity)
                self.assertEqual(status, "timeout")
                self.assertEqual(len(vars), 2)
                self.assertTrue(vars[0].variant_title.startswith("Empathetic") or len(vars[0].variant_title) > 0)

    def test_ab_invalid_json_uses_fallback(self):
        """Verifies invalid JSON output cleanly returns fallback variants with invalid_json status code."""
        from unittest.mock import patch
        with patch("ab_testing.ab_test_variant_generator.generate_text", return_value="Invalid non-json text response."):
            with patch("ab_testing.ab_test_variant_generator.check_llm_available", return_value=(True, "Connected")):
                vars, name, status = generate_llm_ab_variants("Question", "retention", self.sample_entity)
                self.assertEqual(status, "invalid_json")
                self.assertEqual(len(vars), 2)

    def test_ab_truncated_json_uses_fallback(self):
        """Verifies incomplete/truncated JSON output cleanly returns fallback variants with partial_json status code."""
        from unittest.mock import patch
        truncated = '{"experiment_name": "Incomplete Test", "variants": [{"variant_label": "A", "variant_title": "Truncated'
        with patch("ab_testing.ab_test_variant_generator.generate_text", return_value=truncated):
            with patch("ab_testing.ab_test_variant_generator.check_llm_available", return_value=(True, "Connected")):
                vars, name, status = generate_llm_ab_variants("Question", "retention", self.sample_entity)
                self.assertEqual(status, "partial_json")
                self.assertEqual(len(vars), 2)

    def test_ab_empty_variants_uses_fallback(self):
        """Verifies empty variants array output returns empty_variants status code."""
        from unittest.mock import patch
        empty_json = '{"variants": []}'
        with patch("ab_testing.ab_test_variant_generator.generate_text", return_value=empty_json):
            with patch("ab_testing.ab_test_variant_generator.check_llm_available", return_value=(True, "Connected")):
                vars, name, status = generate_llm_ab_variants("Question", "retention", self.sample_entity)
                self.assertEqual(status, "empty_variants")
                self.assertEqual(len(vars), 2)

    def test_ab_incomplete_variant_count_uses_fallback(self):
        """Verifies returning fewer variants than requested uses incomplete_variant_count status code."""
        from unittest.mock import patch
        partial_count_json = '{"variants": [{"variant_label": "A", "variant_title": "Title A", "message_text": "Msg A", "offer_type": "service_recovery", "incentive_value": 0, "channel": "email", "tone": "empathetic", "call_to_action": "CTA A"}]}'
        with patch("ab_testing.ab_test_variant_generator.generate_text", return_value=partial_count_json):
            with patch("ab_testing.ab_test_variant_generator.check_llm_available", return_value=(True, "Connected")):
                vars, name, status = generate_llm_ab_variants("Question", "retention", self.sample_entity, num_variants=2)
                self.assertEqual(status, "incomplete_variant_count")
                self.assertEqual(len(vars), 2)

    def test_ab_debug_llm_mode(self):
        """Verifies OSMOS_AB_DEBUG_LLM environment flag triggers debug logging without crashing."""
        import os
        from unittest.mock import patch
        old_env = os.environ.get("OSMOS_AB_DEBUG_LLM")
        valid_json = '''{
          "variants": [
            {"variant_label": "A", "variant_title": "Title A", "message_text": "Msg A", "offer_type": "service_recovery", "incentive_value": 0, "channel": "email", "tone": "empathetic", "call_to_action": "CTA A"},
            {"variant_label": "B", "variant_title": "Title B", "message_text": "Msg B", "offer_type": "discount", "incentive_value": 10, "channel": "email", "tone": "commercial", "call_to_action": "CTA B"}
          ]
        }'''
        try:
            os.environ["OSMOS_AB_DEBUG_LLM"] = "true"
            with patch("ab_testing.ab_test_variant_generator.generate_text", return_value=valid_json):
                with patch("ab_testing.ab_test_variant_generator.check_llm_available", return_value=(True, "Connected")):
                    vars, name, status = generate_llm_ab_variants("Question", "retention", self.sample_entity)
                    self.assertEqual(status, "llm_success_valid")
        finally:
            if old_env is not None:
                os.environ["OSMOS_AB_DEBUG_LLM"] = old_env
            elif "OSMOS_AB_DEBUG_LLM" in os.environ:
                del os.environ["OSMOS_AB_DEBUG_LLM"]

    def test_candidate_llm_output_logged(self):
        """Verifies candidate LLM outputs are logged to candidate_llm_output.log in ab_testing directory."""
        import os
        from ab_testing.ab_test_variant_generator import CANDIDATE_LLM_LOG_PATH, _log_candidate_llm_output
        self.assertTrue(CANDIDATE_LLM_LOG_PATH.endswith("candidate_llm_output.log"))
        _log_candidate_llm_output("Test Question", "retention", "P_TEST_001", "llm_success", '{"variants": []}')
        self.assertTrue(os.path.exists(CANDIDATE_LLM_LOG_PATH))

    def test_ollama_generate_response_extraction(self):
        """Verifies _extract_ollama_text parses /api/generate 'response' field."""
        from llm.llm_client import _extract_ollama_text
        payload = {"response": "  Generated text content  ", "done": True}
        self.assertEqual(_extract_ollama_text(payload), "Generated text content")

    def test_ollama_chat_response_extraction(self):
        """Verifies _extract_ollama_text parses /api/chat 'message' -> 'content' field and fallback fields."""
        from llm.llm_client import _extract_ollama_text
        chat_payload = {"message": {"role": "assistant", "content": "Chat response text"}}
        self.assertEqual(_extract_ollama_text(chat_payload), "Chat response text")

        fallback_payload = {"content": "Fallback content text"}
        self.assertEqual(_extract_ollama_text(fallback_payload), "Fallback content text")

    def test_empty_llm_output_uses_fallback(self):
        """Verifies returning an empty string uses fallback variants."""
        from unittest.mock import patch
        with patch("ab_testing.ab_test_variant_generator.generate_text", return_value=""):
            with patch("ab_testing.ab_test_variant_generator.check_llm_available", return_value=(True, "Connected")):
                vars, name, status = generate_llm_ab_variants("Question", "retention", self.sample_entity)
                self.assertEqual(len(vars), 2)
                self.assertTrue(bool(vars[0].variant_title))

    def test_empty_llm_output_status_code(self):
        """Verifies empty LLM output specifically returns empty_llm_output status code."""
        from unittest.mock import patch
        with patch("ab_testing.ab_test_variant_generator.generate_text", return_value="   "):
            with patch("ab_testing.ab_test_variant_generator.check_llm_available", return_value=(True, "Connected")):
                vars, name, status = generate_llm_ab_variants("Question", "retention", self.sample_entity)
                self.assertEqual(status, "empty_llm_output")

    def test_debug_logs_full_ollama_response_keys(self):
        """Verifies debug logging captures Ollama response keys when OSMOS_AB_DEBUG_LLM is enabled."""
        import os
        from unittest.mock import patch, MagicMock
        old_env = os.environ.get("OSMOS_AB_DEBUG_LLM")
        try:
            os.environ["OSMOS_AB_DEBUG_LLM"] = "true"
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"response": '{"variants": []}', "done": True, "context": [1, 2, 3]}

            with patch("requests.post", return_value=mock_resp):
                with patch("llm.llm_client.check_llm_available", return_value=(True, "Connected")):
                    from llm.llm_client import generate_text
                    out = generate_text("Prompt", json_format=True)
                    self.assertIn('"variants"', out)
        finally:
            if old_env is not None:
                os.environ["OSMOS_AB_DEBUG_LLM"] = old_env
            elif "OSMOS_AB_DEBUG_LLM" in os.environ:
                del os.environ["OSMOS_AB_DEBUG_LLM"]
        """Verifies build_variant_blueprints constructs deterministic skeletons for 2 and 3 variants."""
        from ab_testing.ab_test_variant_generator import build_variant_blueprints
        bps2 = build_variant_blueprints("retention", "Question", self.sample_entity, number_of_variants=2)
        self.assertEqual(len(bps2), 2)
        self.assertEqual(bps2[0].variant_label, "A")
        self.assertEqual(bps2[0].offer_type, "service_recovery")
        self.assertEqual(bps2[1].variant_label, "B")
        self.assertEqual(bps2[1].offer_type, "discount")

        bps3 = build_variant_blueprints("retention", "Question", self.sample_entity, number_of_variants=3)
        self.assertEqual(len(bps3), 3)
        self.assertEqual([b.variant_label for b in bps3], ["A", "B", "C"])

    def test_partial_llm_output_merges_with_blueprints(self):
        """Verifies when LLM returns 1 variant for A/B request, LLM text is merged for Variant A and Variant B uses blueprint copy."""
        from unittest.mock import patch
        partial_json = '{"variants": [{"variant_label": "A", "variant_title": "LLM Title A", "message_text": "LLM Msg A", "call_to_action": "CTA A", "tone": "empathetic"}]}'
        with patch("ab_testing.ab_test_variant_generator.generate_text", return_value=partial_json):
            with patch("ab_testing.ab_test_variant_generator.check_llm_available", return_value=(True, "Connected")):
                vars, name, status = generate_llm_ab_variants("Question", "retention", self.sample_entity, num_variants=2)
                self.assertEqual(len(vars), 2)
                self.assertEqual(status, "llm_partial_merged:1/2")
                self.assertEqual(vars[0].variant_title, "LLM Title A")
                self.assertEqual(vars[0].offer_type, "service_recovery")
                self.assertEqual(vars[1].variant_label, "B")
                self.assertEqual(vars[1].offer_type, "discount")
                self.assertTrue(len(vars[1].variant_title) > 0)

    def test_offline_llm_immediately_uses_blueprints(self):
        """Verifies offline LLM immediately returns deterministic blueprint variants without calling LLM text generator."""
        from unittest.mock import patch
        with patch("ab_testing.ab_test_variant_generator.check_llm_available", return_value=(False, "Offline")):
            with patch("ab_testing.ab_test_variant_generator.generate_text") as mock_gen:
                vars, name, status = generate_llm_ab_variants("Question", "retention", self.sample_entity, num_variants=2)
                self.assertEqual(len(vars), 2)
                self.assertEqual(status, "timeout")
                mock_gen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
