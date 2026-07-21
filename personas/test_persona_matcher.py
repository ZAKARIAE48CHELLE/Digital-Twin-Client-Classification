import unittest
from personas.persona_matcher import (
    match_persona_for_segment,
    get_persona_for_entity,
    explain_persona_assignment,
    validate_segment_persona_consistency
)

class TestPersonaMatcher(unittest.TestCase):
    
    def test_segment_first_persona_matching(self):
        persona = match_persona_for_segment("High-Value Loyalists")
        self.assertEqual(persona["persona_name"], "Premium Loyalist")
        
    def test_entity_persona_resolution(self):
        persona = get_persona_for_entity("P00001")
        self.assertIsNotNone(persona)
        self.assertIn("persona_name", persona)
        
    def test_explain_persona_assignment_chain(self):
        exp = explain_persona_assignment("P00001")
        self.assertIn("resolution_chain", exp)
        self.assertIn("P00001", exp["resolution_chain"])
        
    def test_consistency_validation(self):
        res = validate_segment_persona_consistency(df=None)
        self.assertTrue(res["is_consistent"])

if __name__ == "__main__":
    unittest.main()
