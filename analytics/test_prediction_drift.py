import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import analytics.prediction_drift as drift

class TestPredictionDrift(unittest.TestCase):

    @patch('analytics.prediction_drift.compare_class_distribution')
    @patch('analytics.prediction_drift.is_postgres_available')
    def test_detect_prediction_drift_thresholds(self, mock_avail, mock_compare):
        mock_avail.return_value = True
        
        # Mock class distribution comparison
        mock_data = pd.DataFrame([
            {
                "dynamic_class": "Active Client",
                "baseline_count": 100,
                "current_count": 100,
                "baseline_percent": 0.50,
                "current_percent": 0.20, # Drop of 30% -> High Drift
                "change_percent": -0.30
            },
            {
                "dynamic_class": "VIP Client",
                "baseline_count": 100,
                "current_count": 100,
                "baseline_percent": 0.50,
                "current_percent": 0.62, # Increase of 12% -> Low Drift
                "change_percent": 0.12
            }
        ])
        mock_compare.return_value = mock_data
        
        result_df = drift.detect_prediction_drift(threshold=0.15)
        
        self.assertEqual(result_df.loc[0, "drift_level"], "High")
        self.assertEqual(result_df.loc[0, "drift_flag"], True)
        
        self.assertEqual(result_df.loc[1, "drift_level"], "Low")
        self.assertEqual(result_df.loc[1, "drift_flag"], False) # threshold is 0.15, so 12% change does not flag

    @patch('analytics.prediction_drift.is_postgres_available')
    def test_get_class_distribution_empty_db(self, mock_avail):
        mock_avail.return_value = False
        df = drift.get_class_distribution()
        self.assertTrue(df.empty)

if __name__ == "__main__":
    unittest.main()
