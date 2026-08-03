# OSMOS UI Package

The `ui/` package contains the OSMOS visual design system, theme manager, professional icon registry, reusable layout primitives, reusable HTML components, and contextual Page Guide content.

## Design System Overview

OSMOS uses a custom Streamlit-compatible CSS layer rather than relying only on `.streamlit/config.toml`. This allows live Light/Dark switching from inside the app.

Main files:

```text
ui/
├── __init__.py
├── theme_manager.py
├── design_system.py
├── icons.py
├── layout.py
├── components.py
├── contextual_help.py
├── help_content.py
└── README.md
```

## Light and Dark Mode

Theme state is stored in:

```python
st.session_state["osmos_theme"]
```

Use:

```python
from ui.theme_manager import apply_osmos_theme, get_theme, render_theme_toggle

apply_osmos_theme(get_theme())
render_theme_toggle(st.sidebar)
```

Default mode is `Light`. Unknown theme values fall back to `Light`.

## Icons

OSMOS uses Bootstrap Icons via CDN. Add or update icons in `ui/icons.py`:

```python
PAGE_ICONS["New Page"] = "bi-diagram-3"
ICON_MAP["New Concept"] = "bi-cpu"
```

Use icon helpers instead of emoji:

```python
from ui.icons import icon_html

icon_html("CLV")
icon_html("PostgreSQL")
```

Rule: avoid emojis in professional UI strings, navigation, page titles, cards, buttons, tabs, alerts, and section headers.

## Layout

Use shared page and section headers:

```python
from ui.layout import render_page_header, section_header_html

render_page_header(
    "Digital Twin Explorer",
    "Inspect customer state, predictive scores, and segment-persona resolution.",
    icon="Digital Twin & Persona",
    badge="PostgreSQL",
)

st.markdown(section_header_html("Predictive Scores", "Chart"), unsafe_allow_html=True)
```

## Components

Use `ui/components.py` for reusable cards and badges:

```python
from ui.components import metric_card_html, status_badge_html, persona_card_html

metric_card_html("CLV", "12,500 MAD", icon="CLV", status="VIP")
status_badge_html("PostgreSQL", icon="PostgreSQL")
persona_card_html("Premium Loyalist", "High-Value Loyalists", "High", "Low", "Email", "Invite to loyalty program")
```

All components use CSS variables and adapt automatically to Light/Dark mode.

## Floating Page Guide

`ui/contextual_help.py` renders the right-side Page Guide overlay. It is UI-only and does not call LLM, ML, database, or storage functions. The widget uses the same CSS variables as the rest of OSMOS and stays fixed on the right side without shifting page layout.

## Tests

Run UI tests with:

```bash
python -m unittest ui/test_theme_manager.py ui/test_icons.py ui/test_design_system.py ui/test_contextual_help.py ui/test_sidebar_help.py
```
