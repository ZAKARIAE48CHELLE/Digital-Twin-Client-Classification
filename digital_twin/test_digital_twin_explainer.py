import unittest
from digital_twin.digital_twin_builder import build_digital_twin_profile
from digital_twin.digital_twin_explainer import (
    explain_risk_level,
    explain_value_level,
    explain_engagement_level,
    explain_recommended_action,
    explain_digital_twin_state
)

class TestDigitalTwinExplainer(unittest.TestCase):
    
    def setUp(self):
        self.profile = build_digital_twin_profile("P00001")
        
    def test_explain_risk_level(self):
        exp = explain_risk_level(self.profile)
        self.assertIn("explanation_fr", exp)
        self.assertIn("explanation_en", exp)
        
    def test_explain_value_level(self):
        exp = explain_value_level(self.profile)
        self.assertIn("explanation_fr", exp)
        self.assertIn("explanation_en", exp)
        
    def test_explain_digital_twin_state(self):
        exp = explain_digital_twin_state(self.profile)
        self.assertEqual(exp["entity_id"], "P00001")
        self.assertIn("risk_explanation", exp)

if __name__ == "__main__":
    unittest.main()
