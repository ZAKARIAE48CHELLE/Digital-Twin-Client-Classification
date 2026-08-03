"""Reusable OSMOS UI components rendered as Streamlit-safe HTML."""

from html import escape

from ui.icons import icon_html


BADGE_VARIANTS = {
    "client": "success",
    "prospect": "",
    "vip": "purple",
    "at risk": "danger",
    "high priority": "danger",
    "medium priority": "warning",
    "low priority": "success",
    "postgresql": "success",
    "excel mode": "warning",
    "llm optional": "purple",
    "simulated only": "",
}

SEVERITY_VARIANTS = {
    "success": "success",
    "warning": "warning",
    "error": "danger",
    "danger": "danger",
    "risk": "danger",
    "info": "",
}


def _variant_class(value, default=""):
    return escape(str(value or default), quote=True)


def status_badge_html(label, variant=None, icon=None):
    """Return a status badge that adapts to the active OSMOS theme."""
    label_text = str(label)
    badge_variant = variant or BADGE_VARIANTS.get(label_text.lower(), "")
    icon_fragment = icon_html(icon) if icon else ""
    return (
        f"<span class='osmos-badge {_variant_class(badge_variant)}'>"
        f"{icon_fragment}<span>{escape(label_text)}</span></span>"
    )


def metric_card_html(title, value, delta=None, icon=None, status=None):
    """Return a reusable KPI/metric card."""
    delta_html = f"<div class='osmos-metric-delta'>{escape(str(delta))}</div>" if delta else ""
    status_html = status_badge_html(status) if status else ""
    return f"""
    <div class='osmos-metric-card'>
        <span class='osmos-metric-icon'>{icon_html(icon or title)}</span>
        <div class='osmos-metric-value'>{escape(str(value))}</div>
        <div class='osmos-metric-title'>{escape(str(title))}</div>
        {delta_html}
        {status_html}
    </div>
    """


def insight_card_html(title, body, icon="Info", accent=""):
    """Return an insight card."""
    return f"""
    <div class='osmos-card osmos-insight-card {_variant_class(accent)}' style='padding:18px;'>
        <div style='display:flex;align-items:center;gap:10px;margin-bottom:10px;color:var(--osmos-primary);font-weight:800;'>
            {icon_html(icon)}<span>{escape(str(title))}</span>
        </div>
        <p style='margin:0;color:var(--osmos-secondary);font-size:13.5px;line-height:1.55;'>{escape(str(body))}</p>
    </div>
    """


def alert_card_html(severity, title, description, recommended_action=None):
    """Return a themed alert card."""
    variant = SEVERITY_VARIANTS.get(str(severity).lower(), "")
    icon = "Warning" if variant in {"warning", "danger"} else "Info"
    action_html = ""
    if recommended_action:
        action_html = (
            "<div style='margin-top:10px;font-size:12.5px;color:var(--osmos-secondary);'>"
            f"<strong>Recommended action:</strong> {escape(str(recommended_action))}</div>"
        )
    return f"""
    <div class='osmos-alert-card {_variant_class(variant)}' style='padding:16px;border-left:4px solid var(--osmos-{variant or "primary"});'>
        <div style='display:flex;align-items:center;gap:10px;font-weight:800;color:var(--osmos-text);'>
            {icon_html(icon)}<span>{escape(str(title))}</span>
        </div>
        <p style='margin:8px 0 0;color:var(--osmos-secondary);font-size:13px;line-height:1.55;'>{escape(str(description))}</p>
        {action_html}
    </div>
    """


def persona_card_html(persona_name, segment, value_level, risk_level, channel, action):
    """Return a professional persona card."""
    return f"""
    <div class='osmos-persona-card' style='padding:18px;'>
        <div style='display:flex;justify-content:space-between;gap:12px;align-items:start;margin-bottom:12px;'>
            <div>
                <div style='font-size:11px;text-transform:uppercase;font-weight:800;color:var(--osmos-muted);'>Persona</div>
                <div style='font-size:18px;font-weight:800;color:var(--osmos-text);'>{escape(str(persona_name))}</div>
            </div>
            {status_badge_html(segment, icon="Segment")}
        </div>
        <div style='display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;'>
            {status_badge_html(value_level, variant="success", icon="Value")}
            {status_badge_html(risk_level, variant="warning" if str(risk_level).lower() == "medium" else None, icon="Churn Risk")}
            {status_badge_html(channel, icon="Channel")}
        </div>
        <p style='margin:0;color:var(--osmos-secondary);font-size:13px;line-height:1.55;'>{escape(str(action))}</p>
    </div>
    """


def timeline_step_card_html(step_number, stage_name, event, before_state, after_state, recommendation):
    """Return a themed lifecycle timeline card."""
    return f"""
    <div class='osmos-timeline-card' style='padding:18px;margin-bottom:14px;border-left:4px solid var(--osmos-primary-accent);'>
        <div style='display:flex;justify-content:space-between;gap:12px;align-items:start;margin-bottom:12px;'>
            <div>
                <div style='font-size:11px;text-transform:uppercase;font-weight:800;color:var(--osmos-muted);'>Step {escape(str(step_number))}</div>
                <div style='font-size:17px;font-weight:800;color:var(--osmos-text);'>{escape(str(stage_name))}</div>
            </div>
            {status_badge_html(event, icon="Journey")}
        </div>
        <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-bottom:12px;'>
            <div><strong>Before:</strong> {escape(str(before_state))}</div>
            <div><strong>After:</strong> {escape(str(after_state))}</div>
        </div>
        <p style='margin:0;color:var(--osmos-secondary);font-size:13px;line-height:1.55;'>{escape(str(recommendation))}</p>
    </div>
    """


def button_class(kind="primary"):
    """Return a CSS class name for custom HTML action buttons."""
    allowed = {"primary", "secondary", "danger", "success", "ghost"}
    normalized = str(kind).lower()
    return f"osmos-btn osmos-btn-{normalized if normalized in allowed else 'primary'}"
