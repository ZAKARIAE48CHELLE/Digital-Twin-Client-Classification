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
    st.dataframe(t_df, use_container_width=True, hide_index=True)
    
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
        st.dataframe(db_metrics.get_latest_events(), use_container_width=True)
    with tab2:
        st.dataframe(db_metrics.get_latest_classification_predictions(), use_container_width=True)
    with tab3:
        st.dataframe(db_metrics.get_latest_clv_predictions(), use_container_width=True)
    with tab4:
        st.dataframe(db_metrics.get_latest_rfm_scores(), use_container_width=True)
    with tab5:
        st.dataframe(db_metrics.get_latest_customer_segments(), use_container_width=True)
    with tab6:
        st.dataframe(db_metrics.get_audit_logs(), use_container_width=True)
        
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
                    st.dataframe(timeline_df, use_container_width=True)
                else:
                    st.write("No historical event logs registered for this entity.")
                    
            # Classification
            with st.expander("🤖 Dynamic Classification History"):
                if not class_hist.empty:
                    st.dataframe(class_hist, use_container_width=True)
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
                    st.dataframe(clv_hist, use_container_width=True)
                else:
                    st.write("No CLV prediction history logged.")
                    
            # RFM
            with st.expander("⚡ RFM-ES score Evolution History"):
                if not rfm_hist.empty:
                    st.markdown("<p style='font-size:11px; text-align:center;'>RFM Score Evolution Over Time</p>", unsafe_allow_html=True)
                    st.line_chart(rfm_hist.set_index("calculated_at")["rfm_score"], color="#ec4899")
                    st.dataframe(rfm_hist, use_container_width=True)
                else:
                    st.write("No RFMscore history logged.")
                    
            # Segments
            with st.expander("👥 Cohort Segments & Persona Transition History"):
                if not seg_hist.empty:
                    st.dataframe(seg_hist, use_container_width=True)
                else:
                    st.write("No customer segment/persona assignments logged.")
                    
    # 6. Model Registry
    st.markdown("<div class='section-header'><span class='icon'>📦</span><span class='title'>Model Registry Lineage Tracking</span></div>", unsafe_allow_html=True)
    registry_df = db_metrics.get_model_registry()
    if not registry_df.empty:
        st.dataframe(registry_df, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ **Model Registry is Empty**: No active model artifact records found in PostgreSQL. Please run the Excel-to-PostgreSQL migration tool to populate active model registry items.")
