import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import admin.database_metrics as db_metrics

class TestDatabaseMetrics(unittest.TestCase):

    @patch('admin.database_metrics.test_connection')
    def test_database_health_offline(self, mock_test_conn):
        mock_test_conn.return_value = (False, "Timeout connection error")
        health = db_metrics.get_database_health()
        self.assertEqual(health["status"], "Offline")
        self.assertEqual(health["reason"], "Timeout connection error")

    @patch('admin.database_metrics.is_postgres_available')
    def test_table_counts_offline_fallback(self, mock_avail):
        mock_avail.return_value = False
        counts = db_metrics.get_table_counts()
        self.assertTrue(len(counts) > 0)
        self.assertEqual(counts[0]["row_count"], 0)

    def test_module_imports_without_crashing(self):
        try:
            import admin.database_dashboard as dashboard
            import admin.database_metrics as metrics
            imported = True
        except Exception:
            imported = False
        self.assertTrue(imported)

    @patch('admin.database_metrics.pd.read_sql')
    @patch('admin.database_metrics.get_engine')
    @patch('admin.database_metrics.is_postgres_available')
    def test_entity_history_parameterized(self, mock_avail, mock_get_engine, mock_read_sql):
        mock_avail.return_value = True
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        mock_read_sql.return_value = MagicMock()
        
        # Test timeline query
        db_metrics.get_entity_event_timeline("P01500")
        mock_read_sql.assert_called_once()


if __name__ == "__main__":
    unittest.main()
