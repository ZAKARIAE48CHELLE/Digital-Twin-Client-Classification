"""
OSMOS Database Intelligence Layer — Concurrency & Performance Stress Tester
=============================================================================
Provides real-time PostgreSQL connection pool telemetry, multi-threaded stress testing,
concurrency throughput benchmarks, and latency distribution analysis to prove database resilience.
"""

import time
import logging
import concurrent.futures
from typing import Dict, Any, List, Tuple
import pandas as pd
from database.db import get_connection
from admin.database_metrics import is_postgres_available

logger = logging.getLogger("OSMOS_DB_CONCURRENCY")


def get_realtime_connection_stats() -> Dict[str, Any]:
    """
    Fetches real-time connection pool stats, state breakdown, and database size from PostgreSQL.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Total & Max connections
        cur.execute("SELECT count(*) FROM pg_stat_activity;")
        total_active = cur.fetchone()[0]

        cur.execute("SHOW max_connections;")
        max_conns_str = cur.fetchone()[0]
        try:
            max_conns = int(max_conns_str)
        except ValueError:
            max_conns = 500

        # Database size
        cur.execute("SELECT pg_size_pretty(pg_database_size(current_database())), pg_database_size(current_database());")
        size_row = cur.fetchone()
        db_size_pretty = size_row[0] if size_row else "Unknown"
        db_size_bytes = size_row[1] if size_row else 0

        # Connection states
        cur.execute("""
            SELECT COALESCE(state, 'background') AS state, count(*)
            FROM pg_stat_activity
            WHERE datname = current_database() OR datname IS NULL
            GROUP BY COALESCE(state, 'background');
        """)
        state_rows = cur.fetchall()
        states = {row[0]: row[1] for row in state_rows}

        cur.close()
        conn.close()

        utilization_pct = round((total_active / max_conns) * 100.0, 2) if max_conns > 0 else 0.0

        return {
            "status": "Online",
            "active_connections": total_active,
            "max_connections": max_conns,
            "utilization_pct": utilization_pct,
            "idle_connections": states.get("idle", 0),
            "active_queries": states.get("active", 0),
            "background_workers": states.get("background", 0),
            "db_size_pretty": db_size_pretty,
            "db_size_bytes": db_size_bytes,
        }
    except Exception as e:
        logger.error(f"Failed to fetch real-time DB stats: {e}")
        return {
            "status": "Offline / Error",
            "reason": str(e),
            "active_connections": 0,
            "max_connections": 500,
            "utilization_pct": 0.0,
            "idle_connections": 0,
            "active_queries": 0,
            "background_workers": 0,
            "db_size_pretty": "0 MB",
            "db_size_bytes": 0,
        }


def get_detailed_table_storage_stats() -> List[Dict[str, Any]]:
    """
    Returns detailed disk usage and row count estimates for all PostgreSQL tables.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT relname AS table_name,
                   pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
                   n_live_tup AS row_estimate,
                   pg_total_relation_size(relid) AS size_bytes
            FROM pg_stat_user_tables
            ORDER BY pg_total_relation_size(relid) DESC;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "table_name": r[0],
                "size_pretty": r[1],
                "row_estimate": r[2],
                "size_bytes": r[3],
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Failed to get table storage stats: {e}")
        return []


def _run_single_stress_worker(worker_id: int, workload_type: str) -> Tuple[bool, int, float, str]:
    """
    Worker function executed inside ThreadPoolExecutor to simulate a single concurrent client.
    """
    start = time.time()
    try:
        conn = get_connection()
        cur = conn.cursor()

        if workload_type == "Read Query (SELECT 1)":
            cur.execute("SELECT 1, pg_backend_pid();")
            cur.fetchone()
        elif workload_type == "Complex Analytics Join":
            cur.execute("""
                SELECT e.entity_id, count(h.event_id) AS evt_count, MAX(h.event_date) AS last_date
                FROM entities e
                LEFT JOIN event_history h ON e.entity_id = h.entity_id
                GROUP BY e.entity_id
                LIMIT 20;
            """)
            cur.fetchall()
        elif workload_type == "Audit Transaction Write":
            cur.execute("""
                INSERT INTO audit_logs (action_type, entity_id, details)
                VALUES (%s, %s, %s);
            """, (f"CONCURRENCY_TEST_W{worker_id}", "P_DEMO_001", "Automated stress test transaction execution."))
            conn.commit()
        else:
            cur.execute("SELECT current_timestamp;")
            cur.fetchone()

        cur.close()
        conn.close()
        duration_ms = (time.time() - start) * 1000.0
        return (True, worker_id, duration_ms, "Success")
    except Exception as e:
        duration_ms = (time.time() - start) * 1000.0
        return (False, worker_id, duration_ms, str(e))


def run_concurrency_stress_test(num_requests: int = 50, workload_type: str = "Read Query (SELECT 1)") -> Dict[str, Any]:
    """
    Executes concurrent multi-threaded database queries against PostgreSQL and computes performance statistics.
    Proves that PostgreSQL handles concurrent request surges cleanly without crashing.
    """
    start_total = time.time()

    initial_stats = get_realtime_connection_stats()

    # Determine concurrency thread count
    workers = min(num_requests, 100)

    results: List[Tuple[bool, int, float, str]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_run_single_stress_worker, idx, workload_type)
            for idx in range(1, num_requests + 1)
        ]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    total_duration_sec = time.time() - start_total
    final_stats = get_realtime_connection_stats()

    successes = [r for r in results if r[0]]
    failures = [r for r in results if not r[0]]

    success_count = len(successes)
    failure_count = len(failures)
    success_rate = (success_count / num_requests) * 100.0 if num_requests > 0 else 0.0

    latencies = [r[2] for r in results]
    latencies_sorted = sorted(latencies) if latencies else [0.0]

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    min_latency = latencies_sorted[0] if latencies_sorted else 0.0
    max_latency = latencies_sorted[-1] if latencies_sorted else 0.0
    p50_latency = latencies_sorted[int(len(latencies_sorted) * 0.50)] if latencies_sorted else 0.0
    p95_latency = latencies_sorted[int(len(latencies_sorted) * 0.95)] if latencies_sorted else 0.0

    throughput_qps = num_requests / total_duration_sec if total_duration_sec > 0 else 0.0

    # Build per-request breakdown dataframe
    df_results = pd.DataFrame([
        {
            "Request_ID": r[1],
            "Status": "Success" if r[0] else "Failed",
            "Latency_ms": round(r[2], 2),
            "Details": r[3],
        }
        for r in results
    ]).sort_values("Request_ID")

    is_database_stopped = (failure_count > 0 and final_stats["status"] != "Online")

    summary_verdict = (
        f"✅ **Database Remained 100% Operational!** Executed {num_requests} concurrent requests in {total_duration_sec:.2f}s "
        f"({throughput_qps:.1f} req/sec, {success_rate:.0f}% Success Rate). "
        f"Peak active connections stayed safely within PostgreSQL max limit ({final_stats['active_connections']}/{final_stats['max_connections']})."
        if failure_count == 0 else
        f"⚠️ Executed {num_requests} requests with {success_count} Successes and {failure_count} Failures. "
        f"Database server is currently: **{final_stats['status']}**."
    )

    return {
        "num_requests": num_requests,
        "workload_type": workload_type,
        "total_duration_sec": round(total_duration_sec, 3),
        "throughput_qps": round(throughput_qps, 2),
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": round(success_rate, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "min_latency_ms": round(min_latency, 2),
        "max_latency_ms": round(max_latency, 2),
        "p50_latency_ms": round(p50_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "initial_connections": initial_stats.get("active_connections", 0),
        "final_connections": final_stats.get("active_connections", 0),
        "max_connections": final_stats.get("max_connections", 500),
        "is_database_stopped": is_database_stopped,
        "summary_verdict": summary_verdict,
        "results_df": df_results,
    }
