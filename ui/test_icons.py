import unittest

from ui.icons import MAIN_PAGES, PAGE_ICONS, icon_html, nav_link_html


class TestIcons(unittest.TestCase):
    def test_page_icon_mapping_includes_all_main_pages(self):
        for page in MAIN_PAGES:
            self.assertIn(page, PAGE_ICONS)
            self.assertTrue(PAGE_ICONS[page].startswith("bi-"))

    def test_icon_helper_returns_safe_html(self):
        html = icon_html("LLM")
        self.assertIn("bi-cpu", html)
        self.assertIn("aria-hidden", html)
        self.assertNotIn("<script", icon_html("<script>alert(1)</script>"))

    def test_nav_link_uses_display_label_and_page_query(self):
        html = nav_link_html("Dashboard Overview", active=True)
        self.assertIn("osmos-nav-link", html)
        self.assertIn("is-active", html)
        self.assertIn("page=Dashboard%20Overview", html)
        self.assertIn("bi-speedometer2", html)


if __name__ == "__main__":
    unittest.main()
