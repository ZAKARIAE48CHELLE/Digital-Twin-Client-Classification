"""
OSMOS Database Intelligence Layer — Database Concurrency Tests
===============================================================
Unit test suite verifying real-time connection stats, table storage metrics,
and multi-threaded concurrency stress testing against PostgreSQL.
"""

import unittest
from admin.database_concurrency import (
    get_realtime_connection_stats,
    get_detailed_table_storage_stats,
    run_concurrency_stress_test,
)


class TestDatabaseConcurrency(unittest.TestCase):

    def test_get_realtime_connection_stats(self):
        """Verifies real-time stats return valid dictionary keys."""
        stats = get_realtime_connection_stats()
        self.assertIn("status", stats)
        self.assertIn("active_connections", stats)
        self.assertIn("max_connections", stats)
        self.assertIn("utilization_pct", stats)
        self.assertGreaterEqual(stats["max_connections"], 100)

    def test_run_concurrency_stress_test_read(self):
        """Verifies multi-threaded stress test handles 25 concurrent requests successfully."""
        res = run_concurrency_stress_test(num_requests=25, workload_type="Read Query (SELECT 1)")
        self.assertEqual(res["num_requests"], 25)
        self.assertEqual(res["failure_count"], 0)
        self.assertEqual(res["success_rate"], 100.0)
        self.assertGreater(res["throughput_qps"], 0.0)
        self.assertFalse(res["is_database_stopped"])
        self.assertIn("Database Remained 100% Operational", res["summary_verdict"])

    def test_get_detailed_table_storage_stats(self):
        """Verifies table storage stats function executes without error."""
        t_stats = get_detailed_table_storage_stats()
        self.assertIsInstance(t_stats, list)


if __name__ == "__main__":
    unittest.main()
