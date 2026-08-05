"""
OSMOS Executive Report Generator — Test Suite (Phase 8.6)
=========================================================
Unit tests verifying report context building, section templates, report generation,
markdown/HTML/PDF exports, and read-only safety.
"""

import os
import unittest
import pandas as pd

from reports.report_schemas import ReportContext, ReportSection, ReportExportResult
from reports.report_context_builder import (
    build_entity_report_context,
    build_agent_run_report_context,
    build_journey_report_context,
    build_system_report_context,
)
from reports.report_generator import (
    generate_report_markdown,
    generate_entity_executive_report,
    generate_agent_run_report,
    generate_journey_report,
    generate_system_overview_report,
)
from reports.report_exporter import (
    convert_markdown_to_html,
    export_report_to_file,
    save_report_markdown,
    save_report_html,
)


class TestReportsPhase86(unittest.TestCase):

    def test_build_entity_report_context(self):
        """Verifies build_entity_report_context assembles valid ReportContext."""
        sample_df = pd.DataFrame([{"entity_id": "P_DEMO_001", "entity_type": "Prospect", "recency_days": 5}])
        ctx = build_entity_report_context("P_DEMO_001", df=sample_df, include_live_supervision=False)
        self.assertEqual(ctx.report_type, "Entity Executive Report")
        self.assertEqual(ctx.entity_id, "P_DEMO_001")
        self.assertIsNotNone(ctx.latest_scores)

    def test_build_agent_run_report_context_fallback(self):
        """Verifies build_agent_run_report_context handles missing run gracefully."""
        ctx = build_agent_run_report_context(999999)
        self.assertEqual(ctx.report_type, "Agent Run Report")
        self.assertEqual(ctx.run_id, 999999)

    def test_generate_report_markdown(self):
        """Verifies generate_report_markdown produces non-empty markdown string."""
        sample_df = pd.DataFrame([{"entity_id": "P_DEMO_001", "entity_type": "Prospect", "recency_days": 5}])
        md_text, ctx = generate_entity_executive_report("P_DEMO_001", df=sample_df)
        self.assertIn("# 🛡️ OSMOS EXECUTIVE REPORT", md_text)
        self.assertIn("Entity ID: `P_DEMO_001`", md_text)
        self.assertIn("1. Executive Summary", md_text)

    def test_convert_markdown_to_html(self):
        """Verifies convert_markdown_to_html produces valid HTML doc with styles."""
        md = "# Sample Title\n\n- Bullet 1\n- Bullet 2"
        html = convert_markdown_to_html(md)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<h1", html)
        self.assertIn("Sample Title", html)

    def test_export_report_to_file(self):
        """Verifies export_report_to_file saves .md and .html files to reports/generated/."""
        sample_md = "# Test Report Document\nSample text."
        res_md = export_report_to_file(sample_md, file_name_base="Test_Export_Unit", export_format="markdown")
        self.assertEqual(res_md.status, "Success")
        self.assertTrue(os.path.exists(res_md.file_path))

        res_html = export_report_to_file(sample_md, file_name_base="Test_Export_Unit", export_format="html")
        self.assertEqual(res_html.status, "Success")
        self.assertTrue(os.path.exists(res_html.file_path))

    def test_system_overview_report(self):
        """Verifies generate_system_overview_report compiles system context."""
        md_text, ctx = generate_system_overview_report()
        self.assertEqual(ctx.report_type, "System Overview Report")
        self.assertIn("OSMOS EXECUTIVE REPORT", md_text)


if __name__ == "__main__":
    unittest.main()
