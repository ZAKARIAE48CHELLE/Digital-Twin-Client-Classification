import streamlit as st
import pandas as pd
from admin.database_metrics import is_postgres_available
from digital_twin.digital_twin_builder import build_digital_twin_profile
from journey.journey_repository import (
    get_journey_scenarios,
    get_journey_steps,
    get_latest_scenario_for_entity,
    delete_journey_scenario
)
from journey.journey_runner import (
    DEMO_ENTITY_ID,
    create_demo_entity,
    reset_demo_journey,
    run_next_journey_step,
    run_full_journey,
    generate_llm_journey_explanation
)
from journey.journey_tree import (
    render_journey_tree_mermaid,
    build_step_card,
    get_stage_icon
)

def render_journey_dashboard(df_data=None, df_history=None):
    """
    Renders the Digital Twin Journey Tree Simulator Dashboard (Phase 7.5).
    """
    st.markdown("<h1 style='margin:0; font-size: 30px;'>🗺️ Digital Twin <span style='background: linear-gradient(135deg,#38bdf8,#34d399,#fbbf24); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Journey Tree Simulator</span></h1>", unsafe_allow_html=True)
    st.markdown("Guided demonstration scenario illustrating single-entity Digital Twin evolution through a 5-stage customer lifecycle: **New Prospect ➔ Warm Prospect ➔ New Client ➔ VIP Client ➔ Churn Risk VIP**.")
    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

    # 1. Excel Fallback Mode Check
    if not is_postgres_available():
        st.warning("⚠️ **Journey Simulator with historical tracking requires PostgreSQL.**")
        st.info("The platform is currently running in **Excel Fallback Mode**. Switch to `OSMOS_STORAGE_BACKEND=postgres` to enable full scenario persistence, step-by-step tree rendering, and historical audit logs.")
        st.markdown("""
        ### 📖 Demo Lifecycle Concept:
        1. **1. New Prospect**: Page visits & product views -> `Cold Prospect` -> Persona `New Explorer`.
        2. **2. Warm Prospect**: Email opens, clicks & cart additions -> `Warm Prospect` -> Conversion Probability increases.
        3. **3. New Client**: First purchase completed (1,800 MAD) -> Converts from Prospect to Client (`New Customers` segment).
        4. **4. VIP Client / Premium Loyalist**: Repeat purchases (total > 20,000 MAD) -> `VIP Client` (`High-Value Loyalists` segment, Persona `Premium Loyalist`).
        5. **5. Churn Risk VIP**: Complaint & inactivity -> `At-Risk Client` (`At-Risk Premium Clients` segment, Persona `Silent VIP at Risk`).
        """)
        return

    # 2. Top Controls & Presentation Mode Bar
    top_col1, top_col2 = st.columns([3, 1])
    with top_col2:
        presentation_mode = st.checkbox("🎭 Presentation Mode", value=False, key="chk_pres_mode", help="Hides debug metadata and displays large clean presentation cards suitable for demo video recordings.")

    # 3. Scenario & Demo Entity Retrieval
    latest_scen = get_latest_scenario_for_entity(DEMO_ENTITY_ID)
    scenario_id = latest_scen["scenario_id"] if latest_scen else None

    # ── A. Scenario Overview ──
    if not presentation_mode:
        st.markdown("<div class='section-header'><span class='icon'>📋</span><span class='title'>Scenario Overview</span></div>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Demo Entity ID", DEMO_ENTITY_ID)
        m2.metric("Scenario Name", "Prospect to VIP to Churn Risk")
        m3.metric("Scenario ID", f"#{scenario_id}" if scenario_id else "None")
        m4.metric("Status", latest_scen["status"] if latest_scen else "Not Started")

    st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)

    # ── B. Control Actions ──
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("🔄 Reset Demo Entity", key="btn_reset_demo", help="Re-initializes P_DEMO_001 as a Cold Prospect and creates a fresh scenario."):
            with st.spinner("Initializing P_DEMO_001 as Cold Prospect..."):
                scen_id = reset_demo_journey(DEMO_ENTITY_ID)
                st.success(f"Initialized P_DEMO_001 (Scenario #{scen_id})!")
                st.rerun()

    with c2:
        if st.button("▶️ Run Next Step", key="btn_next_step", help="Advances P_DEMO_001 by 1 stage in the lifecycle."):
            if not scenario_id:
                scenario_id = reset_demo_journey(DEMO_ENTITY_ID)
            with st.spinner("Executing next journey stage..."):
                step = run_next_journey_step(scenario_id)
                if step:
                    st.success(f"Executed Step {step['step_order']}: {step['stage_name']}!")
                    st.rerun()
                else:
                    st.info("Journey scenario is already complete!")

    with c3:
        if st.button("🚀 Run Full Journey", type="primary", key="btn_full_journey", help="Runs all 5 stages in sequence."):
            if not scenario_id:
                scenario_id = reset_demo_journey(DEMO_ENTITY_ID)
            with st.spinner("Executing full 5-stage lifecycle journey..."):
                steps = run_full_journey(scenario_id, use_llm=False)
                st.success(f"Successfully executed {len(steps)} journey stages!")
                st.rerun()

    with c4:
        if st.button("🤖 Generate LLM Explanations", key="btn_llm_journey", help="Optional button-triggered local LLM cognitive explanations for all steps."):
            if scenario_id:
                steps = get_journey_steps(scenario_id)
                if steps:
                    with st.spinner("Generating LLM explanations via Local LLM..."):
                        for s in steps:
                            generate_llm_journey_explanation(s)
                        st.success("Generated LLM explanations for all steps!")
                        st.rerun()
                else:
                    st.warning("No steps executed yet. Run at least one step first.")
            else:
                st.warning("No scenario active.")

    with c5:
        if st.button("🗑️ Clear Scenario", key="btn_clear_scen", help="Deletes current scenario results."):
            if scenario_id:
                delete_journey_scenario(scenario_id)
                st.success("Scenario cleared.")
                st.rerun()

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # Fetch steps
    steps = get_journey_steps(scenario_id) if scenario_id else []

    # ── C. Journey Tree Visual Flowchart ──
    st.markdown("<div class='section-header'><span class='icon'>🌳</span><span class='title'>Digital Twin Lifecycle Journey Tree</span></div>", unsafe_allow_html=True)
    
    mermaid_code = render_journey_tree_mermaid(steps)
    try:
        st.markdown(f"```mermaid\n{mermaid_code}\n```")
    except Exception:
        pass

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # ── D. Step-by-Step Timeline ──
    st.markdown("<div class='section-header'><span class='icon'>📜</span><span class='title'>Step-by-Step Lifecycle Progression Timeline</span></div>", unsafe_allow_html=True)
    if steps:
        for step in steps:
            card_html = build_step_card(step)
            st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.info("No journey steps executed yet. Click **'▶️ Run Next Step'** or **'🚀 Run Full Journey'** above to start the demo.")

    # ── E. Current Digital Twin Snapshot Card ──
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'><span class='icon'>🧬</span><span class='title'>Current Digital Twin Snapshot (P_DEMO_001)</span></div>", unsafe_allow_html=True)
    
    profile = build_digital_twin_profile(DEMO_ENTITY_ID)
    identity = profile.get("identity", {})
    scores = profile.get("scores", {})
    predictions = profile.get("predictions", {})
    persona_ctx = profile.get("persona_context", {})
    
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Entity Type", identity.get("entity_type", "Prospect"))
    sc2.metric("Dynamic Class", predictions.get("dynamic_class", "Cold Prospect"))
    sc3.metric("Customer Segment", persona_ctx.get("customer_segment", "Prospect"))
    sc4.metric("Persona Blueprint", persona_ctx.get("customer_persona", "New Explorer"))
    
    sc5, sc6, sc7, sc8 = st.columns(4)
    sc5.metric("CLV Amount (MAD)", f"{predictions.get('predicted_clv_amount_mad', 0.0):.2f} MAD")
    sc6.metric("RFM-ES Score", f"{scores.get('rfm_score_raw', 0.15):.2f}")
    sc7.metric("Churn Risk Score", f"{scores.get('churn_risk_raw', 0.10):.2f}")
    sc8.metric("Decision Priority", f"{scores.get('priority_score_raw', 0.30):.2f}")
