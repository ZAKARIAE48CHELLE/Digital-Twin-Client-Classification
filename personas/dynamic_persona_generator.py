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

# ── 1. DETERMINISTIC HELPER FUNCTIONS ──────────────────────────────────────────

def get_value_level(avg_clv):
    """
    Returns deterministic value level label based on CLV thresholds:
    - >= 8000 MAD: High-Value
    - 1500 to < 8000 MAD: Medium-Value
    - 0 to < 1500 MAD: Low-Value
    - <= 0 or missing: No Current Value / Value Collapse
    """
    if avg_clv is None:
        return "No Current Value / Value Collapse"
    try:
        val = float(avg_clv)
    except (ValueError, TypeError):
        return "No Current Value / Value Collapse"

    if val >= 8000.0:
        return "High-Value"
    elif val >= 1500.0:
        return "Medium-Value"
    elif val > 0.0:
        return "Low-Value"
    else:
        return "No Current Value / Value Collapse"


def get_engagement_level(avg_rfm, avg_engagement=None):
    """
    Returns deterministic engagement level based on RFM-ES and behavioral engagement:
    Combines average of RFM and engagement score if avg_engagement is normalized in [0, 1].
    Thresholds:
    - >= 0.70: High engagement
    - 0.45 to < 0.70: Moderate engagement
    - 0.20 to < 0.45: Low engagement
    - < 0.20: Very low engagement
    """
    rfm_val = float(avg_rfm) if avg_rfm is not None else 0.5
    if avg_engagement is not None:
        try:
            eng_val = float(avg_engagement)
            if 0.0 <= eng_val <= 1.0:
                score = (rfm_val + eng_val) / 2.0
            else:
                score = rfm_val
        except (ValueError, TypeError):
            score = rfm_val
    else:
        score = rfm_val

    if score >= 0.70:
        return "High engagement"
    elif score >= 0.45:
        return "Moderate engagement"
    elif score >= 0.20:
        return "Low engagement"
    else:
        return "Very low engagement"


def get_risk_level(avg_churn_risk):
    """
    Returns deterministic churn risk level:
    - >= 0.70: High risk
    - 0.40 to < 0.70: Medium risk
    - < 0.40: Low risk
    """
    risk_val = float(avg_churn_risk) if avg_churn_risk is not None else 0.2
    if risk_val >= 0.70:
        return "High risk"
    elif risk_val >= 0.40:
        return "Medium risk"
    else:
        return "Low risk"


def is_outlier_cluster(entity_count, total_entities, avg_clv=0):
    """
    Detects micro-clusters or statistical outlier groups.
    Condition: entity_count <= 2 OR (total_entities > 0 and percentage < 1.0%)
    """
    if entity_count <= 2:
        return True
    if total_entities and total_entities > 0:
        pct = (entity_count / total_entities) * 100.0
        if pct < 1.0:
            return True
    return False


def get_cluster_reliability_label(entity_count, total_entities):
    """
    Returns operational interpretation reliability label:
    - Micro-cluster / Outlier: entity_count <= 2 or pct < 1.0%
    - Small cluster: entity_count < 15 or pct < 5.0%
    - Stable cluster: otherwise
    """
    pct = (entity_count / total_entities * 100.0) if (total_entities and total_entities > 0) else 0.0
    if entity_count <= 2 or pct < 1.0:
        return "Micro-cluster / Outlier"
    elif entity_count < 15 or pct < 5.0:
        return "Small cluster"
    else:
        return "Stable cluster"


def get_priority_reason(cluster_summary):
    """
    Generates a clear plain language justification for the assigned decision priority.
    """
    count = cluster_summary.get("count", 0)
    total = cluster_summary.get("total_dataset_count", 0)
    clv = cluster_summary.get("avg_clv", 0.0)
    churn = cluster_summary.get("avg_churn_risk", 0.0)
    conv = cluster_summary.get("avg_conversion_prob", 0.0)
    complaints = cluster_summary.get("avg_complaints", 0.0)
    seg = cluster_summary.get("dominant_segment", "")
    ent_type = cluster_summary.get("dominant_entity_type", "Client")
    
    is_outlier = is_outlier_cluster(count, total, clv)
    priority = generate_dynamic_persona_priority(cluster_summary)

    if priority == "High":
        if is_outlier and clv >= 8000:
            return f"High priority because this micro-cluster ({count} entity) exhibits extremely high CLV (~{clv:,.0f} MAD), making it a top-tier exceptional VIP case."
        elif churn >= 0.70:
            return f"High priority due to elevated churn risk ({churn:.2f}), requiring urgent retention or service recovery."
        elif clv >= 8000:
            return f"High priority because this cluster combines high CLV (~{clv:,.0f} MAD) with low/medium churn risk, making it suitable for VIP retention and upsell."
        elif seg == "Complaint-Driven Risk Clients" or complaints >= 0.5:
            return "High priority because complaint signals indicate immediate dissatisfaction requiring support escalation."
        elif ent_type == "Prospect" and conv >= 0.70:
            return f"High priority because prospect conversion probability is very high ({conv:.0%}), making immediate outreach highly profitable."
        else:
            return "High priority due to key risk or value indicators requiring active attention."

    elif priority == "Medium":
        if 1500 <= clv < 8000:
            return f"Medium priority because the cluster has moderate value (~{clv:,.0f} MAD) with manageable risk."
        elif ent_type == "Prospect" and conv >= 0.40:
            return f"Medium priority because prospects show warm conversion probability ({conv:.0%})."
        else:
            return f"Medium priority because the cluster has moderate engagement but limited value (~{clv:,.0f} MAD) and low immediate churn risk."

    else: # Low
        if clv < 1500 and churn < 0.40:
            return f"Low priority because the cluster has low value (~{clv:,.0f} MAD) and low risk ({churn:.2f}), so automated nurturing is sufficient."
        else:
            return "Low priority due to low economic value and minimal churn risk."


# ── 2. SUMMARY & NAMING LOGIC ──────────────────────────────────────────────────

def summarize_cluster_profile(cluster_df, cluster_id, total_dataset_count=None):
    """
    Computes a statistical summary profile for a single cluster DataFrame.
    Gracefully handles missing or NaN columns.
    """
    count = len(cluster_df)
    total_cnt = total_dataset_count if total_dataset_count and total_dataset_count > 0 else count
    pct = (count / total_cnt) * 100.0 if total_cnt > 0 else 0.0

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

    avg_clv = _mean_val(cluster_df, "predicted_clv_amount_mad", _mean_val(cluster_df, "predicted_clv_score", 0.0))
    avg_rfm = _mean_val(cluster_df, "rfm_score", 0.5)
    avg_eng = _mean_val(cluster_df, "behavioral_engagement_score", _mean_val(cluster_df, "initial_interest_score", 0.5))
    avg_churn = _mean_val(cluster_df, "churn_risk_score", 0.2)

    val_level = get_value_level(avg_clv)
    eng_level = get_engagement_level(avg_rfm, avg_eng)
    risk_level = get_risk_level(avg_churn)
    is_outlier = is_outlier_cluster(count, total_cnt, avg_clv)
    rel_label = get_cluster_reliability_label(count, total_cnt)

    summary = {
        "cluster_id": cluster_id,
        "count": count,
        "total_dataset_count": total_cnt,
        "percentage": round(pct, 1),
        "dominant_entity_type": _mode_val(cluster_df, "entity_type", "Client"),
        "dominant_dynamic_class": _mode_val(cluster_df, "dynamic_class", "Prospect / Regular"),
        "dominant_segment": _mode_val(cluster_df, "customer_segment", "Standard Cohort"),
        "dominant_channel": _mode_val(cluster_df, "preferred_channel", _mode_val(cluster_df, "source_channel", "Email")),
        "dominant_category": _mode_val(cluster_df, "preferred_category", "General"),
        "dominant_device": _mode_val(cluster_df, "preferred_device", "Mobile"),
        
        "avg_clv": avg_clv,
        "avg_rfm": avg_rfm,
        "avg_engagement": avg_eng,
        "avg_churn_risk": avg_churn,
        "avg_conversion_prob": _mean_val(cluster_df, "conversion_probability", 0.5),
        "avg_purchases_90d": _mean_val(cluster_df, "purchases_90d", _mean_val(cluster_df, "initial_purchase_count", 0.0)),
        "avg_total_spent_90d": _mean_val(cluster_df, "total_spent_90d_mad", _mean_val(cluster_df, "initial_total_spent_mad", 0.0)),
        "avg_complaints": _mean_val(cluster_df, "complaint_count_90d", 0.0),
        "avg_sentiment": _mean_val(cluster_df, "review_score_avg", _mean_val(cluster_df, "social_sentiment_avg", 3.5)),
        "avg_recency_days": _mean_val(cluster_df, "recency_days", 30.0),

        "value_level": val_level,
        "engagement_level": eng_level,
        "risk_level": risk_level,
        "is_outlier": is_outlier,
        "reliability_label": rel_label
    }
    return summary


def assign_dynamic_persona_name(summary):
    """
    Generates a readable, business-friendly dynamic persona title based on cluster statistics.
    Includes micro-cluster / outlier detection and ensures cluster number traceability.
    """
    c_id = summary["cluster_id"]
    count = summary.get("count", 0)
    total = summary.get("total_dataset_count", 0)
    clv = summary.get("avg_clv", 0.0)
    rfm = summary.get("avg_rfm", 0.0)
    churn = summary.get("avg_churn_risk", 0.0)
    conv = summary.get("avg_conversion_prob", 0.0)
    complaints = summary.get("avg_complaints", 0.0)
    sentiment = summary.get("avg_sentiment", 3.5)
    ent_type = str(summary.get("dominant_entity_type", "")).capitalize()
    seg = summary.get("dominant_segment", "")

    is_outlier = is_outlier_cluster(count, total, clv)

    # 1. Micro-Cluster / Outlier Naming Logic
    if is_outlier:
        if clv >= 8000.0 and churn < 0.40:
            label = "Exceptional VIP Outlier"
        elif churn >= 0.70:
            label = "High-Risk Micro-Cluster"
        elif clv < 1500.0 and rfm < 0.45:
            label = "Dormant Micro-Cluster"
        else:
            label = "Exploratory Micro-Cluster"
    # 2. Prospect Naming Logic
    elif ent_type == "Prospect" or "prospect" in str(summary.get("dominant_dynamic_class", "")).lower():
        if conv >= 0.70:
            label = "Dynamic Hot Prospects"
        elif rfm < 0.45 or conv < 0.40:
            label = "Dynamic Cold Explorers"
        else:
            label = "Dynamic Prospect Segment"
    # 3. Client Naming Logic
    else:
        if clv >= 8000.0 and rfm >= 0.70 and churn < 0.40:
            label = "Dynamic VIP Loyalists"
        elif clv >= 8000.0 and churn >= 0.40:
            label = "Dynamic At-Risk High-Value Clients"
        elif clv < 1500.0 and churn >= 0.70:
            label = "Dynamic Churn Risk Customers"
        elif seg == "Complaint-Driven Risk Clients" or complaints >= 0.5:
            label = "Dynamic Frustrated Customers"
        elif sentiment >= 0.75 and rfm >= 0.70:
            label = "Dynamic Brand Advocates"
        elif 1500.0 <= clv < 8000.0 and rfm >= 0.45 and churn < 0.70:
            label = "Dynamic Regular Buyers"
        elif clv < 1500.0 and rfm < 0.45:
            label = "Dynamic Dormant Low-Value Customers"
        elif clv < 1500.0 and rfm >= 0.45 and churn < 0.40:
            label = "Dynamic Low-Value Active Buyers"
        elif churn >= 0.70:
            label = "Dynamic Churn Risk Customers"
        elif clv >= 8000.0:
            label = "Dynamic VIP Loyalists"
        else:
            label = "Dynamic Regular Buyers"

    return f"Cluster {c_id} — {label}"


def generate_dynamic_persona_description(summary):
    """
    Generates a deterministic business description summarizing the cluster's characteristics.
    Guarantees consistency between numerical thresholds and text descriptors.
    Mentions: value level, entity type, segment/class, engagement level, avg RFM, avg CLV, risk level, churn risk.
    """
    clv = summary.get("avg_clv", 0.0)
    rfm = summary.get("avg_rfm", 0.0)
    churn = summary.get("avg_churn_risk", 0.0)
    eng = summary.get("avg_engagement", 0.0)
    count = summary.get("count", 0)
    total = summary.get("total_dataset_count", 0)
    ent_type = summary.get("dominant_entity_type", "Client")
    segment = summary.get("dominant_segment", "Standard Cohort")
    d_class = summary.get("dominant_dynamic_class", "Active")

    val_level = summary.get("value_level") or get_value_level(clv)
    eng_level = summary.get("engagement_level") or get_engagement_level(rfm, eng)
    risk_level = summary.get("risk_level") or get_risk_level(churn)
    is_outlier = summary.get("is_outlier") if "is_outlier" in summary else is_outlier_cluster(count, total, clv)

    if is_outlier:
        return (
            f"This micro-cluster contains only {count} entity, making it an outlier rather than a stable customer persona. "
            f"It exhibits {eng_level.lower()} (avg. RFM-ES: {rfm:.2f}), {val_level.lower()} predicted CLV of ~{clv:,.0f} MAD, "
            f"and {risk_level.lower()} (churn risk: {churn:.2f}). It should be interpreted carefully as a special case."
        )

    if val_level == "Low-Value" and churn < 0.40:
        context_str = "It is suitable for automated nurturing rather than high-priority manual intervention."
    elif val_level == "High-Value" and churn < 0.40:
        context_str = "It represents a key revenue driver suitable for VIP retention and upsell."
    elif churn >= 0.70:
        context_str = "It requires immediate retention focus to prevent customer churn."
    else:
        context_str = "It represents a stable cohort benefiting from ongoing engagement."

    return (
        f"This cluster represents a {val_level} {ent_type.lower()} cohort dominated by '{segment}' ({d_class}). "
        f"It exhibits {eng_level.lower()} (avg. RFM-ES: {rfm:.2f}), predicted CLV of ~{clv:,.0f} MAD, "
        f"and {risk_level.lower()} (churn risk: {churn:.2f}). {context_str}"
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
    count = summary.get("count", 0)
    total = summary.get("total_dataset_count", 0)
    ent_type = summary.get("dominant_entity_type", "Client")

    is_outlier = is_outlier_cluster(count, total, clv)

    if is_outlier:
        if clv >= 8000.0:
            return "Perform manual account review and assign a dedicated relationship manager for direct outreach."
        elif churn >= 0.70:
            return "Perform manual review and route to priority support desk for immediate retention assessment."
        else:
            return "Monitor entity activity; treat as an isolated exploratory case rather than a broad cohort."

    if ent_type == "Prospect":
        if conv >= 0.70:
            return "Send conversion-focused offer and product reminder with a limited-time incentive."
        else:
            return "Use brand awareness content, educational emails, and low-pressure retargeting."

    if complaints >= 0.5 or summary.get("dominant_segment") == "Complaint-Driven Risk Clients":
        return "Prioritize complaint resolution, direct support phone call, and goodwill credit."

    if clv >= 8000.0 and churn >= 0.40:
        return "Trigger immediate retention campaign, dedicated account manager call, and custom discount."
    elif clv >= 8000.0 and churn < 0.40:
        return "Offer VIP loyalty perks, early access to new collections, and premium cross-sell items."
    elif churn >= 0.70:
        return "Send win-back reactivation campaign with exclusive return incentive."
    elif 1500.0 <= clv < 8000.0:
        return "Maintain steady engagement with personalized recommendations and cross-category offers."
    else:
        return "Apply low-cost automated nurturing and campaign sequences to maintain brand awareness."


def generate_dynamic_persona_channel(summary):
    """
    Generates recommended channel based on cluster profile.
    """
    clv = summary.get("avg_clv", 0.0)
    churn = summary.get("avg_churn_risk", 0.0)
    complaints = summary.get("avg_complaints", 0.0)
    conv = summary.get("avg_conversion_prob", 0.0)
    count = summary.get("count", 0)
    total = summary.get("total_dataset_count", 0)
    ent_type = summary.get("dominant_entity_type", "Client")

    is_outlier = is_outlier_cluster(count, total, clv)

    if is_outlier:
        if clv >= 8000.0:
            return "Manual Review / Direct Outreach"
        elif churn >= 0.70:
            return "Manual Review / Priority Support"
        else:
            return "Manual Review / Automated Monitoring"

    if complaints >= 0.5 or summary.get("dominant_segment") == "Complaint-Driven Risk Clients":
        return "Direct Phone / Priority Desk"
    elif clv >= 8000.0 and churn >= 0.40:
        return "Direct Phone / Priority Support"
    elif clv >= 8000.0:
        return "VIP Email / Direct Outreach"
    elif ent_type == "Prospect" and conv >= 0.70:
        return "Email / Retargeting"
    elif ent_type == "Prospect":
        return "Web Popup / Awareness Email"
    elif 1500.0 <= clv < 8000.0:
        return "Email / App Notification"
    elif clv < 1500.0 and churn < 0.40:
        return "Automated Email"
    else:
        return "Email / In-App Message"


def generate_dynamic_persona_priority(summary):
    """
    Generates decision priority level (High, Medium, Low) based on explicit rules:
    High priority only when there is a strong reason (high risk >=0.70, high CLV >=8000, hot prospects >=0.70, or active complaints).
    """
    clv = summary.get("avg_clv", 0.0)
    churn = summary.get("avg_churn_risk", 0.0)
    conv = summary.get("avg_conversion_prob", 0.0)
    complaints = summary.get("avg_complaints", 0.0)
    seg = summary.get("dominant_segment", "")
    ent_type = summary.get("dominant_entity_type", "Client")
    rfm = summary.get("avg_rfm", 0.5)

    # High Priority Conditions
    if (churn >= 0.70 or
        clv >= 8000.0 or
        (seg == "Complaint-Driven Risk Clients" and churn >= 0.40) or
        complaints >= 0.5 or
        (ent_type == "Prospect" and conv >= 0.70)):
        return "High"

    # Medium Priority Conditions
    if (1500.0 <= clv < 8000.0 or
        (rfm >= 0.45 and churn < 0.40) or
        (ent_type == "Prospect" and conv >= 0.40) or
        churn >= 0.40):
        return "Medium"

    # Low Priority Fallback
    return "Low"


# ── 3. MAIN DYNAMIC PERSONA GENERATION ─────────────────────────────────────────

def generate_dynamic_personas(df, cluster_col="ml_cluster_id"):
    """
    Main entry point function.
    Summarizes each cluster in df and returns a list of dynamic persona dictionaries.
    Handles duplicate persona names with descriptive qualifiers.
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

    # First pass: build summaries and initial names
    raw_personas = []
    name_counts = {}

    for c_id in unique_clusters:
        c_df = valid_df[valid_df[target_col] == c_id]
        summary = summarize_cluster_profile(c_df, c_id, total_dataset_count=total_dataset_cnt)
        
        base_name = assign_dynamic_persona_name(summary)
        parts = base_name.split(" — ")
        label_part = parts[1] if len(parts) > 1 else base_name
        
        name_counts[label_part] = name_counts.get(label_part, 0) + 1
        raw_personas.append((c_id, summary, base_name, label_part))

    # Second pass: disambiguate duplicate persona labels if any
    seen_labels = {}
    dynamic_personas = []

    for c_id, summary, base_name, label_part in raw_personas:
        if name_counts[label_part] > 1:
            idx = seen_labels.get(label_part, 0) + 1
            seen_labels[label_part] = idx
            
            if summary.get("is_outlier"):
                qualifier = "Micro-Cluster Outlier"
            elif summary.get("avg_churn_risk", 0) < 0.40:
                qualifier = "Low-Risk Cohort" if idx == 1 else "Core Group"
            elif summary.get("avg_churn_risk", 0) >= 0.70:
                qualifier = "High-Risk Cohort"
            elif summary.get("avg_clv", 0) >= 8000:
                qualifier = "Premium Cohort"
            else:
                qualifier = f"Group {idx}"

            final_name = f"Cluster {c_id} — {label_part} ({qualifier})"
        else:
            final_name = base_name

        desc = generate_dynamic_persona_description(summary)
        action = generate_dynamic_persona_recommended_action(summary)
        channel = generate_dynamic_persona_channel(summary)
        priority = generate_dynamic_persona_priority(summary)
        prio_reason = get_priority_reason(summary)

        persona_dict = {
            "cluster_id": c_id,
            "persona_name": final_name,
            "entity_count": summary["count"],
            "total_dataset_count": summary["total_dataset_count"],
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
            "value_level": summary["value_level"],
            "engagement_level": summary["engagement_level"],
            "risk_level": summary["risk_level"],
            "is_outlier": summary["is_outlier"],
            "reliability_label": summary["reliability_label"],
            "description": desc,
            "recommended_action": action,
            "recommended_channel": channel,
            "priority_level": priority,
            "priority_reason": prio_reason
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
        prio_reason = p.get("priority_reason", "")
        chan = p["recommended_channel"]
        is_outlier = p.get("is_outlier", False)
        rel_label = p.get("reliability_label", "Stable cluster")
        val_level = p.get("value_level", "Medium-Value")
        eng_level = p.get("engagement_level", "Moderate engagement")
        risk_level = p.get("risk_level", "Low risk")
        
        prio_color = "#f87171" if prio == "High" else ("#facc15" if prio == "Medium" else "#34d399")
        
        warning_badge = "<span style='background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 11px; margin-left: 8px;'>⚠️ Micro-cluster: interpret carefully</span>" if is_outlier else f"<span style='background: rgba(56, 189, 248, 0.12); color: #38bdf8; padding: 3px 8px; border-radius: 6px; font-size: 11px; margin-left: 8px;'>ℹ️ {rel_label}</span>"

        card_html = f"""<div style='background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9)); border: 1.5px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 18px; margin-bottom: 14px;'>
<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
<div>
<span style='font-size: 18px; font-weight: 700; color: #38bdf8;'>⚡ {p_name}</span>
<span style='font-size: 12px; color: #94a3b8; margin-left: 8px;'>(Cluster ID: {c_id} | {cnt} entities, {pct}%)</span>
{warning_badge}
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
<div style='font-size: 12px; font-weight: 700; color: #38bdf8;'>{p["avg_clv"]:,.0f} MAD <span style='font-size:10px; color:#94a3b8;'>({val_level})</span></div>
</div>
<div style='background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px;'>
<span style='font-size: 10px; color: #94a3b8; text-transform: uppercase;'>Avg RFM-ES</span>
<div style='font-size: 12px; font-weight: 700; color: #818cf8;'>{p["avg_rfm"]:.2f} <span style='font-size:10px; color:#94a3b8;'>({eng_level})</span></div>
</div>
<div style='background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px;'>
<span style='font-size: 10px; color: #94a3b8; text-transform: uppercase;'>Avg Churn Risk</span>
<div style='font-size: 12px; font-weight: 700; color: #f87171;'>{p["avg_churn_risk"]:.2f} <span style='font-size:10px; color:#94a3b8;'>({risk_level})</span></div>
</div>
</div>
<div style='background: rgba(129, 140, 248, 0.08); padding: 8px 12px; border-radius: 8px; border-left: 3.5px solid #818cf8; margin-bottom: 8px;'>
<strong style='color: #a78bfa; font-size: 11px;'>🎯 Priority Rationale</strong>
<p style='font-size: 11.5px; color: #e2e8f0; margin: 2px 0 0 0;'>{prio_reason}</p>
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
