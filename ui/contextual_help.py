"""
OSMOS Contextual Right-Side Floating Page Guide Module.

Renders a non-intrusive floating right-side help widget and overlay panel in Streamlit.
The widget is UI-only: it does not call LLM, ML, database, or storage functions.
"""

from html import escape
import logging

import streamlit as st

from ui.help_content import get_page_help_content
from ui.icons import icon_html

logger = logging.getLogger("OSMOS_CONTEXTUAL_HELP")


def inject_floating_help_css():
    """Floating guide CSS is provided by the global OSMOS design-system style."""
    return None


def _list_html(items):
    return "".join(f"<li style='margin-bottom:4px;'>{escape(str(item))}</li>" for item in items)


def render_help_panel(page_name, help_data):
    """Render the right-side overlay help panel."""
    db_note_html = ""
    if help_data.get("requires_postgres", False):
        db_note_html = (
            "<div class='osmos-db-note'>"
            f"{icon_html('PostgreSQL')} <b>PostgreSQL feature area:</b> Full historical tracking is available when the PostgreSQL backend is active."
            "</div>"
        )

    actions_html = _list_html(help_data.get("actions", []))
    outputs_html = _list_html(help_data.get("outputs", []))

    panel_html = f"""<div class='osmos-floating-panel'>
<div class='osmos-panel-header'>
<span class='osmos-panel-title'>{icon_html('Guide')}<span>OSMOS Page Guide</span></span>
</div>
<div class='osmos-panel-page-title'>{escape(str(help_data.get('title', page_name)))}</div>
{db_note_html}
<div class='osmos-flow-badge'>{icon_html('Journey')}<b>{escape(str(help_data.get('workflow_position', 'Workflow position')))}</b></div>
<div class='osmos-panel-section-title'>{icon_html('Priority')}<span>Purpose</span></div>
<p class='osmos-panel-text'>{escape(str(help_data.get('purpose', '')))}</p>
<div class='osmos-panel-section-title'>{icon_html('Journey')}<span>Pipeline Flow</span></div>
<div class='osmos-mini-flow'>{escape(str(help_data.get('mini_workflow', '')))}</div>
<div class='osmos-panel-section-title'>{icon_html('Run')}<span>What You Can Do Here</span></div>
<ul style='font-size: 12px; color: var(--osmos-secondary); padding-left: 18px; margin: 0 0 10px 0;'>{actions_html}</ul>
<div class='osmos-panel-section-title'>{icon_html('Chart')}<span>Key Outputs</span></div>
<ul style='font-size: 12px; color: var(--osmos-secondary); padding-left: 18px; margin: 0 0 10px 0;'>{outputs_html}</ul>
<div class='osmos-tip-box'><b>Demo tip:</b> {escape(str(help_data.get('demo_tip', '')))}</div>
</div>"""

    st.markdown(panel_html, unsafe_allow_html=True)


def render_floating_help_widget(page_name):
    """
    Render the fixed bottom-right Page Guide button and floating overlay panel.
    Uses st.session_state["osmos_help_open"] and performs no backend calls.
    """
    if "osmos_help_open" not in st.session_state:
        st.session_state["osmos_help_open"] = False

    help_data = get_page_help_content(page_name)
    inject_floating_help_css()

    if st.session_state["osmos_help_open"]:
        if st.button("Close Guide", key="btn_close_page_guide", help="Close the Page Guide panel"):
            st.session_state["osmos_help_open"] = False
            st.rerun()
        render_help_panel(page_name, help_data)
    else:
        if st.button("Page Guide", key="btn_open_page_guide", help=f"Open Page Guide for {help_data['title']}"):
            st.session_state["osmos_help_open"] = True
            st.rerun()


