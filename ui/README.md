# OSMOS UI Package — Contextual Sidebar Page Guide

## 1. Overview & Purpose
The `ui/` package provides contextual, in-app documentation displayed directly in the Streamlit sidebar below the main navigation menu.

This guide helps new users, executives, and presenters understand:
1. **Page Purpose**: What the selected section accomplishes.
2. **User Actions**: What operations the admin can perform.
3. **Key Outputs**: Primary KPIs, charts, data tables, and records generated.
4. **Workflow Position**: Where the page fits in the global OSMOS closed-loop pipeline (`Raw Data → Digital Twin → ML Predictions → Segment/Persona → Campaign Action → Event Feedback`).
5. **Mini Pipeline Flow**: A quick visual text chain.
6. **Demo / Presentation Tips**: Talking points and recommended presenter actions for live demonstrations.

---

## 2. Architecture & File Layout
```
ui/
├── __init__.py          # Package exports (render_sidebar_help, get_page_help_content)
├── sidebar_help.py      # PAGE_HELP dictionary & Streamlit sidebar rendering logic
├── test_sidebar_help.py # Unit test suite for help content integrity
└── README.md            # Technical documentation
```

---

## 3. PAGE_HELP Dictionary Structure

Each entry in `PAGE_HELP` in `ui/sidebar_help.py` follows this schema:

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

## 4. How to Add Help for a New Page

To add contextual sidebar documentation for a new page:

1. Open `ui/sidebar_help.py`.
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
3. Call `render_sidebar_help(page_name)` in `app.py` after page selection.
4. Run `python -m unittest ui/test_sidebar_help.py` to verify schema integrity.
