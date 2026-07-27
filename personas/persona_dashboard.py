"""
OSMOS Persona Dashboard Component Module.

Renders:
1. Stable Persona Library (9 predefined official strategic personas used for official interpretation & Digital Twin resolution)
2. Dynamic Personas (data-driven profiles generated from clustering outputs, varying 2-9 clusters)
3. Comparison View (explaining Stable vs Dynamic persona roles)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from personas.persona_library import get_all_personas, seed_default_personas
from personas.dynamic_persona_generator import (
    generate_dynamic_personas,
    build_dynamic_persona_cards,
    generate_dynamic_persona_with_llm
)
from admin.database_metrics import is_postgres_available

def render_stable_persona_library():
    """Renders the official, fixed 9-persona strategic catalog."""
    st.markdown("<div class='section-header'><span class='icon'>🎭</span><span class='title'>OSMOS Official Stable Persona Library</span></div>", unsafe_allow_html=True)
    
    st.info(
        "ℹ️ **Stable Personas**: These 9 predefined strategic profiles are used for official marketing interpretation "
        "and Digital Twin persona resolution (`entity_id → Digital Twin → segment → persona`). They remain fixed regardless of ML cluster settings."
    )

    if not is_postgres_available():
        st.caption("PostgreSQL inactive — displaying default local persona blueprints.")
        
    col_act1, col_act2 = st.columns([1, 4])
    with col_act1:
        if st.button("🌱 Sync Default Personas", key="btn_seed_personas"):
            count = seed_default_personas()
            st.success(f"✅ Seeding complete: {count} personas synced!")
            st.rerun()
            
    personas = get_all_personas()
    if personas:
        p_df = pd.DataFrame(personas)
        
        # Display Columns
        cols = [
            "persona_id", "segment_name", "persona_name", "priority_level", 
            "preferred_channel", "recommended_action_fr", "description_fr", "is_active"
        ]
        available_cols = [c for c in cols if c in p_df.columns]
        
        st.dataframe(p_df[available_cols], width="stretch", hide_index=True)
        
        st.markdown("---")
        st.markdown("<p style='font-size:16px; font-weight:700;'>Persona Blueprint Card Inspector</p>", unsafe_allow_html=True)
        
        seg_list = p_df["segment_name"].unique()
        selected_seg = st.selectbox("Select Cohort Segment to view Persona Blueprint:", seg_list, key="sel_persona_card")
        
        p_row = p_df[p_df["segment_name"] == selected_seg].iloc[0].to_dict()
        
        # Render Detailed Persona Blueprint Card
        card_html = f"""<div style='background: rgba(30, 41, 59, 0.7); border: 1.5px solid rgba(129, 140, 248, 0.3); border-radius: 12px; padding: 20px; margin-top: 10px;'>
<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
<div>
<span style='font-size: 20px; font-weight: 700; color: #818cf8;'>🎭 {p_row.get("persona_name")}</span>
<span style='font-size: 13px; color: #94a3b8; margin-left: 10px;'>[Segment: {p_row.get("segment_name")}]</span>
</div>
<div>
<span style='background: rgba(129, 140, 248, 0.2); color: #818cf8; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 12px;'>Priority: {p_row.get("priority_level")}</span>
<span style='background: rgba(52, 211, 153, 0.2); color: #34d399; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 12px; margin-left: 6px;'>Channel: {p_row.get("preferred_channel")}</span>
</div>
</div>
<p style='color: #cbd5e1; font-size: 14px;'><b>Description (FR):</b> {p_row.get("description_fr")}</p>
<p style='color: #94a3b8; font-size: 13px;'><b>Description (EN):</b> {p_row.get("description_en")}</p>
<div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 16px;'>
<div style='background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px;'>
<strong style='color: #60a5fa;'>📊 Behavior Profile</strong>
<p style='font-size: 12px; color: #cbd5e1; margin-top: 4px;'>{p_row.get("behavior_profile_fr")}</p>
</div>
<div style='background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px;'>
<strong style='color: #34d399;'>💎 Value Profile</strong>
<p style='font-size: 12px; color: #cbd5e1; margin-top: 4px;'>{p_row.get("value_profile_fr")}</p>
</div>
<div style='background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px;'>
<strong style='color: #f87171;'>⚠️ Risk Profile</strong>
<p style='font-size: 12px; color: #cbd5e1; margin-top: 4px;'>{p_row.get("risk_profile_fr")}</p>
</div>
</div>
<div style='margin-top: 16px; background: rgba(129, 140, 248, 0.1); padding: 12px; border-radius: 8px; border-left: 4px solid #818cf8;'>
<strong style='color: #c084fc;'>🚀 Recommended Marketing Action</strong>
<p style='font-size: 13px; color: #f8fafc; margin-top: 4px;'>{p_row.get("recommended_action_fr")}</p>
</div>
</div>"""

        if hasattr(st, "html"):
            st.html(card_html)
        else:
            st.markdown(card_html, unsafe_allow_html=True)

    else:
        st.warning("No personas registered in catalog.")

def render_dynamic_personas_tab(df_data):
    """Renders the exploratory Dynamic Personas tab with cluster selection (2-9), cards, and charts."""
    st.markdown("<div class='section-header'><span class='icon'>⚡</span><span class='title'>Dynamic Data-Driven Persona Generator</span></div>", unsafe_allow_html=True)

    # Explanation Box
    st.info(
        "💡 **Fixed vs. Dynamic Personas**: Fixed personas are stable business profiles used for official marketing interpretation "
        "and Digital Twin resolution. **Dynamic personas** are temporary, data-driven profiles generated directly from the current "
        "clustering result. Their number follows the selected number of clusters (2 to 9)."
    )

    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        n_clusters = st.slider(
            "Select Number of Dynamic Clusters / Personas:",
            min_value=2, max_value=9, value=5, step=1,
            key="dyn_n_clusters_slider"
        )
    with col_ctrl2:
        recluster_btn = st.button("🤖 Re-Cluster & Generate Dynamic Personas", key="btn_recluster_dyn", width="stretch", type="primary")

    # Run clustering if required or requested
    if recluster_btn or "df" not in st.session_state or st.session_state.get("dyn_last_n_clusters") != n_clusters:
        try:
            from app import run_customer_clustering
            df_data, pca_df_res, _ = run_customer_clustering(df_data, n_clusters=n_clusters)
            st.session_state["df"] = df_data
            st.session_state["dyn_last_n_clusters"] = n_clusters
        except Exception as e:
            logger.warning(f"Clustering execution note: {e}")

    # Generate Dynamic Personas
    dynamic_personas = generate_dynamic_personas(df_data, cluster_col="ml_cluster_id")

    if not dynamic_personas:
        st.warning("⚠️ No clusters found. Please run clustering or select a client dataset.")
        return

    st.success(f"✅ Generated **{len(dynamic_personas)} Dynamic Persona Profiles** based on {n_clusters} clusters!")

    # Render Visual Charts
    st.markdown("<div class='section-header' style='margin-top:16px;'><span class='icon'>📊</span><span class='title'>Dynamic Cohort Metrics Breakdown</span></div>", unsafe_allow_html=True)

    dyn_df = pd.DataFrame(dynamic_personas)
    dyn_df["chart_label"] = dyn_df.apply(
        lambda r: f"Cluster {r['cluster_id']} — {r['persona_name'].split('—')[-1].strip()[:20]}", axis=1
    )

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig_size = px.bar(
            dyn_df, x="chart_label", y="entity_count",
            color="chart_label", text="entity_count",
            title="Entity Count per Dynamic Persona",
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        fig_size.update_layout(template="plotly_dark", height=280, showlegend=False, xaxis_title="", margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig_size, use_container_width=True)

    with chart_col2:
        fig_clv = px.bar(
            dyn_df, x="chart_label", y="avg_clv",
            color="chart_label", text_auto=".0f",
            title="Average Predicted CLV (MAD) by Dynamic Persona",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_clv.update_layout(template="plotly_dark", height=280, showlegend=False, xaxis_title="", margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig_clv, use_container_width=True)


    # Optional LLM Enhancement Button
    st.markdown("---")
    col_llm1, col_llm2 = st.columns([1, 2])
    with col_llm1:
        if st.button("🤖 Generate LLM Persona Narratives", key="btn_llm_dyn_narrative", help="Enhance dynamic persona descriptions using Ollama (Button-triggered only, zero PII)"):
            with st.spinner("Generating LLM narrative enhancements for dynamic personas..."):
                for p in dynamic_personas:
                    llm_res = generate_dynamic_persona_with_llm(p)
                    if llm_res and "persona_name" in llm_res:
                        p["persona_name"] = f"Cluster {p['cluster_id']} — {llm_res.get('persona_name')}"
                        p["description"] = llm_res.get("description", p["description"])
                        p["recommended_action"] = llm_res.get("recommended_action", p["recommended_action"])
            st.success("✅ LLM Persona Narratives updated!")

    # Render Dynamic Persona Cards
    st.markdown("<div class='section-header'><span class='icon'>🎴</span><span class='title'>Dynamic Persona Profile Cards</span></div>", unsafe_allow_html=True)
    build_dynamic_persona_cards(dynamic_personas)

    # Expandable Dataframe Inspector
    with st.expander("🔎 View Entities in Dynamic Personas Dataframe", expanded=False):
        if "ml_cluster_id" in df_data.columns:
            inspect_cols = [
                "entity_id", "entity_type", "ml_cluster_id", "dynamic_class",
                "customer_segment", "customer_persona", "rfm_score",
                "predicted_clv_amount_mad", "churn_risk_score"
            ]
            avail_inspect = [c for c in inspect_cols if c in df_data.columns]
            st.dataframe(df_data[avail_inspect].dropna(subset=["ml_cluster_id"]), use_container_width=True, hide_index=True)

def render_persona_comparison_tab():
    """Renders the Comparison view explaining Stable vs Dynamic Personas."""
    st.markdown("<div class='section-header'><span class='icon'>⚖️</span><span class='title'>Stable vs. Dynamic Personas Comparison</span></div>", unsafe_allow_html=True)

    st.markdown(
        "OSMOS clearly distinguishes between **Stable Strategic Personas** and **Dynamic Data-Driven Personas**. "
        "The table below outlines their architectural roles and business use cases."
    )

    comparison_data = {
        "Aspect": [
            "Number of Personas",
            "Source of Profile",
            "Platform Role",
            "Used by Digital Twin",
            "Stability across Runs",
            "Primary Business Use"
        ],
        "Stable Personas": [
            "Fixed at 9 Predefined Blueprints",
            "Predefined Strategic Persona Library",
            "Official Business Interpretation Layer",
            "Yes (enforces resolution chain)",
            "100% Stable & Deterministic",
            "Decision Consistency & Strategy Alignment"
        ],
        "Dynamic Personas": [
            "Variable (2 to 9, matches selected k)",
            "Current KMeans Clustering Output",
            "Exploratory Data-Driven Discovery",
            "No (exploratory analysis tab only)",
            "Varies with data & cluster count",
            "Data Exploration & Cohort Discovery"
        ]
    }

    comp_df = pd.DataFrame(comparison_data)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    st.markdown("""
    <div style='background: rgba(129, 140, 248, 0.1); border-left: 4px solid #818cf8; padding: 14px; border-radius: 8px; margin-top: 16px;'>
        <strong style='color: #c084fc; font-size: 14px;'>💡 Architectural Rule:</strong>
        <p style='color: #f8fafc; font-size: 13px; margin: 4px 0 0 0;'>
            Stable personas ensure <b>decision consistency</b> across the platform and power the Digital Twin resolution chain
            (<code>entity_id → Digital Twin → segment → persona</code>). Dynamic personas allow analysts and marketers to explore
            how the customer base reorganizes when different clustering granularities (from 2 to 9 clusters) are selected.
        </p>
    </div>
    """, unsafe_allow_html=True)
