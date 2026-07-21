import streamlit as st
import pandas as pd
from admin.database_metrics import is_postgres_available
from database.repositories import get_llm_action_recommendations
from digital_twin.digital_twin_builder import build_digital_twin_profile
from campaigns.campaign_repository import (
    get_campaign_dispatches,
    get_campaign_responses,
    get_pending_campaigns,
    get_campaign_by_id
)
from campaigns.campaign_dispatcher import (
    create_campaign_from_recommendation,
    create_campaign_from_digital_twin_action,
    approve_campaign,
    simulate_dispatch,
    cancel_campaign
)
from campaigns.campaign_simulator import simulate_campaign_response
from campaigns.campaign_metrics import (
    get_campaign_overview_metrics,
    get_campaign_response_distribution,
    get_campaign_success_by_type,
    get_campaign_success_by_channel,
    get_campaign_impact_on_clv
)

def render_campaign_dashboard(df_data=None):
    """
    Renders the Closed-Loop Campaign Simulation Dashboard.
    """
    st.markdown("<h1 style='margin:0; font-size: 32px;'>🚀 Closed-Loop <span style='background: linear-gradient(135deg,#38bdf8,#818cf8,#c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Campaign Simulation</span></h1>", unsafe_allow_html=True)
    st.markdown("Convert LLM Action Recommendations and Digital Twin states into simulated campaign dispatches, simulate customer responses, and audit closed-loop CRM feedback.")
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # 1. PostgreSQL Backend Availability Guard
    if not is_postgres_available():
        st.warning("⚠️ **Campaign simulation with dispatch tracking requires PostgreSQL.**")
        st.info("The application is currently running in **Excel Fallback Mode**. Please start PostgreSQL (`OSMOS_STORAGE_BACKEND=postgres`) to enable full campaign creation, response simulation, and historical feedback loops.")
        return

    # 2. Section Tabs
    t_overview, t_rec, t_twin, t_dispatch, t_history, t_impact = st.tabs([
        "📊 Campaign Overview",
        "💡 Create from Recommendation",
        "👤 Create from Digital Twin",
        "⚡ Simulate Customer Response",
        "📋 Campaign History & Audit",
        "📈 Campaign Impact Analysis"
    ])

    # ── A. Campaign Overview ──
    with t_overview:
        metrics = get_campaign_overview_metrics()
        
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Total Campaigns", metrics["total_campaigns"])
        m2.metric("Draft Campaigns", metrics["draft_campaigns"])
        m3.metric("Approved", metrics["approved_campaigns"])
        m4.metric("Dispatched", metrics["simulated_dispatches"])
        m5.metric("Responded", metrics["responded_campaigns"])
        m6.metric("Response Rate", f"{metrics['response_rate_pct']}%")

        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)
        
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.markdown("<div class='section-header'><span class='icon'>📩</span><span class='title'>Response Distribution</span></div>", unsafe_allow_html=True)
            dist_df = get_campaign_response_distribution()
            if not dist_df.empty:
                st.dataframe(dist_df, width="stretch", hide_index=True)
            else:
                st.info("No campaign responses recorded yet.")

        with col_c2:
            st.markdown("<div class='section-header'><span class='icon'>🎯</span><span class='title'>Campaign Types</span></div>", unsafe_allow_html=True)
            type_df = get_campaign_success_by_type()
            if not type_df.empty:
                st.dataframe(type_df, width="stretch", hide_index=True)
            else:
                st.info("No campaign dispatches recorded.")

        with col_c3:
            st.markdown("<div class='section-header'><span class='icon'>📱</span><span class='title'>Marketing Channels</span></div>", unsafe_allow_html=True)
            chan_df = get_campaign_success_by_channel()
            if not chan_df.empty:
                st.dataframe(chan_df, width="stretch", hide_index=True)
            else:
                st.info("No campaign dispatches recorded.")

    # ── B. Create Campaign from LLM Recommendation ──
    with t_rec:
        st.markdown("<div class='section-header'><span class='icon'>💡</span><span class='title'>Convert LLM Action Recommendation into Campaign</span></div>", unsafe_allow_html=True)
        recs = get_llm_action_recommendations(limit=50)
        
        if recs:
            rec_options = {f"#{r['id']} | [{r.get('entity_id')}] {r.get('alert_type')} ({r.get('priority')} Priority)": r['id'] for r in recs}
            selected_rec_label = st.selectbox("Select Action Recommendation to Dispatch:", list(rec_options.keys()), key="sb_rec_dispatch")
            selected_rec_id = rec_options[selected_rec_label]
            
            rec_item = next(r for r in recs if r['id'] == selected_rec_id)
            
            st.markdown(f"""<div style='background:rgba(30,41,59,0.7); border:1px solid #818cf8; padding:16px; border-radius:10px;'>
                <strong style='color:#818cf8;'>Recommendation details:</strong> Entity: <b>{rec_item.get('entity_id')}</b> | Alert: <b>{rec_item.get('alert_type')}</b><br>
                <p style='font-size:13px; color:#cbd5e1; margin-top:6px;'><b>Recommandation (FR):</b> {rec_item.get('recommended_action_fr')}</p>
                <p style='font-size:13px; color:#94a3b8;'><b>Message Draft (FR):</b> {rec_item.get('message_draft_fr')}</p>
                <span style='background:rgba(129,140,248,0.2); color:#818cf8; padding:4px 8px; border-radius:4px; font-size:12px;'>Channel: {rec_item.get('suggested_channel')}</span>
            </div>""", unsafe_allow_html=True)
            
            st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("📝 Create Campaign Draft", key="btn_create_draft_rec"):
                    cid = create_campaign_from_recommendation(selected_rec_id)
                    if cid:
                        st.success(f"Successfully created Campaign Draft #{cid}!")
                        st.rerun()
            with col_b2:
                if st.button("🚀 Create & Approve Immediately", key="btn_create_approve_rec"):
                    cid = create_campaign_from_recommendation(selected_rec_id)
                    if cid:
                        approve_campaign(cid)
                        st.success(f"Successfully created & approved Campaign #{cid}!")
                        st.rerun()
        else:
            st.info("No LLM Action Recommendations found. Generate an LLM recommendation from Critical Action Alerts on the main dashboard first.")

    # ── C. Create Campaign from Digital Twin ──
    with t_twin:
        st.markdown("<div class='section-header'><span class='icon'>👤</span><span class='title'>Create Campaign Directly from Digital Twin Profile</span></div>", unsafe_allow_html=True)
        
        if df_data is not None and not df_data.empty and "entity_id" in df_data.columns:
            entity_list = sorted(df_data["entity_id"].dropna().unique())
        else:
            entity_list = ["C00001", "P00001", "P01501"]
            
        selected_dt_entity = st.selectbox("Select Digital Twin Entity ID:", entity_list, key="sb_dt_camp_entity")
        
        profile = build_digital_twin_profile(selected_dt_entity)
        persona = profile.get("persona_context", {})
        
        st.markdown(f"""<div style='background:rgba(30,41,59,0.7); border:1px solid #34d399; padding:16px; border-radius:10px;'>
            <strong style='color:#34d399;'>Digital Twin State: [{selected_dt_entity}]</strong> | Class: <b>{profile['predictions']['dynamic_class']}</b> | Segment: <b>{persona.get('customer_segment')}</b><br>
            <p style='font-size:13px; color:#cbd5e1; margin-top:6px;'><b>Persona Blueprint:</b> 🎭 {persona.get('customer_persona')}</p>
            <p style='font-size:13px; color:#cbd5e1;'><b>Action Recommandée:</b> {persona.get('recommended_action_fr')}</p>
        </div>""", unsafe_allow_html=True)
        
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
        
        c_title = st.text_input("Campaign Title", f"Outreach for {selected_dt_entity}", key="inp_camp_title")
        c_type = st.selectbox("Campaign Type", ["Retention Campaign", "Reactivation Campaign", "VIP Loyalty Campaign", "Service Recovery Campaign", "Cross-sell Campaign"], key="sb_camp_type")
        c_channel = st.selectbox("Channel", [persona.get('preferred_channel', 'Email'), "Email", "SMS", "Phone", "Dashboard Follow-up"], key="sb_camp_channel")
        
        if st.button("📝 Create Digital Twin Campaign Draft", key="btn_create_dt_camp"):
            ctx = {
                "campaign_type": c_type,
                "campaign_channel": c_channel,
                "campaign_title": c_title,
                "campaign_message_fr": persona.get('recommended_action_fr'),
                "campaign_message_en": persona.get('recommended_action_en'),
                "priority": persona.get('priority_level', 'Medium')
            }
            cid = create_campaign_from_digital_twin_action(selected_dt_entity, ctx)
            if cid:
                st.success(f"Successfully created Campaign Draft #{cid} for Entity [{selected_dt_entity}]!")
                st.rerun()

    # ── D. Simulate Customer Response ──
    with t_dispatch:
        st.markdown("<div class='section-header'><span class='icon'>⚡</span><span class='title'>Simulate Campaign Dispatch & Customer Response</span></div>", unsafe_allow_html=True)
        
        pending_camps = get_pending_campaigns(limit=50)
        dispatched_camps = get_campaign_dispatches(status="Simulated Dispatch", limit=50)
        
        st.subheader("Step 1: Approve & Simulate Dispatch")
        if pending_camps:
            p_options = {f"#{c['campaign_id']} | [{c['entity_id']}] {c['campaign_title']} (Status: {c['status']})": c['campaign_id'] for c in pending_camps}
            selected_pending_label = st.selectbox("Select Pending Campaign Draft:", list(p_options.keys()), key="sb_pending_dispatch")
            selected_p_id = p_options[selected_pending_label]
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Approve Campaign", key="btn_approve_camp"):
                    approve_campaign(selected_p_id)
                    st.success(f"Campaign #{selected_p_id} Approved.")
                    st.rerun()
            with c2:
                if st.button("🚀 Simulate Dispatch (Zero Real Messages)", key="btn_sim_dispatch"):
                    approve_campaign(selected_p_id)
                    simulate_dispatch(selected_p_id)
                    st.success(f"Simulated dispatch executed for Campaign #{selected_p_id}!")
                    st.rerun()
        else:
            st.info("No pending draft/approved campaigns.")

        st.markdown("---")
        st.subheader("Step 2: Simulate Customer Response (Closed-Loop)")
        
        all_sim_ready = get_campaign_dispatches(limit=50)
        ready_camps = [c for c in all_sim_ready if c.get("status") in ["Approved", "Simulated Dispatch"]]
        
        if ready_camps:
            r_options = {f"#{c['campaign_id']} | [{c['entity_id']}] {c['campaign_title']} ({c['status']})": c['campaign_id'] for c in ready_camps}
            selected_ready_label = st.selectbox("Select Dispatched Campaign to Simulate Response:", list(r_options.keys()), key="sb_ready_response")
            selected_r_id = r_options[selected_ready_label]
            
            sim_mode = st.radio("Simulation Mode:", ["Auto Simulation (Probabilistic State Model)", "Force Specific Customer Response"], horizontal=True, key="rad_sim_mode")
            
            forced_resp = None
            if "Force" in sim_mode:
                forced_resp = st.selectbox("Select Customer Response to Force:", [
                    "Opened", "Clicked", "Purchased", "Ignored", "Unsubscribed", "Complained", "Positive Feedback", "Negative Feedback"
                ], key="sb_forced_resp")
                
            if st.button("⚡ Simulate Customer Response & Update Digital Twin", key="btn_exec_sim_resp"):
                with st.spinner("Simulating customer response, generating event, and updating Digital Twin..."):
                    res = simulate_campaign_response(selected_r_id, forced_response_type=forced_resp)
                    if res:
                        st.success(f"Response '{res['response_type']}' simulated for Campaign #{selected_r_id}! Generated Event ID: {res['event_id']}")
                        st.rerun()
        else:
            st.info("No dispatched campaigns waiting for response simulation.")

    # ── E. Campaign History ──
    with t_history:
        st.markdown("<div class='section-header'><span class='icon'>📋</span><span class='title'>Campaign Audit Log & Responses Table</span></div>", unsafe_allow_html=True)
        
        st.subheader("Campaign Dispatches")
        dispatches = get_campaign_dispatches(limit=100)
        if dispatches:
            st.dataframe(pd.DataFrame(dispatches), width="stretch", hide_index=True)
        else:
            st.info("No campaign dispatches found.")
            
        st.markdown("---")
        st.subheader("Simulated Customer Responses")
        responses = get_campaign_responses()
        if responses:
            st.dataframe(pd.DataFrame(responses), width="stretch", hide_index=True)
        else:
            st.info("No campaign responses recorded.")

    # ── F. Campaign Impact ──
    with t_impact:
        st.markdown("<div class='section-header'><span class='icon'>📈</span><span class='title'>Closed-Loop Campaign Impact Analysis</span></div>", unsafe_allow_html=True)
        
        dispatches = get_campaign_dispatches(limit=100)
        if dispatches:
            c_ids = [c['campaign_id'] for c in dispatches]
            sel_impact_cid = st.selectbox("Select Campaign ID to analyze closed-loop impact:", c_ids, key="sb_impact_cid")
            
            impact = get_campaign_impact_on_clv(sel_impact_cid)
            c_info = get_campaign_by_id(sel_impact_cid)
            
            i1, i2, i3 = st.columns(3)
            i1.metric("Before Campaign CLV", f"{impact['before_clv']:.2f} MAD")
            i2.metric("After Campaign CLV", f"{impact['after_clv']:.2f} MAD")
            i3.metric("CLV Value Lift", f"{impact['clv_lift']:+.2f} MAD", delta=f"{impact['clv_lift']:.2f} MAD")
            
            if c_info:
                st.markdown(f"""<div style='background:rgba(30,41,59,0.5); padding:12px; border-radius:8px; margin-top:12px;'>
                    <b>Campaign Title:</b> {c_info.get('campaign_title')}<br>
                    <b>Target Entity:</b> {c_info.get('entity_id')}<br>
                    <b>Status:</b> {c_info.get('status')}<br>
                    <b>Channel:</b> {c_info.get('campaign_channel')}
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No campaign dispatches available for impact analysis.")
