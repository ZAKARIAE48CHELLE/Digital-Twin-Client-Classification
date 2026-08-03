"""Session-backed Light/Dark theme manager for OSMOS."""

import streamlit as st

from ui.design_system import build_theme_style, normalize_theme
from ui.icons import icon_html


THEME_KEY = "osmos_theme"
THEME_OPTIONS = ("Light", "Dark")


def get_theme():
    """Return the current theme from Streamlit session state, defaulting to Light."""
    try:
        current = st.session_state.get(THEME_KEY, "Light")
    except Exception:
        current = "Light"
    return normalize_theme(current)


def set_theme(theme):
    """Persist a supported theme name in Streamlit session state."""
    normalized = normalize_theme(theme)
    st.session_state[THEME_KEY] = normalized
    return normalized


def apply_osmos_theme(theme):
    """Inject OSMOS CSS variables and component overrides for the selected theme."""
    normalized = normalize_theme(theme)
    st.markdown(build_theme_style(normalized), unsafe_allow_html=True)
    return normalized


def render_theme_toggle(container=None):
    """Render the sidebar Appearance control and update session state live."""
    target = container or st
    current = get_theme()
    current_index = THEME_OPTIONS.index(current)

    target.markdown(
        f"""<div class='osmos-theme-title osmos-theme-title-standalone'>{icon_html("Info")}<span>Appearance</span></div>""",
        unsafe_allow_html=True,
    )
    selected = target.radio(
        "Appearance",
        list(THEME_OPTIONS),
        index=current_index,
        key="osmos_theme_selector",
        horizontal=True,
        label_visibility="collapsed",
    )

    if selected != current:
        set_theme(selected)
        st.rerun()

    set_theme(selected)
    return selected
