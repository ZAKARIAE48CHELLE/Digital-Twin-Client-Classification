"""
UI Package for OSMOS.

Provides interface helper modules, including the floating right-side contextual page guide.
"""
from ui.contextual_help import render_floating_help_widget
from ui.help_content import get_page_help_content, PAGE_HELP

__all__ = ["render_floating_help_widget", "get_page_help_content", "PAGE_HELP"]
