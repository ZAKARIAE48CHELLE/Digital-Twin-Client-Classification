import unittest

from ui.design_system import THEME_TOKENS, build_theme_style, get_theme_tokens, normalize_theme
from ui.components import metric_card_html, status_badge_html


class TestDesignSystem(unittest.TestCase):
    def test_light_and_dark_theme_configs_exist(self):
        self.assertIn("Light", THEME_TOKENS)
        self.assertIn("Dark", THEME_TOKENS)
        self.assertEqual(THEME_TOKENS["Light"]["--osmos-card-bg"], "#FFFFFF")
        self.assertEqual(THEME_TOKENS["Dark"]["--osmos-bg"], "#0F172A")

    def test_theme_normalization(self):
        self.assertEqual(normalize_theme("dark"), "Dark")
        self.assertEqual(normalize_theme("LIGHT"), "Light")
        self.assertEqual(normalize_theme("unknown"), "Light")

    def test_theme_tokens_include_aliases_and_css_generation_does_not_crash(self):
        tokens = get_theme_tokens("Light")
        self.assertIn("--osmos-primary", tokens)
        css = build_theme_style("Light")
        self.assertIn(":root", css)
        self.assertIn("--bg-main: var(--osmos-bg)", css)

    def test_component_helpers_return_safe_html(self):
        badge = status_badge_html("PostgreSQL", icon="PostgreSQL")
        metric = metric_card_html("CLV", "1200 MAD", icon="CLV")
        self.assertIn("osmos-badge", badge)
        self.assertIn("bi-server", badge)
        self.assertIn("osmos-metric-card", metric)
        self.assertIn("bi-cash-coin", metric)


if __name__ == "__main__":
    unittest.main()
