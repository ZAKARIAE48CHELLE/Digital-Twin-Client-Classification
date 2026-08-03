"""CSS tokens and Streamlit-compatible styling for the OSMOS design system."""

from ui.icons import BOOTSTRAP_ICONS_CDN


THEME_TOKENS = {
    "Light": {
        "--osmos-bg": "#F8FAFC",
        "--osmos-bg-soft": "#F1F5F9",
        "--osmos-card-bg": "#FFFFFF",
        "--osmos-sidebar-bg": "#FFFFFF",
        "--osmos-sidebar-muted": "#F1F5F9",
        "--osmos-text": "#0F172A",
        "--osmos-secondary": "#475569",
        "--osmos-muted": "#64748B",
        "--osmos-border": "#E5E7EB",
        "--osmos-border-strong": "#CBD5E1",
        "--osmos-primary": "#1E3A8A",
        "--osmos-primary-accent": "#2563EB",
        "--osmos-primary-soft": "#DBEAFE",
        "--osmos-teal": "#0F766E",
        "--osmos-success": "#16A34A",
        "--osmos-warning": "#D97706",
        "--osmos-danger": "#DC2626",
        "--osmos-purple": "#7C3AED",
        "--osmos-shadow": "0 8px 24px rgba(15, 23, 42, 0.08)",
        "--osmos-shadow-sm": "0 2px 8px rgba(15, 23, 42, 0.06)",
        "--osmos-overlay": "rgba(255, 255, 255, 0.94)",
        "--osmos-chart-grid": "rgba(148, 163, 184, 0.24)",
        "--osmos-input-bg": "#FFFFFF",
        "--osmos-table-row-alt": "#F8FAFC",
        "--osmos-table-canvas-filter": "none",
    },
    "Dark": {
        "--osmos-bg": "#0F172A",
        "--osmos-bg-soft": "#020617",
        "--osmos-card-bg": "#111827",
        "--osmos-sidebar-bg": "#020617",
        "--osmos-sidebar-muted": "#0B1120",
        "--osmos-text": "#F8FAFC",
        "--osmos-secondary": "#CBD5E1",
        "--osmos-muted": "#94A3B8",
        "--osmos-border": "#334155",
        "--osmos-border-strong": "#475569",
        "--osmos-primary": "#60A5FA",
        "--osmos-primary-accent": "#60A5FA",
        "--osmos-primary-soft": "rgba(96, 165, 250, 0.16)",
        "--osmos-teal": "#2DD4BF",
        "--osmos-success": "#4ADE80",
        "--osmos-warning": "#FBBF24",
        "--osmos-danger": "#F87171",
        "--osmos-purple": "#A78BFA",
        "--osmos-shadow": "0 18px 48px rgba(0, 0, 0, 0.38)",
        "--osmos-shadow-sm": "0 6px 16px rgba(0, 0, 0, 0.28)",
        "--osmos-overlay": "rgba(15, 23, 42, 0.94)",
        "--osmos-chart-grid": "rgba(148, 163, 184, 0.20)",
        "--osmos-input-bg": "#0B1120",
        "--osmos-table-row-alt": "#0B1120",
        "--osmos-table-canvas-filter": "none",
    },
}

BASE_TOKENS = {
    "--osmos-radius-sm": "8px",
    "--osmos-radius": "16px",
    "--osmos-radius-lg": "20px",
    "--osmos-space-1": "4px",
    "--osmos-space-2": "8px",
    "--osmos-space-3": "12px",
    "--osmos-space-4": "16px",
    "--osmos-space-5": "24px",
    "--osmos-space-6": "32px",
    "--osmos-font": "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    "--osmos-display-font": "'Outfit', 'Plus Jakarta Sans', sans-serif",
    "--osmos-mono-font": "'JetBrains Mono', 'SFMono-Regular', Consolas, monospace",
}


def normalize_theme(theme):
    """Return a supported theme name, defaulting to Light."""
    if isinstance(theme, str):
        lowered = theme.strip().lower()
        if lowered == "dark":
            return "Dark"
        if lowered == "light":
            return "Light"
    return "Light"


def get_theme_tokens(theme):
    """Return merged base and theme-specific design tokens."""
    normalized = normalize_theme(theme)
    return {**BASE_TOKENS, **THEME_TOKENS[normalized]}


def _token_css(theme):
    tokens = get_theme_tokens(theme)
    lines = [f"        {name}: {value};" for name, value in tokens.items()]
    alias_lines = [
        "        --bg-main: var(--osmos-bg);",
        "        --bg-surface: var(--osmos-bg-soft);",
        "        --panel: var(--osmos-card-bg);",
        "        --panel-solid: var(--osmos-card-bg);",
        "        --panel-2: var(--osmos-card-bg);",
        "        --panel-3: var(--osmos-sidebar-muted);",
        "        --panel-hover: var(--osmos-primary-soft);",
        "        --line: var(--osmos-border);",
        "        --line-strong: var(--osmos-border-strong);",
        "        --text-main: var(--osmos-text);",
        "        --text-muted: var(--osmos-muted);",
        "        --text-faint: var(--osmos-muted);",
        "        --cyan: var(--osmos-primary-accent);",
        "        --teal: var(--osmos-teal);",
        "        --indigo: var(--osmos-primary);",
        "        --amber: var(--osmos-warning);",
        "        --rose: var(--osmos-danger);",
        "        --green: var(--osmos-success);",
        "        --blue: var(--osmos-primary-accent);",
        "        --violet: var(--osmos-purple);",
        "        --radius-sm: var(--osmos-radius-sm);",
        "        --radius: var(--osmos-radius);",
        "        --radius-lg: var(--osmos-radius-lg);",
        "        --shadow-sm: var(--osmos-shadow-sm);",
        "        --shadow-md: var(--osmos-shadow);",
        "        --shadow-glow: 0 0 0 rgba(0, 0, 0, 0);",
    ]
    return "\n".join(lines + alias_lines)


def build_design_system_css(theme="Light"):
    """Generate the complete OSMOS design-system CSS for a theme."""
    normalized = normalize_theme(theme)
    return f"""
<link rel="stylesheet" href="{BOOTSTRAP_ICONS_CDN}">
<style id="osmos-design-system">
    :root {{
{_token_css(normalized)}
    }}

    html, body, .stApp, [data-testid="stAppViewContainer"] {{
        background: var(--osmos-bg) !important;
        color: var(--osmos-text) !important;
        font-family: var(--osmos-font) !important;
    }}

    [data-testid="stAppViewContainer"]::before {{
        background:
            linear-gradient(180deg, var(--osmos-bg) 0%, var(--osmos-bg) 54%, var(--osmos-bg-soft) 100%) !important;
        opacity: 1 !important;
    }}

    [data-testid="stMainBlockContainer"], section.main > div {{
        max-width: 1540px !important;
        padding-top: 24px !important;
        padding-right: 32px !important;
        padding-left: 32px !important;
        padding-bottom: 48px !important;
    }}

    h1, h2, h3, h4 {{
        color: var(--osmos-text) !important;
        font-family: var(--osmos-display-font) !important;
        letter-spacing: 0 !important;
    }}

    p, li, label, .stMarkdown, [data-testid="stMarkdownContainer"] {{
        color: var(--osmos-secondary) !important;
    }}

    .page-hero, .osmos-page-header {{
        position: relative;
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        gap: 14px;
        align-items: start;
        margin: 0 0 26px 0;
        padding: 0 0 20px 0;
        border-bottom: 1px solid var(--osmos-border) !important;
    }}

    .page-hero::after, .osmos-page-header::after {{
        content: "";
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 128px;
        height: 2px;
        background: linear-gradient(90deg, var(--osmos-primary-accent), var(--osmos-teal), transparent);
    }}

    .osmos-page-header-icon {{
        display: inline-grid;
        place-items: center;
        width: 46px;
        height: 46px;
        border-radius: 14px;
        background: var(--osmos-primary-soft);
        color: var(--osmos-primary-accent);
        border: 1px solid color-mix(in srgb, var(--osmos-primary-accent) 28%, transparent);
        font-size: 21px;
    }}

    .page-kicker, .osmos-kicker {{
        display: inline-flex;
        align-items: center;
        width: fit-content;
        gap: 8px;
        padding: 4px 10px;
        border-radius: 999px;
        background: var(--osmos-primary-soft) !important;
        border: 1px solid color-mix(in srgb, var(--osmos-primary-accent) 26%, transparent) !important;
        color: var(--osmos-primary) !important;
        font-size: 11px !important;
        font-weight: 800 !important;
        letter-spacing: 0 !important;
        text-transform: uppercase;
        margin-bottom: 4px;
    }}

    .page-hero h1, .osmos-page-title {{
        margin: 2px 0 0 0 !important;
        color: var(--osmos-text) !important;
        background: none !important;
        -webkit-text-fill-color: currentColor !important;
        font-size: 34px !important;
        line-height: 1.15 !important;
        font-weight: 800 !important;
    }}

    .page-hero p, .osmos-page-subtitle {{
        max-width: 860px;
        margin: 5px 0 0 0 !important;
        color: var(--osmos-secondary) !important;
        font-size: 14.5px !important;
        line-height: 1.58;
    }}

    .osmos-page-badge-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
    }}

    [data-testid="stSidebar"] {{
        background: var(--osmos-sidebar-bg) !important;
        border-right: 1px solid var(--osmos-border) !important;
        box-shadow: var(--osmos-shadow-sm) !important;
    }}

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {{
        color: var(--osmos-secondary) !important;
    }}

    .sidebar-brand {{
        padding: 18px 8px 14px;
    }}

    .brand-mark {{
        background: linear-gradient(135deg, var(--osmos-primary), var(--osmos-teal)) !important;
        box-shadow: 0 12px 26px color-mix(in srgb, var(--osmos-primary-accent) 22%, transparent) !important;
    }}

    .brand-title {{
        color: var(--osmos-text) !important;
        letter-spacing: 0.04em !important;
    }}

    .brand-subtitle {{
        color: var(--osmos-primary-accent) !important;
        letter-spacing: 0 !important;
    }}

    .sidebar-rule {{
        height: 1px;
        background: var(--osmos-border) !important;
        margin: 8px 0 14px;
    }}

    .osmos-theme-title {{
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--osmos-text);
        font-size: 12px;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 8px;
    }}

    .osmos-theme-title-standalone {{
        margin: 8px 4px 6px !important;
    }}

    [data-testid="stSidebar"] [data-testid="stRadio"] {{
        padding: 0 4px 12px;
    }}

    [data-testid="stSidebar"] [data-testid="stRadio"] label p {{
        font-size: 12.5px !important;
        font-weight: 700 !important;
    }}
    .osmos-sidebar-nav {{
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin: 2px 0 14px;
    }}

    [data-testid="stSidebar"] .osmos-sidebar-nav + div,
    [data-testid="stSidebar"] .osmos-sidebar-nav ~ div {{
        max-width: 100%;
    }}

    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] .stButton > button {{
        width: 100% !important;
        min-height: 42px !important;
        justify-content: flex-start !important;
        text-align: left !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        white-space: normal !important;
        line-height: 1.25 !important;
        overflow-wrap: anywhere !important;
        box-shadow: none !important;
        transform: none !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}

    /* Active Navigation Button (Primary State) */
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
    [data-testid="stSidebar"] button[kind="primary"],
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"],
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: 1px solid #60a5fa !important;
        border-left: 5px solid #60a5fa !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 18px rgba(37, 99, 235, 0.45) !important;
    }}

    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stSidebar"] button[kind="primary"]:hover,
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
        background-color: #1d4ed8 !important;
        color: #ffffff !important;
        transform: translateX(2px) !important;
    }}

    /* Inactive Navigation Buttons (Secondary State) */
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
    [data-testid="stSidebar"] button[kind="secondary"],
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"],
    [data-testid="stSidebar"] .stButton > button[kind="secondary"],
    [data-testid="stSidebar"] button:not([data-testid="stBaseButton-primary"]):not([kind="primary"]) {{
        background: var(--osmos-sidebar-muted, rgba(255, 255, 255, 0.04)) !important;
        background-color: var(--osmos-sidebar-muted, rgba(255, 255, 255, 0.04)) !important;
        color: var(--osmos-secondary, #cbd5e1) !important;
        border: 1px solid var(--osmos-border, rgba(255, 255, 255, 0.08)) !important;
        font-weight: 600 !important;
        box-shadow: none !important;
    }}

    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stSidebar"] button[kind="secondary"]:hover,
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover,
    [data-testid="stSidebar"] button:not([data-testid="stBaseButton-primary"]):not([kind="primary"]):hover {{
        background: var(--osmos-primary-soft, rgba(56, 189, 248, 0.14)) !important;
        background-color: var(--osmos-primary-soft, rgba(56, 189, 248, 0.14)) !important;
        color: var(--osmos-text, #ffffff) !important;
        border-color: color-mix(in srgb, var(--osmos-primary-accent, #38bdf8) 35%, transparent) !important;
        transform: translateX(3px) !important;
    }}

    [data-testid="stSidebar"] button span,
    [data-testid="stSidebar"] button p,
    [data-testid="stSidebar"] button div,
    [data-testid="stSidebar"] button [data-testid="stIconMaterial"] {{
        color: inherit !important;
        font-weight: inherit !important;
    }}



    .glass-card,
    .glass-card-accent,
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stForm"],
    [data-testid="stExpander"],
    [data-testid="stMetric"],
    .persona-card,
    .osmos-card,
    .osmos-alert-card,
    .osmos-persona-card,

    .glass-card-accent {{
        border-left: 4px solid var(--osmos-primary-accent) !important;
    }}

    div[style*="background:rgba(30, 41, 59"],
    div[style*="background: rgba(30, 41, 59"],
    div[style*="background:rgba(15, 23, 42"],
    div[style*="background: rgba(15, 23, 42"],
    div[style*="background:rgba(129,140,248"],
    div[style*="background: rgba(129,140,248"],
    div[style*="background:linear-gradient(135deg"],
    div[style*="background: linear-gradient(135deg"] {{
        background: var(--osmos-card-bg) !important;
        border-color: var(--osmos-border) !important;
        color: var(--osmos-text) !important;
        box-shadow: var(--osmos-shadow) !important;
    }}

    [style*="color:#f8fafc"],
    [style*="color: #f8fafc"],
    [style*="color:#f1f5f9"],
    [style*="color: #f1f5f9"],
    [style*="color:#e2e8f0"],
    [style*="color: #e2e8f0"],
    [style*="color:#cbd5e1"],
    [style*="color: #cbd5e1"] {{
        color: var(--osmos-text) !important;
    }}

    [style*="color:#94a3b8"],
    [style*="color: #94a3b8"],
    [style*="color:#64748b"],
    [style*="color: #64748b"] {{
        color: var(--osmos-muted) !important;
    }}

    .section-header {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 24px 0 16px !important;
        padding-bottom: 10px !important;
        border-bottom: 1px solid var(--osmos-border) !important;
    }}

    .section-header .icon {{
        display: inline-grid !important;
        place-items: center;
        width: 32px;
        height: 32px;
        border-radius: 10px;
        background: var(--osmos-primary-soft);
        border: 1px solid color-mix(in srgb, var(--osmos-primary-accent) 24%, transparent);
        color: var(--osmos-primary-accent) !important;
        font-size: 16px !important;
        line-height: 1;
    }}

    .section-header .title {{
        color: var(--osmos-text) !important;
        font-family: var(--osmos-display-font) !important;
        font-size: 17px !important;
        font-weight: 750 !important;
    }}

    .kpi-container, .osmos-kpi-grid {{
        display: grid !important;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)) !important;
        gap: 14px !important;
        margin-bottom: 28px !important;
    }}

    .kpi-card, .osmos-metric-card {{
        position: relative;
        min-height: 128px;
        padding: 18px !important;
        border-radius: var(--osmos-radius) !important;
        background: var(--osmos-card-bg) !important;
        border: 1px solid var(--osmos-border) !important;
        box-shadow: var(--osmos-shadow) !important;
        overflow: hidden;
    }}

    .kpi-card::before, .osmos-metric-card::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--osmos-primary-accent), var(--osmos-teal));
    }}

    .kpi-card:hover, .osmos-metric-card:hover {{
        transform: translateY(-2px) !important;
        border-color: var(--osmos-border-strong) !important;
        box-shadow: var(--osmos-shadow) !important;
    }}

    .kpi-icon, .osmos-metric-icon {{
        position: absolute;
        top: 16px;
        right: 16px;
        display: inline-flex;
        color: var(--osmos-primary-accent) !important;
        font-size: 21px !important;
        opacity: 1;
    }}

    .kpi-val, .osmos-metric-value {{
        color: var(--osmos-text) !important;
        font-family: var(--osmos-display-font) !important;
        font-size: 31px !important;
        font-weight: 800 !important;
        line-height: 1.05 !important;
        overflow-wrap: anywhere;
        max-width: 100%;
    }}

    .kpi-label, .osmos-metric-title {{
        color: var(--osmos-muted) !important;
        font-size: 11px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 8px;
    }}

    .osmos-metric-delta {{
        display: inline-flex;
        gap: 4px;
        align-items: center;
        margin-top: 10px;
        color: var(--osmos-success);
        font-size: 12px;
        font-weight: 800;
    }}

    .osmos-badge,
    .tag,
    .persona-segment-tag,
    .persona-client-count,
    .status-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        border-radius: 999px !important;
        border: 1px solid var(--osmos-border);
        background: var(--osmos-primary-soft);
        color: var(--osmos-primary) !important;
        font-size: 11.5px;
        font-weight: 800 !important;
        padding: 5px 10px !important;
        line-height: 1.1;
    }}

    .osmos-badge.success, .tag-active, .tag-client, .tag-loyal {{
        background: color-mix(in srgb, var(--osmos-success) 14%, transparent) !important;
        color: var(--osmos-success) !important;
        border-color: color-mix(in srgb, var(--osmos-success) 28%, transparent) !important;
    }}

    .osmos-badge.warning, .tag-warm, .tag-medium {{
        background: color-mix(in srgb, var(--osmos-warning) 14%, transparent) !important;
        color: var(--osmos-warning) !important;
        border-color: color-mix(in srgb, var(--osmos-warning) 28%, transparent) !important;
    }}

    .osmos-badge.danger, .tag-hot, .tag-churn {{
        background: color-mix(in srgb, var(--osmos-danger) 12%, transparent) !important;
        color: var(--osmos-danger) !important;
        border-color: color-mix(in srgb, var(--osmos-danger) 28%, transparent) !important;
    }}

    .osmos-badge.purple, .tag-vip {{
        background: color-mix(in srgb, var(--osmos-purple) 13%, transparent) !important;
        color: var(--osmos-purple) !important;
        border-color: color-mix(in srgb, var(--osmos-purple) 28%, transparent) !important;
    }}

    .color-total {{ color: var(--osmos-text) !important; }}
    .color-prospect {{ color: var(--osmos-primary-accent) !important; }}
    .color-client, .color-active {{ color: var(--osmos-success) !important; }}
    .color-cold {{ color: var(--osmos-muted) !important; }}
    .color-warm {{ color: var(--osmos-warning) !important; }}
    .color-hot, .color-churn {{ color: var(--osmos-danger) !important; }}
    .color-vip {{ color: var(--osmos-purple) !important; }}

    .score-bar-label {{
        display: flex;
        justify-content: space-between;
        color: var(--osmos-muted) !important;
        font-size: 13px !important;
    }}

    .score-bar-track {{
        background: var(--osmos-bg-soft) !important;
        border: 1px solid var(--osmos-border) !important;
    }}

    .fill-indigo, .fill-violet, .fill-cyan {{
        background: linear-gradient(90deg, var(--osmos-primary-accent), var(--osmos-teal)) !important;
    }}

    .fill-rose {{ background: linear-gradient(90deg, var(--osmos-danger), var(--osmos-warning)) !important; }}
    .fill-amber {{ background: linear-gradient(90deg, var(--osmos-warning), var(--osmos-teal)) !important; }}
    .fill-green {{ background: linear-gradient(90deg, var(--osmos-success), var(--osmos-teal)) !important; }}

    [data-testid="stSelectbox"] > div > div,
    [data-testid="stTextInput"] > div > div > input,
    [data-testid="stNumberInput"] > div > div > input,
    [data-testid="stTextArea"] > div > div > textarea,
    [data-baseweb="select"] > div {{
        background: var(--osmos-input-bg) !important;
        border: 1px solid var(--osmos-border) !important;
        border-radius: 12px !important;
        color: var(--osmos-text) !important;
        box-shadow: none !important;
    }}

    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [data-baseweb="select"] [role="listbox"],
    ul[data-baseweb="menu"] {{
        background: var(--osmos-card-bg) !important;
        border: 1px solid var(--osmos-border) !important;
        color: var(--osmos-text) !important;
        box-shadow: var(--osmos-shadow) !important;
    }}

    [role="option"], [data-baseweb="menu"] li {{
        color: var(--osmos-secondary) !important;
    }}

    [role="option"]:hover,
    [role="option"][aria-selected="true"],
    [data-baseweb="menu"] li:hover,
    [data-baseweb="menu"] li[aria-selected="true"] {{
        background: var(--osmos-primary-soft) !important;
        color: var(--osmos-text) !important;
    }}

    [data-testid="stPlotlyChart"],
    [data-testid="stVegaLiteChart"],
    [data-testid="stPyplot"] {{
        background: var(--osmos-card-bg) !important;
        border: 1px solid var(--osmos-border) !important;
        border-radius: var(--osmos-radius) !important;
        box-shadow: var(--osmos-shadow-sm) !important;
        padding: 8px !important;
        overflow: hidden;
    }}

    [data-testid="stPlotlyChart"] svg,
    [data-testid="stPlotlyChart"] .main-svg {{
        background: transparent !important;
    }}

    [data-testid="stSelectbox"],
    [data-testid="stMultiSelect"],
    [data-testid="stRadio"],
    [data-testid="stSlider"],
    [data-testid="stCheckbox"] {{
        color: var(--osmos-text) !important;
    }}

    [data-testid="stSelectbox"] label,
    [data-testid="stMultiSelect"] label,
    [data-testid="stRadio"] label,
    [data-testid="stSlider"] label,
    [data-testid="stCheckbox"] label {{
        color: var(--osmos-secondary) !important;
        font-weight: 700 !important;
    }}

    [data-baseweb="select"] span,
    [data-baseweb="select"] input,
    [data-baseweb="select"] svg,
    [data-baseweb="popover"] span,
    [data-baseweb="popover"] div,
    [data-baseweb="menu"] div,
    [data-baseweb="menu"] span {{
        color: var(--osmos-text) !important;
        fill: var(--osmos-text) !important;
    }}

    [data-baseweb="select"] > div:hover,
    [data-testid="stSelectbox"] > div > div:hover,
    [data-testid="stMultiSelect"] > div > div:hover {{
        border-color: var(--osmos-primary-accent) !important;
        box-shadow: 0 0 0 3px color-mix(in srgb, var(--osmos-primary-accent) 14%, transparent) !important;
    }}

    [data-baseweb="popover"] [role="listbox"],
    [data-baseweb="popover"] ul,
    [data-baseweb="popover"] li,
    [data-baseweb="menu"] ul,
    [data-baseweb="menu"] li {{
        background: var(--osmos-card-bg) !important;
        color: var(--osmos-text) !important;
        border-color: var(--osmos-border) !important;
    }}

    [data-testid="stRadio"] [role="radiogroup"] {{
        gap: 8px !important;
    }}

    [data-testid="stRadio"] label {{
        background: var(--osmos-card-bg) !important;
        border: 1px solid var(--osmos-border) !important;
        border-radius: 999px !important;
        padding: 6px 10px !important;
    }}

    [data-testid="stRadio"] label:has(input:checked) {{
        background: var(--osmos-primary-soft) !important;
        border-color: color-mix(in srgb, var(--osmos-primary-accent) 36%, transparent) !important;
    }}

    [data-testid="stExpander"] details,
    [data-testid="stExpander"] summary {{
        background: var(--osmos-card-bg) !important;
        color: var(--osmos-text) !important;
        border-color: var(--osmos-border) !important;
    }}

    [data-testid="stExpander"] summary:hover {{
        background: var(--osmos-bg-soft) !important;
    }}
    [data-testid="stMain"] .stButton > button,
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button,
    section.main .stButton > button,
    section.main [data-testid="stFormSubmitButton"] button {{
        min-height: 42px !important;
        border-radius: 12px !important;
        border: 1px solid var(--osmos-primary-accent) !important;
        background: var(--osmos-primary) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 13.5px !important;
        box-shadow: var(--osmos-shadow-sm) !important;
        letter-spacing: 0 !important;
        white-space: normal !important;
    }}

    [data-testid="stMain"] .stButton > button:hover,
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button:hover,
    section.main .stButton > button:hover,
    section.main [data-testid="stFormSubmitButton"] button:hover {{
        transform: translateY(-1px) !important;
        background: var(--osmos-primary-accent) !important;
        border-color: var(--osmos-primary-accent) !important;
        box-shadow: var(--osmos-shadow) !important;
    }

    [data-testid="stMain"] .stButton > button[data-testid="stBaseButton-secondary"],
    section.main .stButton > button[data-testid="stBaseButton-secondary"] {
        background: var(--osmos-card-bg) !important;
        color: var(--osmos-primary) !important;
        border-color: var(--osmos-border) !important;
        box-shadow: none !important;
    }

    /* Clean stDataFrame Wrapper */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--osmos-border) !important;
        border-radius: var(--osmos-radius) !important;
        overflow: hidden !important;
        box-shadow: var(--osmos-shadow-sm) !important;
    }

    /* Standard HTML Tables (st.table, table.dataframe) */
    [data-testid="stTable"] table,
    [data-testid="stTable"] td,
    [data-testid="stTable"] th,
    table.dataframe,
    table.dataframe td,
    table.dataframe th,
    .osmos-table,
    table {
        background: var(--osmos-card-bg) !important;
        background-color: var(--osmos-card-bg) !important;
        color: var(--osmos-text) !important;
        border-color: var(--osmos-border) !important;
    }

    [data-testid="stTable"] thead th,
    table.dataframe thead th,
    .osmos-table thead th,
    table thead th {
        background: var(--osmos-bg-soft) !important;
        background-color: var(--osmos-bg-soft) !important;
        color: var(--osmos-text) !important;
        font-weight: 800 !important;
        border-bottom: 2px solid var(--osmos-border) !important;
    }

    [data-testid="stTable"] tbody tr:nth-child(even) td,
    table.dataframe tbody tr:nth-child(even) td,
    table tbody tr:nth-child(even) td {
        background: var(--osmos-table-row-alt) !important;
        background-color: var(--osmos-table-row-alt) !important;
    }

    [data-testid="stTable"] tbody tr:hover td,
    table.dataframe tbody tr:hover td,
    table tbody tr:hover td {
        background: var(--osmos-primary-soft) !important;
        background-color: var(--osmos-primary-soft) !important;
    }

    [data-testid="stTabs"] button {
        border-radius: 10px 10px 0 0 !important;
        color: var(--osmos-muted) !important;
        font-weight: 800 !important;
        letter-spacing: 0 !important;
    }}

    [data-testid="stTabs"] button[aria-selected="true"] {{
        color: var(--osmos-primary) !important;
        border-bottom-color: var(--osmos-primary-accent) !important;
        background: var(--osmos-primary-soft) !important;
    }}

    [data-testid="stMetric"] {{
        padding: 16px 18px !important;
    }}

    [data-testid="stMetricValue"] {{
        color: var(--osmos-primary) !important;
        font-family: var(--osmos-display-font) !important;
        font-weight: 800 !important;
    }}

    [data-testid="stMetricLabel"] {{
        color: var(--osmos-muted) !important;
        font-size: 12px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
    }}

    [data-testid="stAlert"] {{
        border-radius: var(--osmos-radius) !important;
        border: 1px solid var(--osmos-border) !important;
        background: var(--osmos-card-bg) !important;
        color: var(--osmos-text) !important;
        box-shadow: var(--osmos-shadow-sm) !important;
    }}

    header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] {{
        background: var(--osmos-overlay) !important;
        border-bottom: 1px solid var(--osmos-border) !important;
        backdrop-filter: blur(16px) !important;
    }}

    .privacy-card {{
        background: color-mix(in srgb, var(--osmos-danger) 8%, transparent) !important;
        border-color: color-mix(in srgb, var(--osmos-danger) 24%, transparent) !important;
        color: var(--osmos-secondary) !important;
    }}

    .side-panel-icon {{
        color: var(--osmos-primary-accent);
        font-size: 17px;
        width: 18px;
    }}

    .osmos-journey-tree-flow {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 12px;
        align-items: stretch;
        margin: 4px 0 24px;
    }}

    .osmos-journey-node-wrap {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 10px;
        align-items: center;
        min-width: 0;
    }}

    .osmos-journey-node {{
        min-height: 188px;
        background: var(--osmos-card-bg);
        border: 1px solid var(--osmos-border);
        border-top: 3px solid var(--osmos-primary-accent);
        border-radius: var(--osmos-radius);
        box-shadow: var(--osmos-shadow-sm);
        padding: 14px;
        color: var(--osmos-text);
    }}

    .osmos-journey-node-top {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 10px;
    }}

    .osmos-journey-icon {{
        display: inline-grid;
        place-items: center;
        width: 34px;
        height: 34px;
        border-radius: 10px;
        background: var(--osmos-primary-soft);
        color: var(--osmos-primary-accent);
        border: 1px solid color-mix(in srgb, var(--osmos-primary-accent) 24%, transparent);
        flex: 0 0 auto;
    }}

    .osmos-journey-step {{
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        background: var(--osmos-bg-soft);
        color: var(--osmos-muted);
        border: 1px solid var(--osmos-border);
        padding: 4px 8px;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
    }}

    .osmos-journey-stage {{
        color: var(--osmos-text);
        font-size: 14px;
        font-weight: 800;
        line-height: 1.28;
        margin-bottom: 12px;
        overflow-wrap: anywhere;
    }}

    .osmos-journey-meta {{
        display: grid;
        gap: 7px;
    }}

    .osmos-journey-meta div {{
        display: grid;
        gap: 2px;
        padding: 7px 9px;
        border-radius: 8px;
        background: var(--osmos-bg-soft);
        border: 1px solid var(--osmos-border);
    }}

    .osmos-journey-meta span {{
        color: var(--osmos-muted);
        font-size: 10.5px;
        font-weight: 800;
        text-transform: uppercase;
    }}

    .osmos-journey-meta b {{
        color: var(--osmos-secondary);
        font-size: 12px;
        line-height: 1.25;
        overflow-wrap: anywhere;
    }}

    .osmos-journey-connector {{
        display: inline-grid;
        place-items: center;
        width: 28px;
        height: 28px;
        border-radius: 999px;
        background: var(--osmos-primary-soft);
        color: var(--osmos-primary-accent);
        border: 1px solid color-mix(in srgb, var(--osmos-primary-accent) 24%, transparent);
        font-weight: 900;
        box-shadow: var(--osmos-shadow-sm);
    }}
    .st-key-btn_open_page_guide,
    .st-key-btn_close_page_guide,
    div[data-testid="stButton"]:has(button[key="btn_open_page_guide"]),
    div[data-testid="stButton"]:has(button[key="btn_close_page_guide"]) {{
        position: fixed !important;
        bottom: 24px !important;
        right: 24px !important;
        z-index: 999998 !important;
        width: auto !important;
    }}

    .st-key-btn_open_page_guide button,
    .st-key-btn_close_page_guide button,
    div[data-testid="stButton"]:has(button[key="btn_open_page_guide"]) button,
    div[data-testid="stButton"]:has(button[key="btn_close_page_guide"]) button {{
        border-radius: 999px !important;
        padding: 9px 18px !important;
        background: var(--osmos-primary) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 13.5px !important;
        box-shadow: var(--osmos-shadow) !important;
        border: 1px solid var(--osmos-primary-accent) !important;
        transition: all 0.18s ease-in-out !important;
    }}

    .st-key-btn_open_page_guide button:hover,
    .st-key-btn_close_page_guide button:hover {{
        transform: translateY(-2px) !important;
        background: var(--osmos-primary-accent) !important;
    }}

    .osmos-floating-panel {{
        position: fixed;
        bottom: 82px;
        right: 24px;
        width: min(390px, calc(100vw - 32px));
        max-height: 75vh;
        overflow-y: auto;
        background: var(--osmos-card-bg);
        border: 1px solid var(--osmos-border);
        border-radius: var(--osmos-radius);
        box-shadow: var(--osmos-shadow);
        padding: 20px;
        z-index: 999999;
        color: var(--osmos-text);
        font-family: var(--osmos-font);
    }}

    .osmos-panel-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid var(--osmos-border);
        padding-bottom: 10px;
        margin-bottom: 12px;
    }}

    .osmos-panel-title {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 15px;
        font-weight: 800;
        color: var(--osmos-primary);
        margin: 0;
    }}

    .osmos-panel-page-title {{
        font-size: 15px;
        font-weight: 800;
        color: var(--osmos-text);
        margin-bottom: 8px;
    }}

    .osmos-panel-section-title {{
        display: flex;
        align-items: center;
        gap: 7px;
        font-size: 11px;
        font-weight: 800;
        color: var(--osmos-muted);
        text-transform: uppercase;
        letter-spacing: 0;
        margin-top: 12px;
        margin-bottom: 4px;
    }}

    .osmos-panel-text {{
        font-size: 13px;
        color: var(--osmos-secondary);
        line-height: 1.5;
        margin: 0 0 10px 0;
    }}

    .osmos-flow-badge {{
        background: var(--osmos-primary-soft);
        color: var(--osmos-primary);
        border: 1px solid color-mix(in srgb, var(--osmos-primary-accent) 28%, transparent);
        padding: 7px 10px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 800;
        margin-bottom: 12px;
        display: inline-flex;
        align-items: center;
        gap: 7px;
    }}

    .osmos-mini-flow {{
        background: var(--osmos-bg-soft);
        border: 1px solid var(--osmos-border);
        padding: 7px 10px;
        border-radius: 8px;
        font-size: 11px;
        color: var(--osmos-primary);
        font-family: var(--osmos-mono-font);
        margin-bottom: 10px;
    }}

    .osmos-tip-box {{
        background: color-mix(in srgb, var(--osmos-warning) 10%, transparent);
        border-left: 3px solid var(--osmos-warning);
        padding: 9px 12px;
        border-radius: 8px;
        font-size: 12px;
        color: var(--osmos-secondary);
        margin-top: 12px;
    }}

    .osmos-db-note {{
        background: color-mix(in srgb, var(--osmos-warning) 10%, transparent);
        border: 1px solid color-mix(in srgb, var(--osmos-warning) 28%, transparent);
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 12px;
        color: var(--osmos-secondary);
        margin-bottom: 12px;
    }}
    @media (max-width: 720px) {{
        [data-testid="stMainBlockContainer"], section.main > div {{
            padding-left: 16px !important;
            padding-right: 16px !important;
            padding-top: 18px !important;
        }}
        .page-hero, .osmos-page-header {{
            grid-template-columns: 1fr;
        }}
        h1, .page-hero h1, .osmos-page-title {{
            font-size: 26px !important;
        }}
        .kpi-container, .osmos-kpi-grid {{
            grid-template-columns: 1fr !important;
        }}
        .kpi-card, .osmos-metric-card {{
            min-height: 118px;
        }}
    }}
</style>
"""


def build_theme_style(theme="Light"):
    """Public alias used by tests and Streamlit injection."""
    return build_design_system_css(theme)





