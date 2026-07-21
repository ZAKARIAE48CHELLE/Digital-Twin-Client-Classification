import unittest
from digital_twin.digital_twin_builder import (
    build_digital_twin_profile,
    get_current_digital_twin_state,
    get_digital_twin_scores
)

class TestDigitalTwinBuilder(unittest.TestCase):
    
    def test_build_digital_twin_profile_structure(self):
        profile = build_digital_twin_profile("P00001")
        self.assertIn("core_identity", profile)
        self.assertIn("behavioral_state", profile)
        self.assertIn("scores", profile)
        self.assertIn("predictions", profile)
        self.assertIn("persona_context", profile)
        self.assertIn("history", profile)
        
    def test_missing_entity_fallback(self):
        state = get_current_digital_twin_state("UNKNOWN_999")
        self.assertEqual(state["entity_id"], "UNKNOWN_999")
        self.assertEqual(state["entity_type"], "Client")
        
    def test_score_vector_calculation(self):
        scores = get_digital_twin_scores("P00001")
        self.assertIn(scores["churn_risk"], ["Low Risk", "Moderate Risk", "High Risk", "Critical Risk"])
        self.assertIn(scores["engagement_score"], ["Low Engagement", "Moderate Engagement", "High Engagement"])

if __name__ == "__main__":
    unittest.main()
