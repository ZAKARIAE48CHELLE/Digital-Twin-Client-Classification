import unittest
from personas.persona_library import (
    get_all_personas,
    get_persona_by_segment,
    seed_default_personas,
    DEFAULT_PERSONA_MAP
)

class TestPersonaLibrary(unittest.TestCase):
    
    def test_get_all_personas_returns_list(self):
        personas = get_all_personas()
        self.assertIsInstance(personas, list)
        self.assertGreaterEqual(len(personas), 10)
        
    def test_get_persona_by_segment(self):
        p = get_persona_by_segment("Prospect")
        self.assertEqual(p["persona_name"], "New Explorer")
        
    def test_seed_default_personas_no_duplicates(self):
        count = seed_default_personas()
        self.assertEqual(count, 10)
        
    def test_fallback_map_integrity(self):
        self.assertEqual(len(DEFAULT_PERSONA_MAP), 10)

if __name__ == "__main__":
    unittest.main()
