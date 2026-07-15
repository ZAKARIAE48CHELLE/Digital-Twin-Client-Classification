import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import analytics.clv_trend_alerts as clv_alerts

class TestClvTrendAlerts(unittest.TestCase):

    def test_classify_clv_trend(self):
        # Drop threshold cases
        # High drop: > 35%
        level, action = clv_alerts.classify_clv_trend(100.0, 60.0)
        self.assertEqual(level, "High")
        self.assertEqual(action, "Trigger retention campaign")
        
        # Medium drop: 20% to 35%
        level, action = clv_alerts.classify_clv_trend(100.0, 75.0)
        self.assertEqual(level, "Medium")
        self.assertEqual(action, "Send personalized offer")
        
        # Low drop: 10% to 20%
        level, action = clv_alerts.classify_clv_trend(100.0, 85.0)
        self.assertEqual(level, "Low")
        
        # Stable case: < 10%
        level, action = clv_alerts.classify_clv_trend(100.0, 95.0)
        self.assertEqual(level, "None")
        
        # Safe handling of invalid inputs
        level, action = clv_alerts.classify_clv_trend(None, 50.0)
        self.assertEqual(level, "None")

    @patch('analytics.clv_trend_alerts.is_postgres_available')
    def test_get_clv_trend_alerts_empty_db(self, mock_avail):
        mock_avail.return_value = False
        df = clv_alerts.get_clv_trend_alerts()
        self.assertTrue(df.empty)

if __name__ == "__main__":
    unittest.main()
