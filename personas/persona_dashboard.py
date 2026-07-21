import streamlit as st
import pandas as pd
from personas.persona_library import get_all_personas, seed_default_personas
from admin.database_metrics import is_postgres_available

def render_persona_library_dashboard():
    """Renders the Persona Library Explorer and Management Dashboard."""
    st.markdown("<div class='section-header'><span class='icon'>🎭</span><span class='title'>OSMOS Persona Library Catalog</span></div>", unsafe_allow_html=True)
    
    if not is_postgres_available():
        st.info("ℹ️ **Excel Mode active**: Persona Library persistence requires PostgreSQL. Built-in default personas are currently displayed.")
        
    col_act1, col_act2 = st.columns([1, 4])
    with col_act1:
        if st.button("🌱 Seed Default Personas", key="btn_seed_personas"):
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
        st.markdown("<p style='font-size:16px; font-weight:700;'>Persona Detailed Card Viewer</p>", unsafe_allow_html=True)
        
        seg_list = p_df["segment_name"].unique()
        selected_seg = st.selectbox("Select Cohort Segment to view Persona Blueprint:", seg_list, key="sel_persona_card")
        
        p_row = p_df[p_df["segment_name"] == selected_seg].iloc[0].to_dict()
        
        # Render Detailed Persona Blueprint Card
        st.markdown(f"""<div style='background: rgba(30, 41, 59, 0.7); border: 1.5px solid rgba(129, 140, 248, 0.3); border-radius: 12px; padding: 20px; margin-top: 10px;'>
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
        </div>""", unsafe_allow_html=True)

    else:
        st.warning("No personas registered in catalog.")
