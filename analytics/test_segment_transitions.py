import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import analytics.segment_transitions as seg_trans

class TestSegmentTransitions(unittest.TestCase):

    def test_classify_transition(self):
        # Stable
        self.assertEqual(
            seg_trans.classify_transition("High-Value Loyalists", "High-Value Loyalists", "Premium Loyalist", "Premium Loyalist"),
            "Stable"
        )
        
        # New Assignment
        self.assertEqual(
            seg_trans.classify_transition(None, "New Customers", None, "New Explorer"),
            "New Assignment"
        )
        
        # Upgrades
        self.assertEqual(
            seg_trans.classify_transition("New Customers", "Growth Potential Clients", "New Explorer", "Emerging Loyalist"),
            "Upgrade"
        )
        self.assertEqual(
            seg_trans.classify_transition("Growth Potential Clients", "High-Value Loyalists", "Emerging Loyalist", "Premium Loyalist"),
            "Upgrade"
        )
        
        # Risk Increase
        self.assertEqual(
            seg_trans.classify_transition("High-Value Loyalists", "At-Risk Premium Clients", "Premium Loyalist", "Silent VIP at Risk"),
            "Risk Increase"
        )
        
        # Downgrades
        self.assertEqual(
            seg_trans.classify_transition("High-Value Loyalists", "Dormant Low-Value Clients", "Premium Loyalist", "Sleeping Client"),
            "Downgrade"
        )

    @patch('analytics.segment_transitions.is_postgres_available')
    def test_get_segment_transitions_empty_db(self, mock_avail):
        mock_avail.return_value = False
        df = seg_trans.get_segment_transitions()
        self.assertTrue(df.empty)

if __name__ == "__main__":
    unittest.main()
