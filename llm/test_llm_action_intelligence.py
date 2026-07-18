import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import llm.llm_config as llm_config
import llm.json_utils as json_utils
import llm.prompt_templates as prompts
import llm.llm_client as llm_client
import llm.action_intelligence as action_intel

class TestLlmActionIntelligence(unittest.TestCase):

    def test_prompt_generation(self):
        ctx = "Customer C00001 had a 30% drop in CLV"
        p = prompts.explain_clv_alert_prompt(ctx)
        self.assertIn("Customer C00001", p)
        self.assertIn("summary_fr", p)

    @patch('llm.llm_client.is_llm_enabled')
    def test_llm_disabled_behavior(self, mock_enabled):
        mock_enabled.return_value = False
        available, reason = llm_client.check_llm_available()
        self.assertFalse(available)
        self.assertIn("disabled", reason)

    def test_json_parsing_fallback(self):
        bad_json = "This is not json at all."
        parsed = json_utils.extract_and_parse_json(bad_json)
        self.assertEqual(parsed["confidence"], "Low")
        self.assertIn("Impossible", parsed["summary_fr"])

    @patch('llm.llm_client.requests.get')
    @patch('llm.llm_client.is_llm_enabled')
    def test_ollama_unavailable_behavior(self, mock_enabled, mock_get):
        mock_enabled.return_value = True
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Reset check cache
        llm_client._last_check_time = 0.0
        
        available, reason = llm_client.check_llm_available()

        self.assertFalse(available)
        self.assertIn("offline", reason)

    @patch('database.action_recommendations_repository.get_cursor')
    def test_recommendation_insertion_mock(self, mock_get_cursor):
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {'id': 99}
        
        # Mock connection context manager
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        
        # Set cursor context manager yield to mock_cur
        mock_get_cursor.return_value.__enter__.return_value = mock_cur
        
        from database.action_recommendations_repository import insert_llm_action_recommendation
        res = insert_llm_action_recommendation({
            "entity_id": "C00001",
            "alert_type": "CLV Drop Alert",
            "alert_level": "High",
            "summary_fr": "Alerte de baisse de CLV",
            "priority": "High"
        })
        self.assertEqual(res, 99)

if __name__ == "__main__":
    unittest.main()
