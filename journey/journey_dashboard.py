import json
import streamlit as st
import pandas as pd
from ui.layout import render_page_header, section_header_html
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
    run_service_recovery_step,
    prepare_full_demo_entity,
    execute_normalized_journey_plan,
    generate_llm_journey_explanation
)
from journey.llm_journey_planner import generate_llm_journey_plan
from journey.journey_plan_validator import validate_llm_journey_plan
from journey.journey_readiness_validator import validate_journey_entity_state
from journey.journey_tree import (
    render_journey_tree_mermaid,
    render_journey_tree_html,
    build_step_card,
    get_stage_icon
)

def render_journey_dashboard(df_data=None, df_history=None):
    """
    Renders the Digital Twin Journey Tree Simulator Dashboard (Phase 8.7).
    """
    render_page_header(
        "Digital Twin Journey Tree Simulator",
        "Guided lifecycle generator & LLM-assisted journey scenario planner for demo preparation and multi-agent supervision.",
        icon="Journey",
        badge="Phase 8.7 Active",
    )

    # 1. Excel Fallback Mode Check
    if not is_postgres_available():
        st.warning("**Journey Simulator with historical tracking requires PostgreSQL.**")
        st.info("The platform is currently running in **Excel Fallback Mode**. Switch to `OSMOS_STORAGE_BACKEND=postgres` to enable full scenario persistence, step-by-step tree rendering, and historical audit logs.")
        return

    # 2. Historical Scenario Selection
    all_scenarios = get_journey_scenarios(limit=50)
    selected_scenario_id = None
    
    if all_scenarios:
        scen_options = {}
        for s in all_scenarios:
            s_id = s["scenario_id"]
            created = s.get("created_at")
            created_str = created.strftime("%Y-%m-%d %H:%M:%S") if hasattr(created, "strftime") else str(created)[:19]
            status_badge = s.get("status", "Draft")
            label = f"Scenario #{s_id} — {s.get('scenario_name', 'Journey Scenario')} | Entity [{s.get('entity_id', 'P_DEMO_001')}] | Status: {status_badge} | {created_str}"
            scen_options[label] = s_id

        sel_col1, sel_col2 = st.columns([3, 1])
        with sel_col1:
            selected_label = st.selectbox(
                "Select Active or Historical Journey Scenario:",
                options=list(scen_options.keys()),
                index=0,
                key="sb_journey_scenario_select",
                help="Select any scenario run to view its 5-stage lifecycle tree, dynamic metrics, and historical steps."
            )
            selected_scenario_id = scen_options[selected_label]
        with sel_col2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Delete Selected", key="btn_del_selected_scen"):
                if selected_scenario_id:
                    delete_journey_scenario(selected_scenario_id)
                    st.success(f"Scenario #{selected_scenario_id} deleted!")
                    st.rerun()

    scenario_id = selected_scenario_id
    if not scenario_id and all_scenarios:
        scenario_id = all_scenarios[0]["scenario_id"]

    st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)

    # ── SECTION A: Demo Entity Preparation ──
    st.markdown(section_header_html("Section A: Demo Entity Preparation", "Journey Controls"), unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        if st.button("Create / Reset Demo Entity", key="btn_reset_demo", help="Resets P_DEMO_001 to clean prospect state with low churn risk."):
            with st.spinner("Resetting P_DEMO_001 as clean Prospect..."):
                scen_id = reset_demo_journey(DEMO_ENTITY_ID)
                st.success(f"P_DEMO_001 reset (Scenario #{scen_id})!")
                st.rerun()

    with c2:
        if st.button("Run Next Step", key="btn_next_step", help="Advances P_DEMO_001 by 1 stage in the lifecycle."):
            if not scenario_id:
                scenario_id = reset_demo_journey(DEMO_ENTITY_ID)
            with st.spinner("Executing next journey stage..."):
                step = run_next_journey_step(scenario_id)
                if step and step.get("step_id"):
                    st.success(f"Executed Step {step['step_order']}: {step['stage_name']}!")
                    st.rerun()
                else:
                    st.info("Journey scenario completed all stages!")

    with c3:
        if st.button("Run Full Journey", key="btn_full_journey", help="Runs stages 1 to 5 in sequence."):
            if not scenario_id:
                scenario_id = reset_demo_journey(DEMO_ENTITY_ID)
            with st.spinner("Executing full 5-stage lifecycle journey..."):
                steps = run_full_journey(scenario_id, use_llm=False)
                if steps:
                    st.success(f"Executed {len(steps)} journey stages!")
                    st.rerun()

    with c4:
        if st.button("Prepare Full Demo Entity", type="primary", key="btn_prepare_full_demo", help="One-click preparation: resets and executes full deterministic journey."):
            with st.spinner("Preparing full demo entity P_DEMO_001..."):
                res = prepare_full_demo_entity(DEMO_ENTITY_ID)
                st.success(f"Demo Entity Prepared! ({res['steps_executed']} stages executed, Readiness: {res['readiness']['readiness_status']})")
                st.rerun()

    with c5:
        if st.button("Run Service Recovery Step", key="btn_service_recovery", help="Executes Stage 6 optional retention outreach step."):
            if not scenario_id:
                scenario_id = reset_demo_journey(DEMO_ENTITY_ID)
            with st.spinner("Executing Stage 6 Service Recovery Step..."):
                step = run_service_recovery_step(scenario_id)
                if step:
                    st.success("Executed Stage 6 Service Recovery Step!")
                    st.rerun()

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── SECTION B: LLM-Assisted Journey Scenario Planner ──
    st.markdown(section_header_html("Section B: LLM-Assisted Journey Scenario Planner", "LLM Assistant"), unsafe_allow_html=True)
    st.caption("The LLM proposes a structured scenario plan. OSMOS validates it deterministically. Admin approval is required before execution.")

    lcol1, lcol2, lcol3 = st.columns(3)
    with lcol1:
        if st.button("Generate LLM Journey Plan", key="btn_gen_llm_plan"):
            with st.spinner("Generating structured journey proposal via LLM..."):
                proposal = generate_llm_journey_plan(DEMO_ENTITY_ID)
                st.session_state["llm_journey_plan_proposal"] = proposal
                st.session_state["llm_journey_plan_validation"] = None
                st.success("Generated LLM Journey Plan Proposal!")

    with lcol2:
        proposal = st.session_state.get("llm_journey_plan_proposal")
        if st.button("Validate Journey Plan", key="btn_val_llm_plan", disabled=(not proposal)):
            if proposal:
                val = validate_llm_journey_plan(proposal, DEMO_ENTITY_ID)
                st.session_state["llm_journey_plan_validation"] = val
                if val["is_valid"]:
                    st.success("Plan Validation Passed!")
                else:
                    st.error(f"Plan Validation Failed: {len(val['errors'])} errors found.")

    with lcol3:
        val = st.session_state.get("llm_journey_plan_validation")
        is_valid = val and val.get("is_valid")
        if st.button("Approve & Apply Journey Plan", type="primary", key="btn_apply_llm_plan", disabled=(not is_valid)):
            if is_valid and val.get("normalized_plan"):
                if not scenario_id:
                    scenario_id = reset_demo_journey(DEMO_ENTITY_ID)
                with st.spinner("Applying approved journey plan to P_DEMO_001..."):
                    res = execute_normalized_journey_plan(scenario_id, val["normalized_plan"])
                    st.success(f"Applied Approved Plan! ({res['steps_executed']} stages applied)")
                    st.session_state["llm_journey_plan_proposal"] = None
                    st.session_state["llm_journey_plan_validation"] = None
                    st.rerun()

    # Display LLM Plan Preview & Validation Details
    proposal = st.session_state.get("llm_journey_plan_proposal")
    val = st.session_state.get("llm_journey_plan_validation")

    if proposal:
        render_llm_journey_plan_preview(proposal, val)

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── SECTION C: Demo Entity Readiness ──
    st.markdown(section_header_html("Section C: Demo Entity Readiness Audit", "Audit Check"), unsafe_allow_html=True)
    readiness = validate_journey_entity_state(DEMO_ENTITY_ID)

    r_status = readiness["readiness_status"]
    r_score = readiness["score_pct"]
    r_summary = readiness["summary"]

    if r_status == "Ready for presentation":
        st.success(f"🎯 **Status: {r_status}** ({r_score:.0f}% Readiness Score)")
    elif r_status == "Partially ready":
        st.warning(f"⚠️ **Status: {r_status}** ({r_score:.0f}% Readiness Score)")
    else:
        st.error(f"❌ **Status: {r_status}** ({r_score:.0f}% Readiness Score)")

    st.caption(r_summary)

    with st.expander("Detailed Readiness Check Checklist", expanded=False):
        chk_df = pd.DataFrame(readiness["checks"])
        st.dataframe(chk_df, use_container_width=True)

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── SECTION D: Final Demo State ──
    st.markdown(section_header_html("Section D: Final Demo Entity State (P_DEMO_001)", "Digital Twin Snapshot"), unsafe_allow_html=True)
    profile = build_digital_twin_profile(DEMO_ENTITY_ID)
    identity = profile.get("identity", {})
    scores = profile.get("scores", {})
    predictions = profile.get("predictions", {})
    persona_ctx = profile.get("persona_context", {})

    steps = get_journey_steps(scenario_id) if scenario_id else []

    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Entity Type", identity.get("entity_type", "Prospect"))
    sc2.metric("Dynamic Class", predictions.get("dynamic_class", "Cold Prospect"))
    sc3.metric("Customer Segment", persona_ctx.get("customer_segment", "Prospect"))
    sc4.metric("Customer Persona", persona_ctx.get("customer_persona", "New Explorer"))

    sc5, sc6, sc7, sc8 = st.columns(4)
    sc5.metric("CLV Amount (MAD)", f"{predictions.get('predicted_clv_amount_mad', 0.0):.2f} MAD")
    sc6.metric("RFM-ES Score", f"{scores.get('rfm_score_raw', 0.15):.2f}")
    sc7.metric("Churn Risk Score", f"{scores.get('churn_risk_raw', 0.15):.2f}")
    sc8.metric("Executed Steps", f"{len(steps)} Stages")

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── SECTION E: Presentation Tip ──
    st.info("💡 **Presentation Tip**: After preparing P_DEMO_001, open **Agent Supervision Center** with Knowledge Memory and Debate Mode enabled to showcase multi-agent consensus and automated executive reporting.")

    # Render Visual Flowchart & Timeline
    st.markdown(section_header_html("Lifecycle Journey Tree Flowchart", "Flowchart"), unsafe_allow_html=True)
    st.markdown(render_journey_tree_html(steps), unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    if steps:
        st.markdown(section_header_html("Step-by-Step Lifecycle Timeline", "History"), unsafe_allow_html=True)
        for step in steps:
            card_html = build_step_card(step)
            if hasattr(st, "html"):
                st.html(card_html)
            else:
                st.markdown(card_html, unsafe_allow_html=True)
