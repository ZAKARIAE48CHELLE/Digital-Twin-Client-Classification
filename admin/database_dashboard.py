# ============================================================
# OSMOS Database Intelligence Dashboard (Phase 3)
#
# Scientific Explanation:
# PostgreSQL enables OSMOS to move from static prediction display to historical intelligence.
# Every event, RFM-ES recalculation, classification prediction, CLV prediction, and segment/persona
# assignment can be tracked over time, which supports traceability, explainability, and marketing
# decision monitoring.
# ============================================================

import streamlit as st
import pandas as pd
import os
import storage.storage_manager as storage_manager
import admin.database_metrics as db_metrics
import analytics.clv_trend_alerts as clv_alerts
import analytics.segment_transitions as seg_trans
import analytics.prediction_drift as pred_drift
import database.action_recommendations_repository as action_repo
import llm.action_intelligence as llm_intel


@st.cache_data(ttl=60)
def load_cached_clv_alerts(days=30, drop_threshold=0.20):
    return clv_alerts.get_clv_trend_alerts(days, drop_threshold)

@st.cache_data(ttl=60)
def load_cached_segment_transitions(days=90):
    return seg_trans.get_segment_transitions(days)

@st.cache_data(ttl=60)
def load_cached_transition_matrix(days=90):
    return seg_trans.get_segment_transition_matrix(days)

@st.cache_data(ttl=60)
def load_cached_prediction_drift():
    return pred_drift.detect_prediction_drift()


def render_database_dashboard(df, history_df):
    st.markdown("<h2 style='text-align: center; color: #818cf8;'>🔮 Database Intelligence Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 14px;'>Traceability, model lineage, audit logging and historical lifecycle insights.</p>", unsafe_allow_html=True)
    
    # 1. Check Active Storage Backend and Failover status
    backend = storage_manager.get_storage_backend()
    fallback_active, fallback_reason = storage_manager.get_fallback_status()
    
    # Refresh Button
    col_ref, col_spacer = st.columns([1.5, 8.5])
    with col_ref:
        if st.button("🔄 Refresh Database Metrics", width="stretch"):
            st.cache_data.clear()
            st.rerun()
            
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    
    if backend == "excel":
        if fallback_active:
            st.warning(f"⚠️ **PostgreSQL Connection Failed**: The platform has automatically failed over to the Excel storage engine. Error details: `{fallback_reason}`")
        else:
            st.info("ℹ️ **OSMOS is currently running in Excel mode.** Database Intelligence features are available when running the platform with `OSMOS_STORAGE_BACKEND=postgres`.")
            
        # Display Basic Excel Mode Telemetry
        st.markdown("<div class='section-header'><span class='icon'>📊</span><span class='title'>Local Excel Spreadsheet Telemetry</span></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Excel Digital Twins Rows", len(df) if df is not None else 0)
        with col2:
            st.metric("Excel Event Log Rows", len(history_df) if history_df is not None else 0)
        with col3:
            st.metric("Local Storage File", "osmos_digital_twin_data.xlsx")
            
        st.markdown("""
        > [!NOTE]  
        > Switch your environment setting to `OSMOS_STORAGE_BACKEND=postgres` and launch a local PostgreSQL container to activate historical logging, model registry registration, and audit trace timelines.
        """)
        
        st.markdown("<div class='section-header'><span class='icon'>📈</span><span class='title'>Advanced Historical Intelligence</span></div>", unsafe_allow_html=True)
        st.info("Advanced Historical Intelligence requires PostgreSQL historical tables.")
        st.markdown("<div class='section-header'><span class='icon'>🧠</span><span class='title'>LLM-Assisted Action Intelligence</span></div>", unsafe_allow_html=True)
        st.info("LLM-Assisted Action Intelligence requires PostgreSQL historical tables.")
        return



    # 2. PostgreSQL Active Mode
    if not db_metrics.is_postgres_available():
        st.error("❌ PostgreSQL was requested but connection checks are now returning offline. Check your database credentials or network interface.")
        return
        
    health = db_metrics.get_database_health()
    
    # Health Indicators
    st.markdown("<div class='section-header'><span class='icon'>🩺</span><span class='title'>PostgreSQL Cluster Health Overview</span></div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Cluster Status", health.get("status", "Offline"), delta=None, delta_color="normal")
    with col2:
        st.metric("Active Database", health.get("database_name", "osmos_db"))
    with col3:
        st.metric("Total Digital Twins", health.get("entity_count", 0))
    with col4:
        st.metric("Total Logged Events", health.get("event_count", 0))
        
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        st.info(f"📅 **Latest Logged Event**: {health.get('last_event_date', 'N/A')}")
    with col_date2:
        st.info(f"🔮 **Latest Prediction Logged**: {health.get('last_prediction_date', 'N/A')}")
        
    # 3. Table Overview
    st.markdown("<div class='section-header'><span class='icon'>🗂️</span><span class='title'>Database Table Inventories</span></div>", unsafe_allow_html=True)
    t_counts = db_metrics.get_table_counts()
    t_df = pd.DataFrame(t_counts)
    st.dataframe(t_df, width="stretch", hide_index=True)
    
    # 4. Latest Activities Tabs
    st.markdown("<div class='section-header'><span class='icon'>📝</span><span class='title'>Latest Operational Logs (Database Stream)</span></div>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Latest Events", 
        "Latest Classifications", 
        "Latest CLV predictions", 
        "Latest RFM scores",
        "Latest Cohorts/Personas",
        "System Audit Logs"
    ])
    
    with tab1:
        st.dataframe(db_metrics.get_latest_events(), width="stretch")
    with tab2:
        st.dataframe(db_metrics.get_latest_classification_predictions(), width="stretch")
    with tab3:
        st.dataframe(db_metrics.get_latest_clv_predictions(), width="stretch")
    with tab4:
        st.dataframe(db_metrics.get_latest_rfm_scores(), width="stretch")
    with tab5:
        st.dataframe(db_metrics.get_latest_customer_segments(), width="stretch")
    with tab6:
        st.dataframe(db_metrics.get_audit_logs(), width="stretch")

        
    # 5. Entity Historical Intelligence Explorer
    st.markdown("<div class='section-header'><span class='icon'>🔍</span><span class='title'>Entity Historical Intelligence Explorer</span></div>", unsafe_allow_html=True)
    if df is not None and not df.empty:
        ent_list = sorted(df["entity_id"].dropna().unique())
        selected_ent = st.selectbox("Select Client/Prospect Entity ID to analyze history:", ent_list)
        
        if selected_ent:
            # Query history databases
            timeline_df = db_metrics.get_entity_event_timeline(selected_ent)
            class_hist = db_metrics.get_entity_prediction_history(selected_ent)
            clv_hist = db_metrics.get_entity_clv_history(selected_ent)
            rfm_hist = db_metrics.get_entity_rfm_history(selected_ent)
            seg_hist = db_metrics.get_entity_segment_history(selected_ent)
            
            # Entity Current State Summary Card
            ent_row = df[df["entity_id"] == selected_ent].iloc[0]
            st.markdown(f"""
            <div style='background: rgba(129,140,248,0.06); border: 1px solid rgba(129,140,248,0.2); 
                        border-radius: 12px; padding: 18px; margin-bottom: 20px;'>
                <div style='font-size: 15px; font-weight: 700; color: #a5b4fc; margin-bottom: 12px;'>Entity Current Profile State Summary: {selected_ent}</div>
                <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; font-size: 12px;'>
                    <div><span style='color: #64748b;'>Entity Type:</span> <strong style='color:#cbd5e1;'>{ent_row.get("entity_type", "N/A")}</strong></div>
                    <div><span style='color: #64748b;'>Lifecycle Cohort:</span> <strong style='color:#34d399;'>{ent_row.get("dynamic_class", "N/A")}</strong></div>
                    <div><span style='color: #64748b;'>Customer Segment:</span> <strong style='color:#818cf8;'>{ent_row.get("customer_segment", "N/A")}</strong></div>
                    <div><span style='color: #64748b;'>Current RFM:</span> <strong style='color:#fb7185;'>{ent_row.get("rfm_score", 0.0):.4f}</strong></div>
                    <div><span style='color: #64748b;'>Predicted CLV Amount:</span> <strong style='color:#fbbf24;'>{ent_row.get("predicted_clv_amount_mad", 0.0):.2f} MAD</strong></div>
                    <div><span style='color: #64748b;'>CLV Score:</span> <strong style='color:#cbd5e1;'>{ent_row.get("predicted_clv_score", 0.0):.2f}</strong></div>
                    <div><span style='color: #64748b;'>Persona Label:</span> <strong style='color:#cbd5e1;'>{ent_row.get("customer_persona", "N/A")}</strong></div>
                    <div><span style='color: #64748b;'>Completed Profile:</span> <strong style='color:#cbd5e1;'>{ent_row.get("completed_client_profile", False)}</strong></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Timeline & Evolution Tabs
            tab_timeline, tab_class_ev, tab_clv_ev, tab_rfm_ev, tab_seg_ev = st.columns(5)
            
            st.markdown("<p style='font-size:13px; font-weight:700; color:#818cf8; margin-top:16px;'>Historical Track Records:</p>", unsafe_allow_html=True)
            
            # Events Timeline
            with st.expander("📅 Event History Logs Timeline"):
                if not timeline_df.empty:
                    st.dataframe(timeline_df, width="stretch")
                else:
                    st.write("No historical event logs registered for this entity.")
                    
            # Classification
            with st.expander("🤖 Dynamic Classification History"):
                if not class_hist.empty:
                    st.dataframe(class_hist, width="stretch")
                else:
                    st.write("No lifecycle classification prediction history logged.")
                    
            # CLV
            with st.expander("💰 Customer Lifetime Value (CLV) History"):
                if not clv_hist.empty:
                    col_chart1, col_chart2 = st.columns(2)
                    with col_chart1:
                        st.markdown("<p style='font-size:11px; text-align:center;'>CLV Amount (MAD) Evolution Over Time</p>", unsafe_allow_html=True)
                        st.line_chart(clv_hist.set_index("predicted_at")["predicted_clv_amount_mad"], color="#f59e0b")
                    with col_chart2:
                        st.markdown("<p style='font-size:11px; text-align:center;'>CLV Value Score Evolution Over Time</p>", unsafe_allow_html=True)
                        st.line_chart(clv_hist.set_index("predicted_at")["predicted_clv_score"], color="#3b82f6")
                    st.dataframe(clv_hist, width="stretch")
                else:
                    st.write("No CLV prediction history logged.")
                    
            # RFM
            with st.expander("⚡ RFM-ES score Evolution History"):
                if not rfm_hist.empty:
                    st.markdown("<p style='font-size:11px; text-align:center;'>RFM Score Evolution Over Time</p>", unsafe_allow_html=True)
                    st.line_chart(rfm_hist.set_index("calculated_at")["rfm_score"], color="#ec4899")
                    st.dataframe(rfm_hist, width="stretch")
                else:
                    st.write("No RFMscore history logged.")
                    
            # Segments
            with st.expander("👥 Cohort Segments & Persona Transition History"):
                if not seg_hist.empty:
                    st.dataframe(seg_hist, width="stretch")
                else:
                    st.write("No customer segment/persona assignments logged.")

                    
    # 5.5. Advanced Historical Intelligence Section
    st.markdown("<div class='section-header'><span class='icon'>📈</span><span class='title'>Advanced Historical Intelligence</span></div>", unsafe_allow_html=True)
    
    tab_clv_alerts, tab_seg_transitions, tab_drift_mon = st.tabs([
        "🚨 CLV Trend Alerts",
        "🔀 Segment Transition Matrix",
        "📊 Prediction Drift Monitoring"
    ])
    
    # Tab 1: CLV Trend Alerts
    with tab_clv_alerts:
        clv_alerts_df = load_cached_clv_alerts()
        if clv_alerts_df is not None and not clv_alerts_df.empty:
            total_alerts = len(clv_alerts_df)
            high_alerts = len(clv_alerts_df[clv_alerts_df["alert_level"] == "High"])
            med_alerts = len(clv_alerts_df[clv_alerts_df["alert_level"] == "Medium"])
            low_alerts = len(clv_alerts_df[clv_alerts_df["alert_level"] == "Low"])
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total Alerts", total_alerts)
            with c2:
                st.metric("High Alerts", high_alerts, delta_color="inverse")
            with c3:
                st.metric("Medium Alerts", med_alerts)
            with c4:
                st.metric("Low Alerts", low_alerts)
                
            st.dataframe(clv_alerts_df, width="stretch", hide_index=True)
        else:
            st.info("Not enough historical records yet. Simulate more events to activate this analysis.")
            
    # Tab 2: Segment Transition Matrix
    with tab_seg_transitions:
        transitions_df = load_cached_segment_transitions()
        matrix_df = load_cached_transition_matrix()
        
        if transitions_df is not None and not transitions_df.empty:
            col_m, col_t = st.columns([1, 1])
            with col_m:
                st.markdown("<p style='font-size:14px; font-weight:700;'>Transition Matrix</p>", unsafe_allow_html=True)
                st.dataframe(matrix_df, width="stretch")
            with col_t:
                st.markdown("<p style='font-size:14px; font-weight:700;'>Top 5 Most Common Transitions</p>", unsafe_allow_html=True)
                common_df = transitions_df.groupby(["previous_segment", "latest_segment"]).size().reset_index(name="Count")
                common_df = common_df.sort_values(by="Count", ascending=False).head(5)
                st.dataframe(common_df, width="stretch", hide_index=True)
                
            st.markdown("<p style='font-size:14px; font-weight:700;'>Detailed Transition Logs</p>", unsafe_allow_html=True)
            st.dataframe(transitions_df, width="stretch", hide_index=True)
        else:
            st.info("Not enough historical records yet. Simulate more events to activate this analysis.")
            
    # Tab 3: Prediction Drift Monitoring
    with tab_drift_mon:
        drift_df = load_cached_prediction_drift()
        if drift_df is not None and not drift_df.empty:
            has_high_drift = any(drift_df["drift_level"] == "High")
            if has_high_drift:
                st.warning("⚠️ **High Drift Detected**: Significant change in lifecycle predictions found! Consider re-evaluating baseline models.")
            else:
                st.success("✅ Prediction distribution is stable (no high drift detected).")
                
            st.dataframe(
                drift_df.style.format({
                    "baseline_percent": "{:.1%}",
                    "current_percent": "{:.1%}",
                    "change_percent": "{:+.1%}"
                }),
                width="stretch",
                hide_index=True
            )
        else:
            st.info("Not enough historical records yet. Simulate more events to activate this analysis.")



                
    # 5.6. LLM-Assisted Action Intelligence Section (PostgreSQL mode only)
    st.markdown("<div class='section-header'><span class='icon'>🧠</span><span class='title'>LLM-Assisted Action Intelligence</span></div>", unsafe_allow_html=True)
    
    # Helper to render LLM outputs beautifully
    def render_recommendation_card(rec):
        if not rec:
            return
        st.markdown(f"""
        <div style='background: rgba(129,140,248,0.06); border: 1.5px solid rgba(129,140,248,0.2); 
                    border-radius: 12px; padding: 20px; margin-top: 16px; margin-bottom: 16px;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
                <h4 style='margin:0; color:#a5b4fc;'>🧠 LLM Recommendation Guidance</h4>
                <span style='background: rgba(129,140,248,0.2); color: #cbd5e1; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;'>
                    Confidence: {rec.get("confidence", "Medium")}
                </span>
            </div>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 13px; margin-bottom: 16px;'>
                <div>
                    <strong style='color:#a5b4fc;'>Priority:</strong> <span style='font-weight: 700; color: #fb7185;'>{rec.get("priority")}</span>
                </div>
                <div>
                    <strong style='color:#a5b4fc;'>Suggested Channel:</strong> <span style='font-weight: 700; color: #fbbf24;'>{rec.get("suggested_channel")}</span>
                </div>
            </div>
            <div style='border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;'>
                <p style='margin: 0 0 6px 0; color:#818cf8; font-weight: 600;'>Summary / Résumé</p>
                <p style='margin: 0 0 12px 0; font-size:12.5px; color:#cbd5e1;'>🇫🇷 {rec.get("summary_fr")}</p>
                <p style='margin: 0 0 12px 0; font-size:12.5px; color:#cbd5e1;'>🇬🇧 {rec.get("summary_en")}</p>
            </div>
            <div style='border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;'>
                <p style='margin: 0 0 6px 0; color:#818cf8; font-weight: 600;'>Risk Explanation / Explication du Risque</p>
                <p style='margin: 0 0 12px 0; font-size:12.5px; color:#cbd5e1;'>🇫🇷 {rec.get("risk_explanation_fr")}</p>
                <p style='margin: 0 0 12px 0; font-size:12.5px; color:#cbd5e1;'>🇬🇧 {rec.get("risk_explanation_en")}</p>
            </div>
            <div style='border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;'>
                <p style='margin: 0 0 6px 0; color:#34d399; font-weight: 600;'>Recommended Action / Action Recommandée</p>
                <p style='margin: 0 0 12px 0; font-size:12.5px; color:#cbd5e1;'>🇫🇷 {rec.get("recommended_action_fr")}</p>
                <p style='margin: 0 0 12px 0; font-size:12.5px; color:#cbd5e1;'>🇬🇧 {rec.get("recommended_action_en")}</p>
            </div>
            <div style='border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;'>
                <p style='margin: 0 0 6px 0; color:#fbbf24; font-weight: 600;'>Message Draft / Projet de Message</p>
                <p style='margin: 0 0 12px 0; font-size:12.5px; color:#cbd5e1; font-style: italic;'>🇫🇷 "{rec.get("message_draft_fr")}"</p>
                <p style='margin: 0 0 12px 0; font-size:12.5px; color:#cbd5e1; font-style: italic;'>🇬🇧 "{rec.get("message_draft_en")}"</p>
            </div>
            <div style='border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;'>
                <p style='margin: 0 0 6px 0; color:#cbd5e1; font-weight: 600;'>Admin Guidance / Directives Administrateur</p>
                <p style='margin: 0 0 6px 0; font-size:12.5px; color:#94a3b8;'>🇫🇷 {rec.get("admin_guidance_fr")}</p>
                <p style='margin: 0 0 0 0; font-size:12.5px; color:#94a3b8;'>🇬🇧 {rec.get("admin_guidance_en")}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    tab_llm_clv, tab_llm_seg, tab_llm_drift, tab_llm_recs, tab_llm_guide = st.tabs([
        "🚨 CLV Alert Actions",
        "🔀 Segment Transition Actions",
        "📊 Prediction Drift Actions",
        "📂 Generated Recommendations",
        "🤖 Entity Guidance Assistant"
    ])
    
    # Tab 1: CLV Alert Actions
    with tab_llm_clv:
        clv_alerts_df = load_cached_clv_alerts()
        if clv_alerts_df is not None and not clv_alerts_df.empty:
            st.markdown("<p style='font-size:14px; font-weight:700;'>CLV Drop Alerts Available</p>", unsafe_allow_html=True)
            st.dataframe(clv_alerts_df, width="stretch", hide_index=True)
            
            selected_alert_entity_id = st.selectbox("Select entity ID to generate action recommendations:", clv_alerts_df['entity_id'].unique(), key="clv_alert_sel")
            
            if st.button("🤖 Generate LLM Recommendation", key="btn_gen_clv_rec"):
                with st.spinner("Analyzing CLV alert context via Local LLM..."):
                    alert_row = clv_alerts_df[clv_alerts_df['entity_id'] == selected_alert_entity_id].iloc[0].to_dict()
                    result = llm_intel.generate_llm_action_for_clv_alert(alert_row)
                    render_recommendation_card(result)
                    st.success("✅ Recommendation generated and saved in PostgreSQL!")
        else:
            st.info("Not enough historical records yet. Simulate more events to activate this analysis.")
            
    # Tab 2: Segment Transition Actions
    with tab_llm_seg:
        transitions_df = load_cached_segment_transitions()
        if transitions_df is not None and not transitions_df.empty:
            st.markdown("<p style='font-size:14px; font-weight:700;'>Cohort Segment Transitions Available</p>", unsafe_allow_html=True)
            st.dataframe(transitions_df, width="stretch", hide_index=True)
            
            selected_trans_entity_id = st.selectbox("Select entity ID to analyze transitions:", transitions_df['entity_id'].unique(), key="trans_alert_sel")
            
            if st.button("🤖 Generate LLM Transition Recommendation", key="btn_gen_seg_rec"):
                with st.spinner("Analyzing segment transition history via Local LLM..."):
                    trans_row = transitions_df[transitions_df['entity_id'] == selected_trans_entity_id].iloc[0].to_dict()
                    result = llm_intel.generate_llm_action_for_segment_transition(trans_row)
                    render_recommendation_card(result)
                    st.success("✅ Recommendation generated and saved in PostgreSQL!")
        else:
            st.info("Not enough historical records yet. Simulate more events to activate this analysis.")
            
    # Tab 3: Prediction Drift Actions
    with tab_llm_drift:
        drift_df = load_cached_prediction_drift()
        if drift_df is not None and not drift_df.empty:
            st.markdown("<p style='font-size:14px; font-weight:700;'>Prediction Drift Distributions</p>", unsafe_allow_html=True)
            st.dataframe(drift_df, width="stretch", hide_index=True)
            
            selected_drift_class = st.selectbox("Select class to generate drift interpretation:", drift_df['dynamic_class'].unique(), key="drift_alert_sel")
            
            if st.button("🤖 Generate LLM Drift Analysis", key="btn_gen_drift_rec"):
                with st.spinner("Analyzing model prediction distribution drift via Local LLM..."):
                    drift_row = drift_df[drift_df['dynamic_class'] == selected_drift_class].iloc[0].to_dict()
                    result = llm_intel.generate_llm_action_for_prediction_drift(drift_row)
                    render_recommendation_card(result)
                    st.success("✅ Prediction drift recommendation generated and saved in PostgreSQL!")
        else:
            st.info("Not enough historical records yet. Simulate more events to activate this analysis.")
            
    # Tab 4: Generated Recommendations
    with tab_llm_recs:
        recs = action_repo.get_llm_action_recommendations(limit=100)
        if recs:
            recs_df = pd.DataFrame(recs)
            # Reorder for display
            display_cols = ["id", "entity_id", "alert_type", "priority", "status", "suggested_channel", "confidence", "created_at"]
            st.dataframe(recs_df[display_cols], width="stretch", hide_index=True)
            
            st.markdown("<p style='font-size:14px; font-weight:700;'>Update Recommendation Status</p>", unsafe_allow_html=True)
            col_rec_id, col_status, col_act = st.columns(3)
            with col_rec_id:
                selected_rec_id = st.selectbox("Select Recommendation ID:", recs_df['id'].unique(), key="rec_id_sel")
            with col_status:
                new_status = st.selectbox("Select New Status:", ["Pending", "In Progress", "Resolved", "Ignored"], key="status_sel")
            with col_act:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("Update Status", key="btn_update_rec_status"):
                    action_repo.update_llm_action_status(selected_rec_id, new_status)
                    st.success(f"✅ Status updated to '{new_status}' successfully!")
                    st.rerun()
            
            # Show details card of selected recommendation
            selected_rec_data = next((r for r in recs if r['id'] == selected_rec_id), None)
            if selected_rec_data:
                st.markdown(f"**Detailed Recommendation Details (ID: {selected_rec_id})**")
                render_recommendation_card(selected_rec_data)
        else:
            st.info("No recommendations have been generated or saved in PostgreSQL yet.")
            
    # Tab 5: Entity Guidance Assistant
    with tab_llm_guide:
        if df is not None and not df.empty:
            st.markdown("<p style='font-size:14px; font-weight:700;'>Generate Customer Guidance Summary</p>", unsafe_allow_html=True)
            selected_guide_entity_id = st.selectbox("Select Customer Entity ID:", sorted(df['entity_id'].dropna().unique()), key="guide_sel")
            
            if st.button("🤖 Generate Customer Guidance Summary", key="btn_gen_guide"):
                with st.spinner("Analyzing complete customer profile and history via Local LLM..."):
                    result = llm_intel.generate_entity_guidance(selected_guide_entity_id)
                    render_recommendation_card(result)
                    st.success("✅ Guidance generated successfully!")
        else:
            st.info("No customers loaded.")
            
    # 6. Model Registry
    st.markdown("<div class='section-header'><span class='icon'>📦</span><span class='title'>Model Registry Lineage Tracking</span></div>", unsafe_allow_html=True)
    registry_df = db_metrics.get_model_registry()


    if not registry_df.empty:
        st.dataframe(registry_df, width="stretch", hide_index=True)
    else:
        st.warning("⚠️ **Model Registry is Empty**: No active model artifact records found in PostgreSQL. Please run the Excel-to-PostgreSQL migration tool to populate active model registry items.")

