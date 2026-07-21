import unittest
from unittest.mock import patch, MagicMock
from campaigns.campaign_repository import (
    create_campaign_dispatch,
    get_campaign_dispatches,
    get_campaign_by_id,
    update_campaign_status,
    insert_campaign_response,
    get_campaign_responses,
    get_campaign_metrics
)
from campaigns.campaign_dispatcher import (
    create_campaign_from_recommendation,
    create_campaign_from_digital_twin_action,
    approve_campaign,
    simulate_dispatch,
    cancel_campaign
)
from campaigns.campaign_simulator import (
    determine_probabilistic_response,
    simulate_campaign_response,
    RESPONSE_TO_EVENT_MAP
)

class TestCampaignSimulation(unittest.TestCase):

    @patch("campaigns.campaign_repository.is_postgres_available", return_value=False)
    def test_excel_mode_graceful_handling(self, mock_pg):
        """Test that campaign creation returns None gracefully in Excel fallback mode without crashing."""
        res = create_campaign_dispatch({"campaign_title": "Test Campaign"})
        self.assertIsNone(res)
        
        metrics = get_campaign_metrics()
        self.assertEqual(metrics["total_campaigns"], 0)
        self.assertEqual(metrics["simulated_dispatches"], 0)

    @patch("campaigns.campaign_repository.is_postgres_available", return_value=True)
    @patch("campaigns.campaign_repository.get_cursor")
    def test_create_and_get_campaign(self, mock_cursor, mock_pg):
        """Test creation and fetching of campaign dispatch draft."""
        cursor_instance = MagicMock()
        cursor_instance.fetchone.return_value = {"campaign_id": 101}
        mock_cursor.return_value.__enter__.return_value = cursor_instance
        
        cid = create_campaign_dispatch({
            "entity_id": "C00001",
            "campaign_type": "VIP Loyalty Campaign",
            "campaign_channel": "Email",
            "campaign_title": "VIP Reward",
            "status": "Draft"
        })
        self.assertEqual(cid, 101)

    @patch("campaigns.campaign_dispatcher.get_campaign_by_id")
    @patch("campaigns.campaign_dispatcher.update_campaign_status")
    def test_approve_and_simulate_dispatch(self, mock_update_status, mock_get_campaign):
        """Test approving and simulating dispatch without sending real emails/SMS."""
        mock_get_campaign.return_value = {"campaign_id": 5, "entity_id": "C00001", "status": "Draft"}
        mock_update_status.return_value = True
        
        # Test approval
        app_res = approve_campaign(5)
        self.assertTrue(app_res)
        
        # Test simulated dispatch
        disp_res = simulate_dispatch(5)
        self.assertTrue(disp_res)

    @patch("campaigns.campaign_simulator.build_digital_twin_profile")
    def test_probabilistic_response_logic(self, mock_profile):
        """Test automatic probabilistic response simulation returns valid type."""
        mock_profile.return_value = {
            "scores": {"churn_risk": "Low Risk", "engagement_score": "High Engagement"},
            "behavioral_state": {"total_spent_90d_mad": 15000.0, "complaint_count_90d": 0}
        }
        
        resp = determine_probabilistic_response("C00001")
        self.assertIn(resp, ["Opened", "Clicked", "Purchased", "Ignored", "Unsubscribed", "Complained", "Positive Feedback", "Negative Feedback"])

    @patch("campaigns.campaign_simulator.get_campaign_by_id")
    @patch("campaigns.campaign_simulator.insert_campaign_response")
    @patch("campaigns.campaign_simulator.update_campaign_status")
    @patch("campaigns.campaign_simulator.generate_response_event")
    def test_forced_campaign_response_simulation(self, mock_gen_evt, mock_upd_status, mock_ins_resp, mock_get_camp):
        """Test forced customer response simulation and single-entity event trigger."""
        mock_get_camp.return_value = {"campaign_id": 12, "entity_id": "C00001", "campaign_title": "Promo", "status": "Simulated Dispatch"}
        mock_gen_evt.return_value = "E0000099"
        mock_ins_resp.return_value = 202
        mock_upd_status.return_value = True
        
        res = simulate_campaign_response(12, forced_response_type="Purchased")
        
        self.assertIsNotNone(res)
        self.assertEqual(res["response_type"], "Purchased")
        self.assertEqual(res["event_id"], "E0000099")
        self.assertEqual(res["status"], "Responded")
        mock_gen_evt.assert_called_once_with("C00001", 12, "Purchased")

    def test_event_mapping_integrity(self):
        """Verify all response types map to valid OSMOS event types."""
        for resp_type, evt_type in RESPONSE_TO_EVENT_MAP.items():
            self.assertIn(evt_type, ["email_open", "email_click", "purchase", "complaint", "positive_review", "negative_review", "inactivity_period", "social_negative_mention"])

if __name__ == "__main__":
    unittest.main()
