import unittest
from unittest.mock import patch, MagicMock
from ui.sidebar_help import PAGE_HELP, get_page_help_content, render_sidebar_help

KNOWN_PAGES = [
    "Dashboard Overview",
    "Entity Profile",
    "Customer Segments & Personas",
    "Simulate Event",
    "Create New Entity",
    "Database Intelligence",
    "Digital Twin & Persona",
    "Campaign Simulation",
    "Journey Simulator"
]

REQUIRED_KEYS = [
    "title",
    "purpose",
    "actions",
    "outputs",
    "workflow_position",
    "mini_workflow",
    "demo_tip"
]

class TestSidebarHelp(unittest.TestCase):

    def test_all_known_pages_exist(self):
        """Verify that all main OSMOS pages have entries in PAGE_HELP."""
        for page in KNOWN_PAGES:
            self.assertIn(page, PAGE_HELP, f"Missing help content for page: {page}")

    def test_required_keys_in_help_content(self):
        """Verify that every page help dictionary contains all required fields."""
        for page_name, help_dict in PAGE_HELP.items():
            for key in REQUIRED_KEYS:
                self.assertIn(key, help_dict, f"Page '{page_name}' is missing key '{key}'")
                self.assertIsNotNone(help_dict[key], f"Page '{page_name}' key '{key}' is None")
            self.assertIsInstance(help_dict["actions"], list, f"Page '{page_name}' actions must be a list")
            self.assertIsInstance(help_dict["outputs"], list, f"Page '{page_name}' outputs must be a list")

    def test_fallback_for_unknown_page(self):
        """Verify that get_page_help_content returns a safe fallback for unknown pages."""
        fallback = get_page_help_content("Unknown Custom Space")
        self.assertEqual(fallback["title"], "Unknown Custom Space")
        self.assertIn("Overview and management workspace", fallback["purpose"])
        for key in REQUIRED_KEYS:
            self.assertIn(key, fallback)

    @patch("streamlit.sidebar")
    def test_render_sidebar_help_does_not_crash(self, mock_sidebar):
        """Verify that render_sidebar_help executes without errors for known and unknown pages."""
        try:
            render_sidebar_help("Dashboard Overview")
            render_sidebar_help("Unknown Page")
        except Exception as e:
            self.fail(f"render_sidebar_help crashed with exception: {e}")

if __name__ == "__main__":
    unittest.main()
