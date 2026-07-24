"""
OSMOS Contextual Right-Side Floating Page Guide Module.

Renders a non-intrusive floating right-side help widget and overlay panel in Streamlit.
Allows users and presenters to toggle in-depth page explanations without crowding the left sidebar.
"""
import streamlit as st
import textwrap
import logging
from ui.help_content import get_page_help_content, PAGE_HELP

logger = logging.getLogger("OSMOS_CONTEXTUAL_HELP")

def inject_floating_help_css():
    """Injects custom CSS for fixed floating positioning on the right side of the screen."""
    css = """
    <style>
    /* Fixed Bottom-Right Trigger Button Positioning */
    .st-key-btn_open_page_guide,
    .st-key-btn_close_page_guide,
    div[data-testid="stButton"]:has(button[key="btn_open_page_guide"]),
    div[data-testid="stButton"]:has(button[key="btn_close_page_guide"]) {
        position: fixed !important;
        bottom: 24px !important;
        right: 24px !important;
        z-index: 999998 !important;
        width: auto !important;
    }
    
    .st-key-btn_open_page_guide button,
    .st-key-btn_close_page_guide button,
    div[data-testid="stButton"]:has(button[key="btn_open_page_guide"]) button,
    div[data-testid="stButton"]:has(button[key="btn_close_page_guide"]) button {
        border-radius: 24px !important;
        padding: 8px 18px !important;
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        box-shadow: 0 8px 24px rgba(2, 132, 199, 0.45) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        transition: all 0.2s ease-in-out !important;
    }

    .st-key-btn_open_page_guide button:hover,
    .st-key-btn_close_page_guide button:hover {
        transform: translateY(-2px) scale(1.03) !important;
        box-shadow: 0 12px 30px rgba(2, 132, 199, 0.6) !important;
    }
    
    /* Overlay Floating Right Panel */
    .osmos-floating-panel {
        position: fixed;
        bottom: 80px;
        right: 24px;
        width: 390px;
        max-height: 75vh;
        overflow-y: auto;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.96));
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1.5px solid rgba(56, 189, 248, 0.35);
        border-radius: 16px;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), 0 0 20px rgba(56, 189, 248, 0.15);
        padding: 20px;
        z-index: 999999;
        color: #f8fafc;
        font-family: system-ui, -apple-system, sans-serif;
    }
    
    .osmos-panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 10px;
        margin-bottom: 12px;
    }
    
    .osmos-panel-title {
        font-size: 16px;
        font-weight: 700;
        color: #38bdf8;
        margin: 0;
    }
    
    .osmos-panel-section-title {
        font-size: 12px;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 12px;
        margin-bottom: 4px;
    }
    
    .osmos-panel-text {
        font-size: 13px;
        color: #cbd5e1;
        line-height: 1.5;
        margin: 0 0 10px 0;
    }

    .osmos-flow-badge {
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 6px 10px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 600;
        margin-bottom: 12px;
    }

    .osmos-tip-box {
        background: rgba(251, 191, 36, 0.1);
        border-left: 3px solid #fbbf24;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        color: #fef08a;
        margin-top: 12px;
    }
    </style>
    """
    if hasattr(st, "html"):
        st.html(css)
    else:
        st.markdown(css, unsafe_allow_html=True)

def render_help_panel(page_name, help_data):
    """
    Renders the right-side overlay help panel cleanly compiled without raw text formatting issues.
    """
    db_warning_html = ""
    if help_data.get("requires_postgres", False):
        try:
            from storage.storage_manager import is_postgres_enabled
            if not is_postgres_enabled():
                db_warning_html = (
                    "<div style='background: rgba(244, 63, 94, 0.15); border: 1px solid rgba(244, 63, 94, 0.4); "
                    "padding: 8px 12px; border-radius: 8px; font-size: 12px; color: #fda4af; margin-bottom: 12px;'>"
                    "⚠️ <b>Excel Mode Active</b>: Full historical tracking requires PostgreSQL. In Excel mode, this page has read-only or fallback behavior."
                    "</div>"
                )
        except Exception:
            pass

    actions_html = "".join([f"<li style='margin-bottom:4px;'>{a}</li>" for a in help_data["actions"]])
    outputs_html = "".join([f"<li style='margin-bottom:4px;'>{o}</li>" for o in help_data["outputs"]])

    panel_html = f"""<div class='osmos-floating-panel'>
<div class='osmos-panel-header'>
<span class='osmos-panel-title'>📘 OSMOS Page Guide</span>
</div>
<div style='font-size: 15px; font-weight: 700; color: #f8fafc; margin-bottom: 8px;'>{help_data['title']}</div>
{db_warning_html}
<div class='osmos-flow-badge'>🧭 <b>{help_data['workflow_position']}</b></div>
<div class='osmos-panel-section-title'>🎯 Purpose</div>
<p class='osmos-panel-text'>{help_data['purpose']}</p>
<div class='osmos-panel-section-title'>🔄 Pipeline Flow</div>
<div style='background: rgba(15, 23, 42, 0.6); padding: 6px 10px; border-radius: 6px; font-size: 11px; color: #38bdf8; font-family: monospace; margin-bottom: 10px;'>{help_data['mini_workflow']}</div>
<div class='osmos-panel-section-title'>⚡ What You Can Do Here</div>
<ul style='font-size: 12px; color: #cbd5e1; padding-left: 18px; margin: 0 0 10px 0;'>{actions_html}</ul>
<div class='osmos-panel-section-title'>📊 Key Outputs</div>
<ul style='font-size: 12px; color: #cbd5e1; padding-left: 18px; margin: 0 0 10px 0;'>{outputs_html}</ul>
<div class='osmos-tip-box'>💡 <b>Demo Tip:</b> {help_data['demo_tip']}</div>
</div>"""

    if hasattr(st, "html"):
        st.html(panel_html)
    else:
        st.markdown(panel_html, unsafe_allow_html=True)

def render_floating_help_widget(page_name):
    """
    Renders the fixed bottom-right Page Guide button and floating overlay panel.
    Uses st.session_state["osmos_help_open"] to toggle visibility cleanly.
    Does NOT auto-trigger LLM calls or DB logic. UI-only component.
    """
    if "osmos_help_open" not in st.session_state:
        st.session_state["osmos_help_open"] = False
        
    help_data = get_page_help_content(page_name)
    
    # Always inject floating CSS so button is anchored fixed at bottom right
    inject_floating_help_css()
    
    if st.session_state["osmos_help_open"]:
        if st.button("❌ Close Guide", key="btn_close_page_guide", help="Close the Page Guide panel"):
            st.session_state["osmos_help_open"] = False
            st.rerun()
        render_help_panel(page_name, help_data)
    else:
        if st.button("📘 Page Guide", key="btn_open_page_guide", help=f"Open Page Guide for {help_data['title']}"):
            st.session_state["osmos_help_open"] = True
            st.rerun()
