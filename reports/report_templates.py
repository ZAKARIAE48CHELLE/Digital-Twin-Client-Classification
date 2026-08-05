"""
OSMOS Executive Report Generator — Section Templates (Phase 8.6)
================================================================
Markdown and HTML section renderers for executive reports.
"""

from typing import Any, Dict, List
import pandas as pd
from reports.report_schemas import ReportContext


def safe_float(val: Any, default: float = 0.0) -> float:
    """Safely converts value to float with default fallback for None/invalid types."""
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def render_report_title_page(ctx: ReportContext) -> str:
    """Renders report header & title metadata block."""
    ent_str = f" | Entity ID: `{ctx.entity_id}`" if ctx.entity_id else ""
    run_str = f" | Run ID: `#{ctx.run_id}`" if ctx.run_id else ""

    return f"""# 🛡️ OSMOS EXECUTIVE REPORT
### {ctx.report_type.upper()}{ent_str}{run_str}

**Generated At:** `{ctx.generated_at[:19]} UTC`  
**Storage Mode:** `{ctx.storage_mode.upper()}`  
**Confidentiality Notice:** *This report is generated from OSMOS internal analytical modules and multi-agent supervision layers for human-in-the-loop decision support.*

---
"""


def render_executive_summary(ctx: ReportContext) -> str:
    """Renders high-level executive summary callout block."""
    scores = ctx.latest_scores
    churn = safe_float(scores.get("churn_risk_score"), 0.0)
    clv = safe_float(scores.get("predicted_clv_mad"), 0.0)

    risk_label = f"High Churn Risk ({churn * 100:.1f}%)" if churn >= 0.50 else "Low Churn Friction"
    opp_label = f"High Monetary Potential ({clv:,.2f} MAD)" if clv >= 3000.0 else "Standard Engagement"

    return f"""## 📊 1. Executive Summary

| Metric / Dimension | Observation |
| :--- | :--- |
| **Primary Status** | `{ctx.final_recommendation[:120]}` |
| **Identified Risk** | {risk_label} |
| **Expansion Opportunity** | {opp_label} |
| **Recommended Next Best Action** | **{ctx.next_best_action}** |
| **Human Approval Required** | **YES (Pending Administrative Review)** |

---
"""


def render_digital_twin_section(ctx: ReportContext) -> str:
    """Renders Digital Twin profile state and demographics table."""
    dt = ctx.digital_twin_state
    if not dt:
        return "## 👤 2. Digital Twin State Profile\n\n*No active Digital Twin snapshot recorded for this entity.*\n\n---\n"

    return f"""## 👤 2. Digital Twin State Profile

| Attribute | Value | Attribute | Value |
| :--- | :--- | :--- | :--- |
| **Entity Type** | `{dt.get('entity_type', 'Client')}` | **Region** | {dt.get('region', 'N/A')} |
| **Source Channel** | {dt.get('source_channel', 'Direct')} | **Preferred Device** | {dt.get('preferred_device', 'Desktop')} |
| **Category Interest** | {dt.get('preferred_category', 'General')} | **Age Group** | {dt.get('age_group', '30-45')} |
| **Marketing Consent** | `{dt.get('marketing_consent', True)}` | **Price Sensitivity** | {safe_float(dt.get('price_sensitivity'), 0.5):.2f} |

---
"""


def render_scores_section(ctx: ReportContext) -> str:
    """Renders ML, CLV, RFM-ES, and Churn Risk score breakdown."""
    s = ctx.latest_scores
    if not s:
        return "## 📈 3. ML & Analytical Metrics\n\n*No ML scores recorded.*\n\n---\n"

    return f"""## 📈 3. ML & Analytical Metrics

- **Predicted CLV Amount:** `{safe_float(s.get('predicted_clv_mad'), 0.0):,.2f} MAD`
- **CLV Segment:** `{s.get('clv_segment', 'Unknown')}` (Score: `{safe_float(s.get('clv_score'), 0.0):.1f}/100`)
- **RFM Score:** `{safe_float(s.get('rfm_score'), 0.0):.3f}` (Recency: `{safe_float(s.get('recency_days'), 0.0):.0f} days`, Freq: `{safe_float(s.get('frequency'), 0.0):.0f}`, Monetary: `{safe_float(s.get('monetary_mad'), 0.0):,.2f} MAD`)
- **Churn Risk Probability:** `{safe_float(s.get('churn_risk_score'), 0.0) * 100:.1f}%`

---
"""


def render_persona_section(ctx: ReportContext) -> str:
    """Renders stable vs dynamic persona classification details."""
    s = ctx.latest_scores
    return f"""## 🎭 4. Customer Cohort & Persona Classification

- **Official Customer Segment:** `{s.get('customer_segment', 'Unknown')}`
- **Official Stable Persona:** `{s.get('persona_name', 'Unknown')}`
> ℹ️ *Note: Stable personas represent official segment-first representations. Dynamic personas represent exploratory behavioral hypotheses.*

---
"""


def render_agent_supervision_section(ctx: ReportContext) -> str:
    """Renders multi-agent supervision outputs and risks/opportunities."""
    outputs = ctx.agent_outputs
    if not outputs:
        return "## 🤖 5. Multi-Agent Supervision Analysis\n\n*No agent supervision runs logged for this context.*\n\n---\n"

    lines = ["## 🤖 5. Multi-Agent Supervision Analysis\n"]
    for out in outputs:
        status_icon = "🟢" if out.get("status") == "OK" else "🟡" if out.get("status") == "Warning" else "🔴"
        lines.append(f"### {status_icon} {out.get('agent_name')} (`{out.get('agent_id')}`)")
        lines.append(f"**Summary:** {out.get('summary')}\n")

        risks = out.get("risks", [])
        if risks:
            lines.append("**Identified Risks:**")
            for r in risks:
                lines.append(f"- ⚠️ {r}")

        recs = out.get("recommendations", [])
        if recs:
            lines.append("**Recommended Actions:**")
            for r in recs:
                lines.append(f"- 💡 {r}")
        lines.append("")

    lines.append("---\n")
    return "\n".join(lines)


def render_debate_consensus_section(ctx: ReportContext) -> str:
    """Renders Agent Collaboration & Debate consensus decisions and conflicts."""
    deb = ctx.debate_output
    if not deb:
        return "## 🤝 6. Agent Collaboration & Debate Consensus\n\n*Debate mode was not active for this run.*\n\n---\n"

    consensus = deb.get("consensus", {})
    conflicts = deb.get("conflicts", [])

    lines = ["## 🤝 6. Agent Collaboration & Debate Consensus\n"]
    lines.append(f"- **Consensus Status:** `{consensus.get('consensus_status', 'N/A')}`")
    lines.append(f"- **Debate Confidence:** `{float(consensus.get('confidence_score', 0.85)) * 100:.0f}%`")
    lines.append(f"- **Reasoning Summary:** {consensus.get('reasoning_summary', 'N/A')}")
    lines.append(f"- **Synthesized Priority Action:** **{consensus.get('priority_action', ctx.next_best_action)}**\n")

    if conflicts:
        lines.append("### Identified Cross-Agent Conflicts & Resolutions:")
        for c in conflicts:
            lines.append(f"- **{c.get('conflict_type')}** ({c.get('severity')} Severity): {c.get('description')}")
            lines.append(f"  *Resolution Suggestion:* {c.get('resolution_suggestion')}")

    lines.append("\n---\n")
    return "\n".join(lines)


def render_approval_history_section(ctx: ReportContext) -> str:
    """Renders historical administrative approval queue items."""
    appr = ctx.approval_history
    if not appr:
        return "## 📋 7. Human Approval Queue History\n\n*No approval queue records linked to this context.*\n\n---\n"

    lines = ["## 📋 7. Human Approval Queue History\n"]
    lines.append("| Item ID | Action Title | Status | Source Agent | Priority | Date |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

    for a in appr[:10]:
        lines.append(
            f"| `#{a.get('approval_id')}` | {a.get('proposed_action_title', '')[:35]} | `{a.get('status')}` | {a.get('source_agent')} | {a.get('priority')} | `{str(a.get('created_at'))[:10]}` |"
        )

    lines.append("\n---\n")
    return "\n".join(lines)


def render_knowledge_evidence_section(ctx: ReportContext) -> str:
    """Renders retrieved knowledge base documentation snippets and system rules."""
    k_items = ctx.knowledge_evidence
    if not k_items:
        return "## 📖 8. Knowledge Base Evidence & System Rules\n\n*No external knowledge snippets retrieved for this context.*\n\n---\n"

    lines = ["## 📖 8. Knowledge Base Evidence & System Rules\n"]
    for k in k_items[:4]:
        lines.append(f"#### 📜 {k.get('source_name', 'Doc')} — `{k.get('section_name', 'Section')}`")
        lines.append(f"> *{k.get('chunk_text', '')[:300]}...*\n")

    lines.append("---\n")
    return "\n".join(lines)


def render_final_recommendation_section(ctx: ReportContext) -> str:
    """Renders final next best action callout block."""
    return f"""## 🎯 9. Final Strategic Recommendation

```text
FINAL RECOMMENDED NEXT BEST ACTION:
{ctx.next_best_action}
```

- **Action Implementation Status:** Pending Administrative Approval in Human Approval Queue.
- **Closed-Loop Campaign Conversion:** Ready to convert into a simulated campaign draft upon admin approval.

---
"""
