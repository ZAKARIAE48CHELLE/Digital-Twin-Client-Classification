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
from journey.llm_journey_planner import generate_llm_journey_plan, regenerate_llm_journey_plan_with_feedback
from journey.journey_plan_validator import validate_llm_journey_plan
from journey.journey_readiness_validator import validate_journey_entity_state
from journey.journey_tree import (
    render_journey_tree_mermaid,
    render_journey_tree_html,
    build_step_card,
    get_stage_icon
)


def render_llm_journey_plan_preview(proposal: dict, val: dict = None):
    """Renders visual cards, quality score, validation feedback, and JSON preview."""
    if not proposal:
        return

    scenario_name = proposal.get("scenario_name", "Custom Journey Plan")
    entity_id = proposal.get("entity_id", "P_DEMO_001")
    description = proposal.get("description", "LLM Proposed customer lifecycle sequence.")
    stages = proposal.get("stages", [])

    q_score = val.get("quality_score", 0.0) if val else 0.0
    q_label = val.get("quality_label", "Not Audited") if val else "Not Audited"
    is_valid = val.get("is_valid", False) if val else False

    label_colors = {
        "Excellent": ("#4ade80", "rgba(74, 222, 128, 0.15)", "rgba(74, 222, 128, 0.3)"),
        "Acceptable": ("#38bdf8", "rgba(56, 189, 248, 0.15)", "rgba(56, 189, 248, 0.3)"),
        "Weak": ("#fbbf24", "rgba(251, 191, 36, 0.15)", "rgba(251, 191, 36, 0.3)"),
        "Invalid": ("#f87171", "rgba(248, 113, 113, 0.15)", "rgba(248, 113, 113, 0.3)"),
        "Not Audited": ("#94a3b8", "rgba(148, 163, 184, 0.15)", "rgba(148, 163, 184, 0.3)"),
    }
    txt_col, bg_col, border_col = label_colors.get(q_label, label_colors["Not Audited"])

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95));
        border: 1px solid rgba(56, 189, 248, 0.4);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
            <div>
                <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #38bdf8;">🤖 LLM Journey Plan Proposal</span>
                <h3 style="margin: 4px 0 0; color: #f8fafc; font-family: 'Outfit', sans-serif; font-size: 22px; font-weight: 800;">{scenario_name}</h3>
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
                <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 20px; padding: 4px 12px; font-size: 12px; font-weight: 600;">Target: [{entity_id}]</span>
                <span style="background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 20px; padding: 4px 12px; font-size: 12px; font-weight: 600;">{len(stages)} Stages</span>
                <span style="background: {bg_col}; color: {txt_col}; border: 1px solid {border_col}; border-radius: 20px; padding: 4px 14px; font-size: 12px; font-weight: 700;">Score: {q_score:.0f}/100 ({q_label})</span>
            </div>
        </div>
        <p style="color: #94a3b8; font-size: 13.5px; margin: 0; line-height: 1.5;">{description}</p>
    </div>
    """, unsafe_allow_html=True)

    # Validation & Repair Feedback Box
    if val:
        repair_warns = val.get("repair_warnings", [])
        if repair_warns:
            with st.expander("🛠️ Automatic JSON Repairs Applied", expanded=False):
                for rw in repair_warns:
                    st.markdown(f"- 🔧 {rw}")

        if not is_valid:
            st.error(f"❌ **Validator Status: INVALID PLAN** ({len(val.get('errors', []))} Errors) — Click 'Regenerate with Validation Feedback' to fix.")
            for err in val.get("errors", []):
                st.markdown(f"- 🔴 **Error**: {err}")
        else:
            st.success(f"✅ **Validator Status: VALID PLAN** (Quality: **{q_label}**, Score: **{q_score:.0f}/100**) — Ready for Admin Approval.")

        for warn in val.get("warnings", []):
            st.markdown(f"- ⚠️ **Warning**: {warn}")

        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

    event_icons = {
        "page_visit": "🌐",
        "product_view": "👁️",
        "email_open": "✉️",
        "email_click": "🖱️",
        "add_to_cart": "🛒",
        "purchase": "💰",
        "complaint": "⚠️",
        "negative_review": "👎",
        "positive_review": "⭐",
        "inactivity_period": "⏳",
        "social_positive_mention": "👍",
        "social_negative_mention": "🚨",
        "service_recovery_contact": "🤝",
        "retention_offer_sent": "🎁",
    }

    for idx, stage in enumerate(stages, start=1):
        s_name = stage.get("stage_name", f"Stage #{idx}")
        s_goal = stage.get("goal", "")
        events = stage.get("events", [])
        state_chg = stage.get("expected_state_change", {})

        evt_pills = []
        for e in events:
            if isinstance(e, dict):
                e_type = e.get("event_type", "event")
                e_offset = e.get("event_offset_days", 0)
                e_val = e.get("event_value")
            else:
                e_type = str(e)
                e_offset = 0
                e_val = None

            icon = event_icons.get(e_type, "⚡")
            val_str = f" ({e_val:,.0f} MAD)" if e_val is not None else ""
            offset_str = f" (T{e_offset}d)" if e_offset else ""
            evt_pills.append(f"""
                <span style="background: rgba(30, 41, 59, 0.8); color: #e2e8f0; border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 4px 10px; font-size: 12px; font-weight: 500;">
                    {icon} <strong>{e_type}</strong>{val_str}<span style="color: #94a3b8; font-size: 11px;">{offset_str}</span>
                </span>
            """)

        evt_html = "".join(evt_pills) if evt_pills else "<span style='color: #64748b; font-size: 12px;'>No events specified</span>"

        entity_t = state_chg.get("entity_type", "Prospect" if idx < 3 else "Client")
        dyn_class = state_chg.get("dynamic_class", "Cold Prospect")
        segment = state_chg.get("segment", "Prospect")
        persona = state_chg.get("persona", "New Explorer")

        st.markdown(f"""
        <div style="
            background: rgba(15, 23, 42, 0.7);
            border-left: 4px solid #38bdf8;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 14px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #f8fafc; font-size: 16px; font-weight: 700;">{s_name}</h4>
                <span style="background: rgba(56, 189, 248, 0.1); color: #38bdf8; font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 12px;">🎯 {s_goal}</span>
            </div>
            
            <div style="margin-bottom: 12px;">
                <span style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; display: block; margin-bottom: 6px;">Trigger Behavioral Telemetry:</span>
                <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                    {evt_html}
                </div>
            </div>

            <div style="background: rgba(30, 41, 59, 0.5); border-radius: 8px; padding: 10px 14px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
                <div>
                    <span style="font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase;">Entity Type</span>
                    <div style="color: #f1f5f9; font-size: 13px; font-weight: 600;">{entity_t}</div>
                </div>
                <div>
                    <span style="font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase;">Dynamic Class</span>
                    <div style="color: #38bdf8; font-size: 13px; font-weight: 600;">{dyn_class}</div>
                </div>
                <div>
                    <span style="font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase;">Segment</span>
                    <div style="color: #c084fc; font-size: 13px; font-weight: 600;">{segment}</div>
                </div>
                <div>
                    <span style="font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase;">Stable Persona</span>
                    <div style="color: #4ade80; font-size: 13px; font-weight: 600;">{persona}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🔍 View Raw Plan JSON Structure", expanded=False):
        st.json(proposal)


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

    if not is_postgres_available():
        st.warning("**Journey Simulator with historical tracking requires PostgreSQL.**")
        st.info("The platform is currently running in **Excel Fallback Mode**. Switch to `OSMOS_STORAGE_BACKEND=postgres` to enable full scenario persistence, step-by-step tree rendering, and historical audit logs.")
        return

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

    proposal = st.session_state.get("llm_journey_plan_proposal")
    val = st.session_state.get("llm_journey_plan_validation")

    lcol1, lcol2, lcol3, lcol4 = st.columns(4)
    with lcol1:
        if st.button("Generate LLM Journey Plan", key="btn_gen_llm_plan"):
            with st.spinner("Generating structured journey proposal via LLM..."):
                prop = generate_llm_journey_plan(DEMO_ENTITY_ID)
                st.session_state["llm_journey_plan_proposal"] = prop
                st.session_state["llm_journey_plan_validation"] = validate_llm_journey_plan(prop, DEMO_ENTITY_ID)
                st.success("Generated & Validated LLM Journey Plan Proposal!")
                st.rerun()

    with lcol2:
        if st.button("Validate Journey Plan", key="btn_val_llm_plan", disabled=(not proposal)):
            if proposal:
                v = validate_llm_journey_plan(proposal, DEMO_ENTITY_ID)
                st.session_state["llm_journey_plan_validation"] = v
                if v["is_valid"]:
                    st.success("Plan Validation Passed!")
                else:
                    st.error(f"Plan Validation Failed: {len(v['errors'])} errors found.")

    with lcol3:
        can_regen = proposal is not None and val is not None
        if st.button("Regenerate with Feedback", key="btn_regen_llm_plan", disabled=(not can_regen)):
            if proposal and val:
                with st.spinner("Regenerating journey plan using validation feedback..."):
                    re_prop = regenerate_llm_journey_plan_with_feedback(proposal, val, DEMO_ENTITY_ID)
                    st.session_state["llm_journey_plan_proposal"] = re_prop
                    st.session_state["llm_journey_plan_validation"] = validate_llm_journey_plan(re_prop, DEMO_ENTITY_ID)
                    st.success("Regenerated & Re-validated Plan!")
                    st.rerun()

    with lcol4:
        is_valid = val and val.get("is_valid") and val.get("quality_label") != "Invalid"
        if st.button("Approve & Apply Plan", type="primary", key="btn_apply_llm_plan", disabled=(not is_valid)):
            if is_valid and val.get("normalized_plan"):
                if not scenario_id:
                    scenario_id = reset_demo_journey(DEMO_ENTITY_ID)
                with st.spinner("Applying approved journey plan to P_DEMO_001..."):
                    res = execute_normalized_journey_plan(scenario_id, val["normalized_plan"])
                    st.success(f"Applied Approved Plan! ({res['steps_executed']} stages applied)")
                    st.session_state["llm_journey_plan_proposal"] = None
                    st.session_state["llm_journey_plan_validation"] = None
                    st.rerun()

    # Render LLM Plan Preview & Validation Details
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
