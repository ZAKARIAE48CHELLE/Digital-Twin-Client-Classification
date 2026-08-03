import streamlit as st
import pandas as pd
from ui.icons import icon_html
from ui.layout import render_page_header, section_header_html
from digital_twin.digital_twin_builder import build_digital_twin_profile
from digital_twin.digital_twin_explainer import (
    explain_digital_twin_state,
    generate_llm_digital_twin_summary
)
from personas.persona_dashboard import render_stable_persona_library as render_persona_library_dashboard

from personas.persona_matcher import explain_persona_assignment
from admin.database_metrics import is_postgres_available

def _is_valid_data(val):
    if val is None:
        return False
    if isinstance(val, pd.DataFrame):
        return not val.empty
    if isinstance(val, (list, tuple)):
        return len(val) > 0
    return False

def render_digital_twin_dashboard(df=None, history_df=None):
    """
    Renders the unified Digital Twin & Persona Dashboard page.
    """
    render_page_header(
        "Digital Twin & Persona Intelligence",
        "Individual-level Digital Twin representation, score vectors, persona assignment, and historical track records.",
        icon="Digital Twin & Persona",
        badge="Digital Twin Explorer",
    )

    tab_twin, tab_library = st.tabs([
        "Digital Twin Explorer",
        "Persona Library Catalog"
    ])

    with tab_twin:
        render_digital_twin_explorer_tab(df)

    with tab_library:
        render_persona_library_dashboard()

def render_digital_twin_explorer_tab(df=None):
    """Renders the individual entity Digital Twin Explorer tab."""
    # A. Entity Selector
    if df is not None and not df.empty and "entity_id" in df.columns:
        entity_list = sorted(df["entity_id"].dropna().unique())
    else:
        entity_list = ["P00001", "C00001", "C00002"]
        
    selected_entity_id = st.selectbox(
        "Select Client or Prospect Entity ID to inspect Digital Twin:",
        entity_list,
        key="dt_entity_selector"
    )
    
    # Build complete Digital Twin profile
    profile = build_digital_twin_profile(selected_entity_id)
    identity = profile["core_identity"]
    behavior = profile["behavioral_state"]
    scores = profile["scores"]
    predictions = profile["predictions"]
    persona = profile["persona_context"]
    history = profile["history"]
    deterministic_exp = explain_digital_twin_state(profile)
    assignment_chain = explain_persona_assignment(selected_entity_id)

    # B. Digital Twin Summary Card

    st.markdown(f"""<div style='background: rgba(30, 41, 59, 0.8); border: 1.5px solid rgba(129, 140, 248, 0.4); border-radius: 12px; padding: 20px; margin-bottom: 24px;'>
        <div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;'>
            <div>
                <span style='font-size:22px; font-weight:800; color:#818cf8;'>{icon_html("Entity")} Entity [{identity['entity_id']}]</span>
                <span style='font-size:14px; color:#94a3b8; margin-left:10px;'>Type: <b>{identity['entity_type']}</b></span>
            </div>
            <div>
                <span style='background:rgba(59, 130, 246, 0.2); color:#60a5fa; padding:4px 10px; border-radius:6px; font-weight:600; font-size:13px;'>Class: {predictions['dynamic_class']}</span>
                <span style='background:rgba(192, 132, 252, 0.2); color:#c084fc; padding:4px 10px; border-radius:6px; font-weight:600; font-size:13px; margin-left:6px;'>Segment: {persona['customer_segment']}</span>
                <span style='background:rgba(251, 191, 36, 0.2); color:#fbbf24; padding:4px 10px; border-radius:6px; font-weight:600; font-size:13px; margin-left:6px;'>Persona: {persona['customer_persona']}</span>
            </div>
        </div>
        <div style='display:grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap:12px; margin-top:16px;'>
            <div style='background:rgba(15, 23, 42, 0.6); padding:10px; border-radius:8px; text-align:center;'>
                <span style='font-size:11px; color:#94a3b8;'>CLV Amount</span><br><strong style='font-size:16px; color:#34d399;'>{predictions['predicted_clv_amount_mad']:.2f} MAD</strong>
            </div>
            <div style='background:rgba(15, 23, 42, 0.6); padding:10px; border-radius:8px; text-align:center;'>
                <span style='font-size:11px; color:#94a3b8;'>CLV Score</span><br><strong style='font-size:16px; color:#60a5fa;'>{scores['clv_score']:.2f}</strong>
            </div>
            <div style='background:rgba(15, 23, 42, 0.6); padding:10px; border-radius:8px; text-align:center;'>
                <span style='font-size:11px; color:#94a3b8;'>RFM-ES Score</span><br><strong style='font-size:16px; color:#c084fc;'>{scores['rfm_score']:.2f}</strong>
            </div>
            <div style='background:rgba(15, 23, 42, 0.6); padding:10px; border-radius:8px; text-align:center;'>
                <span style='font-size:11px; color:#94a3b8;'>Churn Risk</span><br><strong style='font-size:15px; color:#f87171;'>{scores['churn_risk']}</strong>
            </div>
            <div style='background:rgba(15, 23, 42, 0.6); padding:10px; border-radius:8px; text-align:center;'>
                <span style='font-size:11px; color:#94a3b8;'>Engagement</span><br><strong style='font-size:15px; color:#38bdf8;'>{scores['engagement_score']}</strong>
            </div>
            <div style='background:rgba(15, 23, 42, 0.6); padding:10px; border-radius:8px; text-align:center;'>
                <span style='font-size:11px; color:#94a3b8;'>Decision Priority</span><br><strong style='font-size:15px; color:#fbbf24;'>{scores['decision_priority_score']}</strong>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # C. Digital Twin State Cards
    st.markdown(section_header_html("Digital Twin Multi-Dimensional States", "Chart"), unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""<div style='background:rgba(30, 41, 59, 0.5); border-left:4px solid #3b82f6; padding:14px; border-radius:8px;'>
            <strong style='color:#60a5fa;'>{icon_html("Engagement")} Behavioral State</strong>
            <ul style='font-size:12px; color:#cbd5e1; margin-top:6px; padding-left:18px;'>
                <li>Recency: <b>{behavior['recency_days']} days</b></li>
                <li>Visits (30d): <b>{behavior['visits_30d']}</b></li>
                <li>Product Views (30d): <b>{behavior['product_views_30d']}</b></li>
                <li>Purchases (90d): <b>{behavior['purchases_90d']}</b></li>
                <li>Total Spent (90d): <b>{behavior['total_spent_90d_mad']:.2f} MAD</b></li>
            </ul>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""<div style='background:rgba(30, 41, 59, 0.5); border-left:4px solid #34d399; padding:14px; border-radius:8px;'>
            <strong style='color:#34d399;'>{icon_html("Value")} Predictive & Value State</strong>
            <ul style='font-size:12px; color:#cbd5e1; margin-top:6px; padding-left:18px;'>
                <li>Predicted CLV: <b>{predictions['predicted_clv_amount_mad']:.2f} MAD</b></li>
                <li>CLV Segment: <b>{predictions['predicted_clv_segment']}</b></li>
                <li>CLV Score: <b>{scores['clv_score']:.2f}</b></li>
                <li>Avg Order Value: <b>{behavior['avg_order_value_mad']:.2f} MAD</b></li>
            </ul>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div style='background:rgba(30, 41, 59, 0.5); border-left:4px solid #f87171; padding:14px; border-radius:8px;'>
            <strong style='color:#f87171;'>{icon_html("Warning")} Risk & Engagement State</strong>
            <ul style='font-size:12px; color:#cbd5e1; margin-top:6px; padding-left:18px;'>
                <li>Churn Risk: <b>{scores['churn_risk']}</b></li>
                <li>Engagement: <b>{scores['engagement_score']}</b></li>
                <li>Complaints (90d): <b>{behavior['complaint_count_90d']}</b></li>
                <li>Email Open Rate: <b>{behavior['email_open_rate']*100:.1f}%</b></li>
            </ul>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # D. Digital Twin Timeline Tabs
    st.markdown(section_header_html("Digital Twin Track Record History", "History"), unsafe_allow_html=True)
    t_ev, t_clv, t_rfm, t_class, t_seg = st.tabs([
        "Events Timeline",
        "CLV Evolution",
        "RFM Evolution",
        "Classification History",
        "Segment/Persona History"
    ])
    
    with t_ev:
        evs = history.get("events", [])
        if _is_valid_data(evs):
            st.dataframe(pd.DataFrame(evs), width="stretch", hide_index=True)
        else:
            st.info("No recorded event history for this entity.")

    with t_clv:
        clv_h = history.get("clv_history", [])
        if _is_valid_data(clv_h):
            st.dataframe(pd.DataFrame(clv_h), width="stretch", hide_index=True)
        else:
            st.info("No CLV history recorded.")

    with t_rfm:
        rfm_h = history.get("rfm_history", [])
        if _is_valid_data(rfm_h):
            st.dataframe(pd.DataFrame(rfm_h), width="stretch", hide_index=True)
        else:
            st.info("No RFM history recorded.")

    with t_class:
        class_h = history.get("classification_history", [])
        if _is_valid_data(class_h):
            st.dataframe(pd.DataFrame(class_h), width="stretch", hide_index=True)
        else:
            st.info("No classification history recorded.")

    with t_seg:
        seg_h = history.get("segment_history", [])
        if _is_valid_data(seg_h):
            st.dataframe(pd.DataFrame(seg_h), width="stretch", hide_index=True)
        else:
            st.info("No segment transition history recorded.")


    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # E. Persona & F. Explanation Panels
    col_p, col_e = st.columns(2)
    
    with col_p:
        st.markdown(section_header_html("Associated Persona Blueprint", "Persona"), unsafe_allow_html=True)
        st.markdown(f"""<div style='background:rgba(30, 41, 59, 0.7); border:1px solid rgba(192, 132, 252, 0.3); padding:16px; border-radius:10px;'>
            <strong style='color:#c084fc; font-size:16px;'>{icon_html("Persona")} {persona['customer_persona']}</strong><br>
            <span style='font-size:12px; color:#94a3b8;'>Resolution Chain: {assignment_chain['resolution_chain']}</span>
            <hr style='border-color:rgba(255,255,255,0.1); margin:10px 0;'>
            <p style='font-size:13px; color:#cbd5e1;'><b>Description:</b> {persona['persona_description_fr']}</p>
            <p style='font-size:13px; color:#cbd5e1;'><b>Action Recommandée:</b> {persona['recommended_action_fr']}</p>
            <div style='display:flex; gap:10px; margin-top:10px;'>
                <span style='background:rgba(129,140,248,0.2); color:#818cf8; padding:4px 8px; border-radius:4px; font-size:12px;'>Canal: {persona['preferred_channel']}</span>
                <span style='background:rgba(251,191,36,0.2); color:#fbbf24; padding:4px 8px; border-radius:4px; font-size:12px;'>Priorité: {persona['priority_level']}</span>
            </div>
        </div>""", unsafe_allow_html=True)

    with col_e:
        st.markdown(section_header_html("Deterministic State Explanations", "Model"), unsafe_allow_html=True)
        st.markdown(f"""<div style='background:rgba(30, 41, 59, 0.7); border:1px solid rgba(52, 211, 153, 0.3); padding:16px; border-radius:10px;'>
            <p style='font-size:12px; color:#cbd5e1;'><b>Risque:</b> {deterministic_exp['risk_explanation']['explanation_fr']}</p>
            <p style='font-size:12px; color:#cbd5e1;'><b>Valeur:</b> {deterministic_exp['value_explanation']['explanation_fr']}</p>
            <p style='font-size:12px; color:#cbd5e1;'><b>Engagement:</b> {deterministic_exp['engagement_explanation']['explanation_fr']}</p>
            <p style='font-size:12px; color:#cbd5e1;'><b>Action:</b> {deterministic_exp['action_explanation']['explanation_fr']}</p>
        </div>""", unsafe_allow_html=True)


    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # G. LLM Digital Twin Summary (BUTTON-TRIGGERED ONLY)
    st.markdown(section_header_html("LLM Digital Twin Cognitive Summary", "LLM"), unsafe_allow_html=True)
    st.caption("Generate a local LLM natural language cognitive summary for this entity's digital twin on demand.")
    
    if st.button("Generate LLM Digital Twin Summary", key="btn_gen_llm_dt_summary"):
        with st.spinner("Analyzing Digital Twin profile via Local LLM..."):
            llm_res = generate_llm_digital_twin_summary(selected_entity_id)
            if llm_res:
                st.markdown(f"""
                <div style='background:rgba(129, 140, 248, 0.1); border:1.5px solid #818cf8; border-radius:10px; padding:18px; margin-top:10px;'>
                    <h4 style='color:#818cf8; margin-top:0;'>{icon_html("LLM")} Cognitive LLM Analysis (Entity {selected_entity_id})</h4>
                    <p style='color:#f8fafc; font-size:14px;'><b>Résumé Exécutif (FR):</b> {llm_res.get('summary_fr')}</p>
                    <p style='color:#cbd5e1; font-size:13px;'><b>Executive Summary (EN):</b> {llm_res.get('summary_en')}</p>
                    <hr style='border-color:rgba(255,255,255,0.1);'>
                    <p style='color:#60a5fa; font-size:13px;'><b>Analyse Risque & Valeur:</b> {llm_res.get('risk_interpretation_fr')} | {llm_res.get('value_interpretation_fr')}</p>
                    <p style='color:#34d399; font-size:13px;'><b>Action Recommandée:</b> {llm_res.get('recommended_action_fr')}</p>
                    <p style='color:#fbbf24; font-size:12px;'><b>Directives Admin:</b> {llm_res.get('admin_guidance_fr')}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Unable to generate LLM summary.")

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # H. Campaign History for this Digital Twin
    st.markdown(section_header_html("Campaign History for this Digital Twin", "Campaign"), unsafe_allow_html=True)
    if is_postgres_available():
        from campaigns.campaign_metrics import get_entity_campaign_history
        camp_h = get_entity_campaign_history(selected_entity_id)
        if not camp_h["dispatches"].empty:
            c1_dt, c2_dt = st.columns(2)
            with c1_dt:
                st.markdown("<strong style='font-size:13px; color:#818cf8;'>Dispatched Campaigns</strong>", unsafe_allow_html=True)
                st.dataframe(camp_h["dispatches"][["campaign_id", "campaign_title", "status", "priority", "created_at"]], width="stretch", hide_index=True)
            with c2_dt:
                st.markdown("<strong style='font-size:13px; color:#34d399;'>Simulated Customer Responses</strong>", unsafe_allow_html=True)
                if not camp_h["responses"].empty:
                    st.dataframe(camp_h["responses"][["response_id", "campaign_id", "response_type", "simulated_at"]], width="stretch", hide_index=True)
                else:
                    st.info("No responses recorded for this entity.")
        else:
            st.info("No campaign activity recorded for this entity.")
    else:
        st.info("Campaign history tracking requires PostgreSQL backend.")

