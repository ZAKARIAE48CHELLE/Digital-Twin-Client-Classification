"""
OSMOS Dynamic Persona Generator Module.

Generates data-driven, temporary dynamic persona profiles based on clustering outputs (KMeans clusters 2-9).
Crucially, these dynamic personas are exploratory and do NOT alter or overwrite the official 9 fixed
persona blueprints in persona_library.py or Digital Twin persona resolution.
"""
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("OSMOS_DYNAMIC_PERSONAS")

def summarize_cluster_profile(cluster_df, cluster_id, total_dataset_count=None):
    """
    Computes a statistical summary profile for a single cluster DataFrame.
    Gracefully handles missing or NaN columns.
    """
    count = len(cluster_df)
    if total_dataset_count and total_dataset_count > 0:
        pct = (count / total_dataset_count) * 100.0
    else:
        pct = 0.0

    def _mode_val(df, col_name, default="N/A"):
        if col_name in df.columns and not df[col_name].dropna().empty:
            mode_res = df[col_name].mode()
            if not mode_res.empty:
                return str(mode_res.iloc[0])
        return default

    def _mean_val(df, col_name, default=0.0):
        if col_name in df.columns:
            nums = pd.to_numeric(df[col_name], errors="coerce").dropna()
            if not nums.empty:
                return float(nums.mean())
        return default

    summary = {
        "cluster_id": cluster_id,
        "count": count,
        "percentage": round(pct, 1),
        "dominant_entity_type": _mode_val(cluster_df, "entity_type", "Client"),
        "dominant_dynamic_class": _mode_val(cluster_df, "dynamic_class", "Prospect / Regular"),
        "dominant_segment": _mode_val(cluster_df, "customer_segment", "Standard Cohort"),
        "dominant_channel": _mode_val(cluster_df, "preferred_channel", _mode_val(cluster_df, "source_channel", "Email")),
        "dominant_category": _mode_val(cluster_df, "preferred_category", "General"),
        "dominant_device": _mode_val(cluster_df, "preferred_device", "Mobile"),
        
        "avg_clv": _mean_val(cluster_df, "predicted_clv_amount_mad", _mean_val(cluster_df, "predicted_clv_score", 0.0)),
        "avg_rfm": _mean_val(cluster_df, "rfm_score", 0.5),
        "avg_engagement": _mean_val(cluster_df, "behavioral_engagement_score", _mean_val(cluster_df, "initial_interest_score", 0.5)),
        "avg_churn_risk": _mean_val(cluster_df, "churn_risk_score", 0.2),
        "avg_conversion_prob": _mean_val(cluster_df, "conversion_probability", 0.5),
        "avg_purchases_90d": _mean_val(cluster_df, "purchases_90d", _mean_val(cluster_df, "initial_purchase_count", 0.0)),
        "avg_total_spent_90d": _mean_val(cluster_df, "total_spent_90d_mad", _mean_val(cluster_df, "initial_total_spent_mad", 0.0)),
        "avg_complaints": _mean_val(cluster_df, "complaint_count_90d", 0.0),
        "avg_sentiment": _mean_val(cluster_df, "review_score_avg", _mean_val(cluster_df, "social_sentiment_avg", 3.5)),
        "avg_recency_days": _mean_val(cluster_df, "recency_days", 30.0)
    }
    return summary

def assign_dynamic_persona_name(summary):
    """
    Generates a readable, business-friendly dynamic persona title based on cluster statistics.
    Ensures cluster number traceability (e.g. 'Cluster 3 — Dynamic VIP Loyalists').
    """
    c_id = summary["cluster_id"]
    ent_type = str(summary.get("dominant_entity_type", "")).capitalize()
    clv = summary.get("avg_clv", 0.0)
    rfm = summary.get("avg_rfm", 0.0)
    churn = summary.get("avg_churn_risk", 0.0)
    eng = summary.get("avg_engagement", 0.0)
    conv = summary.get("avg_conversion_prob", 0.0)
    complaints = summary.get("avg_complaints", 0.0)
    sentiment = summary.get("avg_sentiment", 3.5)
    purchases = summary.get("avg_purchases_90d", 0.0)

    # Prospect Naming Logic
    if ent_type == "Prospect" or "prospect" in str(summary.get("dominant_dynamic_class", "")).lower():
        if conv >= 0.6 or eng >= 0.6:
            label = "Dynamic Hot Prospects"
        elif eng < 0.3 or churn >= 0.5:
            label = "Dynamic Cold Explorers"
        else:
            label = "Dynamic Prospect Segment"
    else: # Client Naming Logic
        if (clv >= 8000 or rfm >= 0.65) and churn < 0.35:
            label = "Dynamic VIP Loyalists"
        elif (clv >= 6000 or rfm >= 0.55) and churn >= 0.45:
            label = "Dynamic At-Risk High-Value Clients"
        elif complaints >= 0.5 or sentiment < 2.8:
            label = "Dynamic Frustrated Customers"
        elif eng >= 0.65 and sentiment >= 4.0:
            label = "Dynamic Brand Advocates"
        elif purchases < 1.0 or summary.get("avg_recency_days", 0) > 90 or rfm < 0.35:
            label = "Dynamic Dormant Low-Value Customers"
        else:
            label = "Dynamic Regular Buyers"

    return f"Cluster {c_id} — {label}"

def generate_dynamic_persona_description(summary):
    """
    Generates a deterministic business description summarizing the cluster's characteristics.
    """
    clv = summary.get("avg_clv", 0.0)
    rfm = summary.get("avg_rfm", 0.0)
    churn = summary.get("avg_churn_risk", 0.0)
    eng = summary.get("avg_engagement", 0.0)
    ent_type = summary.get("dominant_entity_type", "Client")
    segment = summary.get("dominant_segment", "Standard Cohort")
    d_class = summary.get("dominant_dynamic_class", "Active")

    val_str = "High-Value" if clv >= 7000 or rfm >= 0.6 else ("Medium-Value" if clv >= 3000 or rfm >= 0.4 else "Low-Value")
    eng_str = "Strong" if eng >= 0.6 else ("Moderate" if eng >= 0.3 else "Low")
    risk_str = "High Churn Risk" if churn >= 0.5 else ("Moderate Risk" if churn >= 0.25 else "Low Risk")

    return (
        f"This cluster represents a {val_str} {ent_type.lower()} cohort dominated by '{segment}' ({d_class}). "
        f"It exhibits {eng_str.lower()} behavioral engagement (avg. RFM: {rfm:.2f}), "
        f"predicted CLV of ~{clv:,.0f} MAD, and {risk_str.lower()} ({churn:.2f})."
    )

def generate_dynamic_persona_recommended_action(summary):
    """
    Generates deterministic marketing action advice for the dynamic persona.
    """
    clv = summary.get("avg_clv", 0.0)
    rfm = summary.get("avg_rfm", 0.0)
    churn = summary.get("avg_churn_risk", 0.0)
    conv = summary.get("avg_conversion_prob", 0.0)
    complaints = summary.get("avg_complaints", 0.0)
    ent_type = summary.get("dominant_entity_type", "Client")

    if ent_type == "Prospect":
        if conv >= 0.5:
            return "Send conversion-focused offer and product reminder with a limited-time incentive."
        else:
            return "Use brand awareness content, educational emails, and low-pressure retargeting."

    if complaints >= 0.5:
        return "Prioritize complaint resolution, direct support phone call, and goodwill credit."

    if (clv >= 7000 or rfm >= 0.65) and churn >= 0.45:
        return "Trigger immediate retention campaign, dedicated account manager call, and custom discount."
    elif (clv >= 7000 or rfm >= 0.65) and churn < 0.45:
        return "Offer VIP loyalty perks, early access to new collections, and premium cross-sell items."
    elif churn >= 0.5 or summary.get("avg_recency_days", 0) > 90:
        return "Send win-back reactivation campaign with exclusive return incentive."
    else:
        return "Maintain steady engagement with personalized recommendations and cross-category offers."

def generate_dynamic_persona_channel(summary):
    """
    Generates recommended channel based on cluster profile.
    """
    clv = summary.get("avg_clv", 0.0)
    churn = summary.get("avg_churn_risk", 0.0)
    complaints = summary.get("avg_complaints", 0.0)
    dominant_ch = summary.get("dominant_channel", "Email")

    if complaints >= 0.5 or (clv >= 8000 and churn >= 0.5):
        return "Direct Phone / Priority Desk"
    elif clv >= 8000:
        return "VIP Email / Direct Outreach"
    elif dominant_ch and dominant_ch != "N/A":
        return dominant_ch
    else:
        return "Email"

def generate_dynamic_persona_priority(summary):
    """
    Generates decision priority level (High, Medium, Low).
    """
    churn = summary.get("avg_churn_risk", 0.0)
    clv = summary.get("avg_clv", 0.0)
    complaints = summary.get("avg_complaints", 0.0)
    conv = summary.get("avg_conversion_prob", 0.0)

    if (clv >= 6000 and churn >= 0.4) or complaints >= 0.5 or conv >= 0.6:
        return "High"
    elif clv >= 4000 or churn >= 0.3:
        return "Medium"
    else:
        return "Low"

def generate_dynamic_personas(df, cluster_col="ml_cluster_id"):
    """
    Main entry point function.
    Summarizes each cluster in df and returns a list of dynamic persona dictionaries.
    """
    if df is None or df.empty:
        return []

    # If cluster_col is missing or invalid, try fallback column names
    target_col = cluster_col
    if target_col not in df.columns:
        for alt in ["cluster", "ml_cluster_label", "cluster_id"]:
            if alt in df.columns:
                target_col = alt
                break

    if target_col not in df.columns:
        logger.warning(f"Cluster column '{cluster_col}' not found in DataFrame.")
        return []

    valid_df = df[df[target_col].notna()].copy()
    if valid_df.empty:
        return []

    unique_clusters = sorted(valid_df[target_col].unique(), key=lambda x: str(x))
    total_dataset_cnt = len(valid_df)

    dynamic_personas = []
    for c_id in unique_clusters:
        c_df = valid_df[valid_df[target_col] == c_id]
        summary = summarize_cluster_profile(c_df, c_id, total_dataset_count=total_dataset_cnt)
        
        name = assign_dynamic_persona_name(summary)
        desc = generate_dynamic_persona_description(summary)
        action = generate_dynamic_persona_recommended_action(summary)
        channel = generate_dynamic_persona_channel(summary)
        priority = generate_dynamic_persona_priority(summary)

        persona_dict = {
            "cluster_id": c_id,
            "persona_name": name,
            "entity_count": summary["count"],
            "percentage": summary["percentage"],
            "dominant_entity_type": summary["dominant_entity_type"],
            "dominant_dynamic_class": summary["dominant_dynamic_class"],
            "dominant_segment": summary["dominant_segment"],
            "dominant_channel": summary["dominant_channel"],
            "avg_clv": summary["avg_clv"],
            "avg_rfm": summary["avg_rfm"],
            "avg_churn_risk": summary["avg_churn_risk"],
            "avg_engagement": summary["avg_engagement"],
            "avg_conversion_prob": summary["avg_conversion_prob"],
            "avg_purchases_90d": summary["avg_purchases_90d"],
            "avg_total_spent_90d": summary["avg_total_spent_90d"],
            "description": desc,
            "recommended_action": action,
            "recommended_channel": channel,
            "priority_level": priority
        }
        dynamic_personas.append(persona_dict)

    return dynamic_personas

def build_dynamic_persona_cards(dynamic_personas):
    """
    Renders visual Streamlit UI cards for a list of dynamic personas.
    Uses dedented HTML templates without blank lines to guarantee native DOM compilation.
    """
    import streamlit as st

    if not dynamic_personas:
        st.warning("No dynamic persona profiles available. Run clustering first.")
        return

    for p in dynamic_personas:
        p_name = p["persona_name"]
        c_id = p["cluster_id"]
        cnt = p["entity_count"]
        pct = p["percentage"]
        prio = p["priority_level"]
        chan = p["recommended_channel"]
        
        prio_color = "#f87171" if prio == "High" else ("#facc15" if prio == "Medium" else "#34d399")

        card_html = f"""<div style='background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9)); border: 1.5px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 18px; margin-bottom: 14px;'>
<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
<div>
<span style='font-size: 18px; font-weight: 700; color: #38bdf8;'>⚡ {p_name}</span>
<span style='font-size: 12px; color: #94a3b8; margin-left: 8px;'>(Cluster ID: {c_id} | {cnt} entities, {pct}%)</span>
</div>
<div>
<span style='background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 11px;'>Channel: {chan}</span>
<span style='background: rgba(255, 255, 255, 0.05); color: {prio_color}; border: 1px solid {prio_color}; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 11px; margin-left: 6px;'>Priority: {prio}</span>
</div>
</div>
<p style='color: #cbd5e1; font-size: 13px; margin-bottom: 12px;'>{p["description"]}</p>
<div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 12px;'>
<div style='background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px;'>
<span style='font-size: 10px; color: #94a3b8; text-transform: uppercase;'>Dominant Class</span>
<div style='font-size: 12px; font-weight: 700; color: #2dd4bf;'>{p["dominant_dynamic_class"]}</div>
</div>
<div style='background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px;'>
<span style='font-size: 10px; color: #94a3b8; text-transform: uppercase;'>Average CLV</span>
<div style='font-size: 12px; font-weight: 700; color: #38bdf8;'>{p["avg_clv"]:,.0f} MAD</div>
</div>
<div style='background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px;'>
<span style='font-size: 10px; color: #94a3b8; text-transform: uppercase;'>Avg RFM-ES</span>
<div style='font-size: 12px; font-weight: 700; color: #818cf8;'>{p["avg_rfm"]:.2f}</div>
</div>
<div style='background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px;'>
<span style='font-size: 10px; color: #94a3b8; text-transform: uppercase;'>Avg Churn Risk</span>
<div style='font-size: 12px; font-weight: 700; color: #f87171;'>{p["avg_churn_risk"]:.2f}</div>
</div>
</div>
<div style='background: rgba(56, 189, 248, 0.08); padding: 10px 14px; border-radius: 8px; border-left: 3.5px solid #38bdf8;'>
<strong style='color: #c084fc; font-size: 12px;'>🚀 Recommended Action</strong>
<p style='font-size: 12px; color: #f8fafc; margin: 2px 0 0 0;'>{p["recommended_action"]}</p>
</div>
</div>"""

        if hasattr(st, "html"):
            st.html(card_html)
        else:
            st.markdown(card_html, unsafe_allow_html=True)


def generate_dynamic_persona_with_llm(cluster_summary):
    """
    Optional LLM narrative synthesis for a single dynamic cluster summary.
    BUTTON-TRIGGERED ONLY. Zero PII sent.
    Returns enhanced persona dict or None if LLM is unavailable.
    """
    try:
        from llm.llm_client import generate_llm_response
        prompt = (
            f"You are a strategic marketing AI assistant. Analyze this customer cluster data and generate a JSON narrative:\n"
            f"Cluster ID: {cluster_summary.get('cluster_id')}\n"
            f"Entity Count: {cluster_summary.get('count')}\n"
            f"Dominant Type: {cluster_summary.get('dominant_entity_type')}\n"
            f"Dominant Segment: {cluster_summary.get('dominant_segment')}\n"
            f"Avg CLV: {cluster_summary.get('avg_clv'):.0f} MAD\n"
            f"Avg RFM: {cluster_summary.get('avg_rfm'):.2f}\n"
            f"Avg Churn Risk: {cluster_summary.get('avg_churn_risk'):.2f}\n"
            f"Return JSON with keys: persona_name, description, recommended_action."
        )
        resp = generate_llm_response(prompt)
        if resp:
            import json
            from llm.llm_json_utils import parse_llm_json
            parsed = parse_llm_json(resp)
            if parsed:
                return parsed
    except Exception as e:
        logger.debug(f"LLM dynamic persona synthesis skipped: {e}")
    return None
