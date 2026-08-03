"""Theme helpers for OSMOS charts."""

from ui.design_system import get_theme_tokens, normalize_theme


OSMOS_CHART_COLORS = [
    "#2563EB",
    "#0F766E",
    "#D97706",
    "#DC2626",
    "#7C3AED",
    "#0891B2",
    "#16A34A",
    "#DB2777",
]


def apply_plotly_theme(fig, theme="Light", height=None, showlegend=None, margin=None):
    """Apply the active OSMOS theme to a Plotly figure in-place and return it."""
    normalized = normalize_theme(theme)
    tokens = get_theme_tokens(normalized)
    bg = tokens["--osmos-card-bg"]
    soft_bg = tokens["--osmos-bg-soft"]
    text = tokens["--osmos-text"]
    muted = tokens["--osmos-muted"]
    border = tokens["--osmos-border"]
    grid = tokens["--osmos-chart-grid"]

    layout = {
        "template": "plotly_white" if normalized == "Light" else "plotly_dark",
        "paper_bgcolor": bg,
        "plot_bgcolor": soft_bg,
        "font": {"color": text, "family": "Plus Jakarta Sans, Segoe UI, sans-serif", "size": 12},
        "title": {"font": {"color": text, "size": 15}},
        "legend": {
            "font": {"color": muted},
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": border,
            "borderwidth": 0,
        },
        "xaxis": {
            "gridcolor": grid,
            "linecolor": border,
            "zerolinecolor": border,
            "tickfont": {"color": muted},
            "title": {"font": {"color": muted}},
        },
        "yaxis": {
            "gridcolor": grid,
            "linecolor": border,
            "zerolinecolor": border,
            "tickfont": {"color": muted},
            "title": {"font": {"color": muted}},
        },
        "colorway": OSMOS_CHART_COLORS,
    }
    if height is not None:
        layout["height"] = height
    if showlegend is not None:
        layout["showlegend"] = showlegend
    if margin is not None:
        layout["margin"] = margin

    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=True, gridcolor=grid, linecolor=border, tickfont={"color": muted})
    fig.update_yaxes(showgrid=True, gridcolor=grid, linecolor=border, tickfont={"color": muted})

    if hasattr(fig.layout, "scene"):
        fig.update_layout(
            scene={
                "bgcolor": soft_bg,
                "xaxis": {"gridcolor": grid, "linecolor": border, "zerolinecolor": border, "color": muted},
                "yaxis": {"gridcolor": grid, "linecolor": border, "zerolinecolor": border, "color": muted},
                "zaxis": {"gridcolor": grid, "linecolor": border, "zerolinecolor": border, "color": muted},
            }
        )

    return fig
