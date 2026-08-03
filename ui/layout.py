"""Reusable layout primitives for the OSMOS Streamlit UI."""

from html import escape

import streamlit as st

from ui.icons import icon_html, page_icon_html
from ui.components import status_badge_html


def page_header_html(title, subtitle, icon=None, badge=None, kicker=None):
    """Return a professional page header as safe HTML."""
    icon_fragment = page_icon_html(title, "osmos-page-header-icon")
    if icon:
        icon_fragment = f"<span class='osmos-page-header-icon'>{icon_html(icon)}</span>"

    badge_row = ""
    if badge:
        badges = badge if isinstance(badge, (list, tuple)) else [badge]
        badge_row = (
            "<div class='osmos-page-badge-row'>"
            + "".join(status_badge_html(item) for item in badges)
            + "</div>"
        )

    kicker_html = f"<div class='osmos-kicker'>{escape(str(kicker))}</div>" if kicker else ""

    return (
        "<div class='osmos-page-header'>"
        f"{icon_fragment}"
        "<div>"
        f"{kicker_html}"
        f"<h1 class='osmos-page-title'>{escape(str(title))}</h1>"
        f"<p class='osmos-page-subtitle'>{escape(str(subtitle))}</p>"
        f"{badge_row}"
        "</div>"
        "</div>"
    )


def render_page_header(title, subtitle, icon=None, badge=None, kicker=None):
    """Render a professional page header."""
    st.markdown(page_header_html(title, subtitle, icon=icon, badge=badge, kicker=kicker), unsafe_allow_html=True)


def section_header_html(title, icon=None):
    """Return a compact themed section header."""
    return (
        "<div class='section-header'>"
        f"<span class='icon'>{icon_html(icon or title)}</span>"
        f"<span class='title'>{escape(str(title))}</span>"
        "</div>"
    )


def render_section_header(title, icon=None):
    """Render a themed section header."""
    st.markdown(section_header_html(title, icon=icon), unsafe_allow_html=True)


def content_grid_html(items, min_width=220):
    """Wrap already-rendered card HTML fragments in a responsive content grid."""
    cards = "".join(str(item) for item in items)
    return (
        f"<div style='display:grid; grid-template-columns:repeat(auto-fit,minmax({int(min_width)}px,1fr));"
        f"gap:16px; margin-bottom:24px;'>{cards}</div>"
    )


def render_page_shell(inner_html):
    """Render arbitrary HTML inside a themed OSMOS page shell."""
    st.markdown(f"<div class='osmos-page-shell'>{inner_html}</div>", unsafe_allow_html=True)

