"""
Backward-compatibility alias wrapper for ui/contextual_help.py.
"""
from ui.contextual_help import render_floating_help_widget
from ui.help_content import get_page_help_content, PAGE_HELP

# Alias render_sidebar_help to render_floating_help_widget
def render_sidebar_help(page_name):
    """Legacy alias that redirects to floating right-side help widget."""
    render_floating_help_widget(page_name)
