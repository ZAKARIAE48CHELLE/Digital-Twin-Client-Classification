import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import storage.storage_manager as storage_manager

class TestStorageManager(unittest.TestCase):

    def setUp(self):
        # Reset fallback state before each test
        storage_manager._fallback_active = False
        storage_manager._fallback_reason = None

    @patch('storage.storage_manager.os.getenv')
    def test_excel_backend_selected_by_default(self, mock_getenv):
        mock_getenv.return_value = "excel"
        backend = storage_manager.get_storage_backend()
        self.assertEqual(backend, "excel")
        self.assertFalse(storage_manager.is_postgres_enabled())

    @patch('storage.storage_manager.os.getenv')
    def test_invalid_backend_falls_back_to_excel(self, mock_getenv):
        mock_getenv.return_value = "invalid_backend_xyz"
        backend = storage_manager.get_storage_backend()
        self.assertEqual(backend, "excel")
        self.assertFalse(storage_manager.is_postgres_enabled())

    @patch('storage.storage_manager.test_connection')
    @patch('storage.storage_manager.os.getenv')
    def test_postgres_backend_connection_success(self, mock_getenv, mock_test_conn):
        mock_getenv.return_value = "postgres"
        mock_test_conn.return_value = (True, "Connected")
        
        backend = storage_manager.get_storage_backend()
        self.assertEqual(backend, "postgres")
        self.assertTrue(storage_manager.is_postgres_enabled())

    @patch('storage.storage_manager.test_connection')
    @patch('storage.storage_manager.os.getenv')
    def test_postgres_backend_connection_failure_falls_back(self, mock_getenv, mock_test_conn):
        mock_getenv.return_value = "postgres"
        mock_test_conn.return_value = (False, "Connection refused")
        
        backend = storage_manager.get_storage_backend()
        self.assertEqual(backend, "excel")
        self.assertFalse(storage_manager.is_postgres_enabled())
        
        fallback_active, reason = storage_manager.get_fallback_status()
        self.assertTrue(fallback_active)
        self.assertEqual(reason, "Connection refused")

    def test_manager_exposes_required_methods(self):
        methods = [
            "get_storage_backend",
            "is_postgres_enabled",
            "load_data",
            "save_data",
            "save_event",
            "save_rfm_score",
            "save_classification_prediction",
            "save_clv_prediction",
            "save_customer_segment",
            "load_event_history"
        ]
        for method in methods:
            self.assertTrue(hasattr(storage_manager, method), f"storage_manager is missing method: {method}")

if __name__ == "__main__":
    unittest.main()
