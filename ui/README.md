# OSMOS UI Package — Contextual Right-Side Floating Page Guide

## 1. Overview & Purpose
The `ui/` package provides contextual, in-app documentation displayed as a **non-intrusive floating right-side help widget** on the screen.

This leaves the left Streamlit sidebar clean and dedicated exclusively to navigation and essential model controls.

The floating Page Guide widget helps new users, executives, and presenters understand:
1. **Page Purpose**: What the selected section accomplishes.
2. **User Actions**: Executable operations available to the admin.
3. **Key Outputs**: Primary KPIs, charts, data tables, and records generated.
4. **Workflow Position**: Where the page fits in the global OSMOS closed-loop pipeline (`Raw Data → Digital Twin → ML Predictions → Segment/Persona → Campaign Action → Event Feedback`).
5. **Mini Pipeline Flow**: A quick visual text chain.
6. **Demo / Presentation Tips**: Recommended presenter talking points for live demonstrations.

---

## 2. Architecture & File Layout
```
ui/
├── __init__.py            # Package exports (render_floating_help_widget, get_page_help_content)
├── help_content.py        # PAGE_HELP dictionary mapping pages to documentation content
├── contextual_help.py     # Streamlit floating right-side widget & panel overlay renderer
├── sidebar_help.py        # Legacy compatibility wrapper
├── test_contextual_help.py# Unit test suite for help content and crash-free rendering
└── README.md              # Technical documentation
```

---

## 3. PAGE_HELP Dictionary Structure

Each entry in `PAGE_HELP` in `ui/help_content.py` follows this schema:

```python
"Page Name": {
    "title": "Human Readable Section Title",
    "purpose": "Detailed explanation of page purpose and business value.",
    "actions": [
        "First executable action.",
        "Second executable action."
    ],
    "outputs": [
        "First output indicator / KPI.",
        "Second output / table."
    ],
    "workflow_position": "Workflow position: Layer Name",
    "mini_workflow": "Step 1 → Step 2 → Step 3",
    "demo_tip": "Recommended presentation script or tip.",
    "requires_postgres": True  # Optional boolean flag for DB requirement warning
}
```

---

## 4. Floating Widget Behavior & Non-Intrusive Design

- **State Persistence**: State is stored in `st.session_state["osmos_help_open"]` (default `False`).
- **Zero Heavy Computations**: Rendering the guide panel is a 100% UI-only operation. It executes **zero LLM API calls** and **zero database queries**.
- **No Layout Shift**: The guide renders as a floating glassmorphism panel overlay on the right side of the screen (`position: fixed; right: 24px; bottom: 80px; width: 390px; z-index: 999999`). Main dashboard content does not shift or jump when opening/closing the guide.

---

## 5. How to Add Help for a New Page

To add contextual right-side help documentation for a new page:

1. Open `ui/help_content.py`.
2. Add a new key to the `PAGE_HELP` dictionary matching your page's navigation name:
   ```python
   "New Feature Space": {
       "title": "New Feature Title",
       "purpose": "Purpose of the new feature...",
       "actions": ["Perform action 1", "Perform action 2"],
       "outputs": ["Output metric 1", "Generated artifact 2"],
       "workflow_position": "Workflow position: Feature Layer",
       "mini_workflow": "Input → Process → Output",
       "demo_tip": "Showcase feature capabilities during demo.",
       "requires_postgres": False
   }
   ```
3. Call `render_floating_help_widget(page)` in `app.py` after page routing.
4. Run `python -m unittest ui/test_contextual_help.py` to verify schema integrity.
