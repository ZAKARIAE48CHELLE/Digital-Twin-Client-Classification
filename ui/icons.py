"""Professional icon registry for the OSMOS Streamlit interface."""

from html import escape
from urllib.parse import quote


BOOTSTRAP_ICONS_CDN = (
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"
)

MAIN_PAGES = [
    "Dashboard Overview",
    "Entity Profile",
    "Customer Segments & Personas",
    "Digital Twin & Persona",
    "Campaign Simulation",
    "Journey Simulator",
    "Agent Supervision Center",
    "Simulate Event",
    "Create New Entity",
    "Database Intelligence",
]

PAGE_LABELS = {
    "Dashboard Overview": "Dashboard",
    "Entity Profile": "Entity Profile",
    "Customer Segments & Personas": "Segments & Personas",
    "Simulate Event": "Event Simulation",
    "Create New Entity": "New Entity",
    "Database Intelligence": "Database Intelligence",
    "Digital Twin & Persona": "Digital Twin Explorer",
    "Campaign Simulation": "Campaign Simulation",
    "Journey Simulator": "Journey Simulator",
    "Agent Supervision Center": "Agent Supervision",
}

PAGE_ICONS = {
    "Dashboard Overview": "bi-speedometer2",
    "Entity Profile": "bi-person-vcard",
    "Customer Segments & Personas": "bi-people",
    "Simulate Event": "bi-lightning-charge",
    "Create New Entity": "bi-person-plus",
    "Database Intelligence": "bi-database",
    "Digital Twin & Persona": "bi-diagram-3",
    "Campaign Simulation": "bi-megaphone",
    "Journey Simulator": "bi-signpost-split",
    "Agent Supervision Center": "bi-robot",
}

ICON_MAP = {
    "CLV": "bi-cash-coin",
    "RFM": "bi-bar-chart-line",
    "Churn Risk": "bi-exclamation-triangle",
    "Segment": "bi-grid-3x3-gap",
    "Persona": "bi-person-badge",
    "LLM": "bi-cpu",
    "Campaign": "bi-send",
    "Journey": "bi-map",
    "PostgreSQL": "bi-server",
    "Excel Mode": "bi-file-earmark-spreadsheet",
    "Success": "bi-check-circle",
    "Warning": "bi-exclamation-circle",
    "Error": "bi-x-circle",
    "Info": "bi-info-circle",
    "Database": "bi-database",
    "Dashboard": "bi-speedometer2",
    "Entity": "bi-person-vcard",
    "Entities": "bi-people",
    "Client": "bi-person-check",
    "Prospect": "bi-person",
    "Model": "bi-boxes",
    "Reload": "bi-arrow-clockwise",
    "Search": "bi-search",
    "Edit": "bi-pencil-square",
    "Create": "bi-plus-circle",
    "Run": "bi-play-circle",
    "Refresh": "bi-arrow-clockwise",
    "Delete": "bi-trash3",
    "History": "bi-clock-history",
    "Alert": "bi-exclamation-triangle",
    "Value": "bi-cash-stack",
    "Engagement": "bi-activity",
    "Priority": "bi-flag",
    "Channel": "bi-broadcast",
    "Table": "bi-table",
    "Chart": "bi-graph-up-arrow",
    "Guide": "bi-info-circle",
}


def normalize_icon_class(icon):
    """Return a safe Bootstrap Icons class name."""
    if not icon:
        return "bi-circle"
    raw = str(icon).strip()
    icon_class = ICON_MAP.get(raw, PAGE_ICONS.get(raw, raw))
    if not icon_class.startswith("bi-"):
        return "bi-circle"
    return icon_class


def icon_html(icon, extra_class="", label=None):
    """Return safe HTML for a Bootstrap icon."""
    icon_class = escape(normalize_icon_class(icon), quote=True)
    classes = f"bi {icon_class}"
    if extra_class:
        classes = f"{classes} {escape(str(extra_class), quote=True)}"
    aria = "aria-hidden='true'" if label is None else f"aria-label='{escape(str(label), quote=True)}'"
    return f"<i class='{classes}' {aria}></i>"


def page_icon_html(page_name, extra_class=""):
    """Return safe HTML for the configured page icon."""
    return icon_html(PAGE_ICONS.get(page_name, "bi-circle"), extra_class=extra_class, label=page_name)


def icon_label_html(label, icon=None, extra_class=""):
    """Return icon and escaped label as a compact HTML fragment."""
    label_html = escape(str(label))
    return (
        f"<span class='{escape(str(extra_class), quote=True)}'>"
        f"{icon_html(icon or label)}<span>{label_html}</span></span>"
    )


def nav_link_html(page_name, active=False):
    """Return a safe sidebar navigation link that preserves internal page keys."""
    if page_name not in PAGE_LABELS:
        label = page_name
    else:
        label = PAGE_LABELS[page_name]
    active_class = " is-active" if active else ""
    href = f"?page={quote(page_name)}"
    return (
        f"<a class='osmos-nav-link{active_class}' href='{href}' title='{escape(page_name, quote=True)}'>"
        f"{page_icon_html(page_name, 'osmos-nav-icon')}"
        f"<span>{escape(label)}</span>"
        f"</a>"
    )
