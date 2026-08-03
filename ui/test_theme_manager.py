import unittest
from unittest.mock import patch

from ui.theme_manager import THEME_KEY, apply_osmos_theme, get_theme, set_theme


class TestThemeManager(unittest.TestCase):
    def test_get_theme_defaults_to_light(self):
        with patch("streamlit.session_state", new={}):
            self.assertEqual(get_theme(), "Light")

    def test_set_theme_accepts_light_and_dark(self):
        state = {}
        with patch("streamlit.session_state", new=state):
            self.assertEqual(set_theme("Dark"), "Dark")
            self.assertEqual(state[THEME_KEY], "Dark")
            self.assertEqual(set_theme("Light"), "Light")
            self.assertEqual(state[THEME_KEY], "Light")

    def test_unknown_theme_falls_back_to_light(self):
        state = {}
        with patch("streamlit.session_state", new=state):
            self.assertEqual(set_theme("Solarized"), "Light")
            self.assertEqual(get_theme(), "Light")

    @patch("streamlit.markdown")
    def test_apply_theme_injects_css_without_backend_calls(self, mock_markdown):
        with patch("streamlit.session_state", new={}):
            applied = apply_osmos_theme("Dark")
        self.assertEqual(applied, "Dark")
        self.assertTrue(mock_markdown.called)
        html = mock_markdown.call_args.args[0]
        self.assertIn("--osmos-bg", html)
        self.assertIn("bootstrap-icons", html)


if __name__ == "__main__":
    unittest.main()
