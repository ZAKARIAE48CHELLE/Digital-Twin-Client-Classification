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


def render_mermaid_diagram(code: str, height: int = 320):
    """Renders a Mermaid JS diagram inside Streamlit components."""
    import streamlit.components.v1 as components

    code_clean = code.strip()
    html_code = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            background-color: transparent;
            color: #e2e8f0;
            font-family: system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 4px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .mermaid {{
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 16px;
            width: 100%;
            box-sizing: border-box;
            display: flex;
            justify-content: center;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="mermaid">
{code_clean}
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            securityLevel: 'loose',
            themeVariables: {{
                darkMode: true,
                background: '#0f172a',
                primaryColor: '#3b82f6',
                primaryTextColor: '#f8fafc',
                primaryBorderColor: '#60a5fa',
                lineColor: '#94a3b8',
                secondaryColor: '#10b981',
                tertiaryColor: '#f59e0b'
            }}
        }});
    </script>
</body>
</html>"""
    components.html(html_code, height=height, scrolling=True)


def render_rich_markdown_with_diagrams(content_text: str):
    """Parses markdown text and converts any ```mermaid or diagram blocks into graphical Mermaid diagrams."""
    import re
    import streamlit as st

    if not content_text:
        return

    mermaid_pattern = re.compile(
        r"```(?:mermaid|text)?\s*\n((?:flowchart|graph|sequenceDiagram|gantt|classDiagram|stateDiagram|erDiagram|pie|journey|gitGraph)[\s\S]*?)\n```",
        re.IGNORECASE,
    )

    last_idx = 0
    matches = list(mermaid_pattern.finditer(content_text))

    if not matches:
        st.markdown(content_text)
        return

    for match in matches:
        start, end = match.span()

        pre_text = content_text[last_idx:start].strip()
        if pre_text:
            st.markdown(pre_text)

        diagram_code = match.group(1).strip()
        num_lines = len(diagram_code.split("\n"))
        calc_height = max(220, min(650, num_lines * 35 + 80))

        try:
            render_mermaid_diagram(diagram_code, height=calc_height)
        except Exception:
            st.code(diagram_code, language="mermaid")

        last_idx = end

    post_text = content_text[last_idx:].strip()
    if post_text:
        st.markdown(post_text)
