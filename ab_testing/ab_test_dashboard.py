"""
OSMOS A/B Test Simulator Dashboard (Phase 8.8)
==============================================
Interactive Streamlit user interface for formulating A/B testing questions,
generating or defining variants, running Digital Twin response simulations,
comparing variant metrics, and executing human-supervised governance actions.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from ui.icons import icon_html
from ui.layout import render_page_header, section_header_html
import ab_testing.ab_test_repository as ab_repo
import ab_testing.ab_test_variant_generator as variant_gen
import ab_testing.ab_test_validator as ab_val
import ab_testing.ab_test_evaluator as ab_eval
from ab_testing.ab_test_schemas import ABExperiment, ABVariant


def render_ab_test_dashboard(df: pd.DataFrame, history_df: pd.DataFrame):
    render_page_header(
        "A/B Test & Digital Twin Response Simulator",
        "Formulate A/B testing questions, generate campaign variants, and simulate Digital Twin behavioral reactions.",
        icon="Experiment",
        badge="Phase 8.8",
    )

    if df is None or df.empty:
        st.warning("No customer entity records available. Please load entities first.")
        return

    # --------------------------------------------------------
    # SECTION A: Experiment Setup & Entity Selection
    # --------------------------------------------------------
    st.markdown(section_header_html("1. A/B Experiment Setup", "Experiment"), unsafe_allow_html=True)

    col_ent, col_q = st.columns([3, 7])

    with col_ent:
        ent_list = sorted(df["entity_id"].dropna().unique())
        default_idx = ent_list.index("P_DEMO_001") if "P_DEMO_001" in ent_list else 0
        selected_entity_id = st.selectbox(
            "Select Customer Entity ID:",
            ent_list,
            index=default_idx,
            key="ab_sel_entity_id"
        )

        # Entity State Summary Card
        ent_row = df[df["entity_id"] == selected_entity_id].iloc[0].to_dict()
        st.markdown(f"""
        <div style='background: rgba(129,140,248,0.06); border: 1px solid rgba(129,140,248,0.2); 
                    border-radius: 10px; padding: 14px; margin-top: 10px;'>
            <div style='font-size:13px; font-weight:700; color:#a5b4fc;'>Digital Twin Profile Overview</div>
            <div style='font-size:11.5px; color:#cbd5e1; margin-top:6px; display:grid; grid-template-columns: 1fr 1fr; gap:6px;'>
                <div>Type: <strong>{ent_row.get("entity_type", "Client")}</strong></div>
                <div>Class: <strong style='color:#34d399;'>{ent_row.get("dynamic_class", "N/A")}</strong></div>
                <div>Segment: <strong style='color:#818cf8;'>{ent_row.get("customer_segment", "N/A")}</strong></div>
                <div>Persona: <strong style='color:#a78bfa;'>{ent_row.get("customer_persona", "N/A")}</strong></div>
                <div>Churn Risk: <strong style='color:#fb7185;'>{float(ent_row.get("churn_risk_score", 0.0)):.2f}</strong></div>
                <div>CLV: <strong style='color:#fbbf24;'>{float(ent_row.get("predicted_clv_amount_mad", 0.0)):.0f} MAD</strong></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_q:
        preset_questions = [
            "Which offer is better for this at-risk client?",
            "Should we use a discount or a service recovery apology?",
            "Which message can convert this warm prospect?",
            "Which campaign can reactivate this dormant client?",
            "Which upsell proposal is safest for this VIP client?"
        ]

        preset_choice = st.selectbox(
            "Select Preset Question Example (or write custom):",
            ["Custom Question..."] + preset_questions,
            key="ab_preset_choice"
        )
        default_q_text = preset_choice if preset_choice != "Custom Question..." else "Should we use a discount or a service recovery apology?"

        admin_question = st.text_area(
            "Administrator Business Question:",
            value=default_q_text,
            height=70,
            key="ab_admin_question"
        )

        col_opt1, col_opt2, col_opt3 = st.columns(3)
        with col_opt1:
            objective = st.selectbox(
                "Strategic Objective:",
                ["retention", "conversion", "upsell", "reactivation", "complaint_recovery", "engagement"],
                key="ab_objective"
            )
        with col_opt2:
            channel = st.selectbox(
                "Target Channel:",
                ["email", "sms", "phone", "web_notification", "simulated_only"],
                key="ab_channel"
            )
        with col_opt3:
            num_vars = st.radio(
                "Number of Variants:",
                ["A/B (2 Variants)", "A/B/C (3 Variants)"],
                horizontal=True,
                key="ab_num_vars"
            )
            variant_count = 3 if "3" in num_vars else 2

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # SECTION B: Variant Definition & LLM Generator
    # --------------------------------------------------------
    st.markdown(section_header_html("2. Campaign Variant Definition", "Campaign"), unsafe_allow_html=True)

    col_gen, col_info = st.columns([3.5, 6.5])
    with col_gen:
        gen_llm_btn = st.button("🤖 Generate A/B Variants with LLM", width="stretch", type="secondary", key="btn_gen_ab_llm")

    # Initialize experiment name if missing
    if "ab_test_experiment_name" not in st.session_state:
        st.session_state["ab_test_experiment_name"] = f"A/B Test ({objective.title()}): {selected_entity_id}"
    if "ab_test_is_llm_generated" not in st.session_state:
        st.session_state["ab_test_is_llm_generated"] = False

    # Handle LLM Variant Generation Button Click
    if gen_llm_btn:
        with st.spinner("Generating candidate campaign variants via Local LLM..."):
            gen_vars, exp_name, status_code = variant_gen.generate_llm_ab_variants(
                admin_question, objective, ent_row, channel=channel, num_variants=variant_count
            )
            st.session_state["ab_test_variants"] = gen_vars
            st.session_state["ab_test_experiment_name"] = exp_name
            st.session_state["ab_test_is_llm_generated"] = (status_code == "llm_success_valid")

            # Update widget session_state keys for instant UI input reflection
            for i, v in enumerate(gen_vars):
                st.session_state[f"ab_v_title_{i}"] = v.variant_title
                st.session_state[f"ab_v_msg_{i}"] = v.message_text
                st.session_state[f"ab_v_offer_{i}"] = v.offer_type
                st.session_state[f"ab_v_inc_{i}"] = float(v.incentive_value)
                st.session_state[f"ab_v_tone_{i}"] = v.tone
                st.session_state[f"ab_v_cta_{i}"] = v.call_to_action

            if status_code == "llm_success_valid":
                st.success("LLM variants generated successfully.")
            else:
                st.warning("LLM output was incomplete. Safe deterministic variants were loaded.")

    # Initialize or Adjust Session State Variants matching requested variant_count
    current_stored = st.session_state.get("ab_test_variants", [])
    if not current_stored or len(current_stored) != variant_count:
        fallback_list = variant_gen._build_fallback_variants(
            admin_question, objective, selected_entity_id,
            ent_row.get("customer_segment", "Standard Active Clients"),
            ent_row.get("customer_persona", "Regular Buyer"),
            channel=channel
        )[:variant_count]
        st.session_state["ab_test_variants"] = fallback_list

        for i, v in enumerate(fallback_list):
            if f"ab_v_title_{i}" not in st.session_state:
                st.session_state[f"ab_v_title_{i}"] = v.variant_title
            if f"ab_v_msg_{i}" not in st.session_state:
                st.session_state[f"ab_v_msg_{i}"] = v.message_text
            if f"ab_v_offer_{i}" not in st.session_state:
                st.session_state[f"ab_v_offer_{i}"] = v.offer_type
            if f"ab_v_inc_{i}" not in st.session_state:
                st.session_state[f"ab_v_inc_{i}"] = float(v.incentive_value)
            if f"ab_v_tone_{i}" not in st.session_state:
                st.session_state[f"ab_v_tone_{i}"] = v.tone
            if f"ab_v_cta_{i}" not in st.session_state:
                st.session_state[f"ab_v_cta_{i}"] = v.call_to_action

    # Render Editable Variant Input Fields (Dynamic Count: 2 or 3)
    variant_labels = ["A", "B", "C"][:variant_count]
    var_cols = st.columns(variant_count)
    edited_variants: List[ABVariant] = []

    for idx, lbl in enumerate(variant_labels):
        stored_v = st.session_state["ab_test_variants"][idx] if idx < len(st.session_state["ab_test_variants"]) else None

        with var_cols[idx]:
            st.markdown(f"**Variant {lbl} Configuration**")

            # Input Title
            v_title = st.text_input(
                f"Variant {lbl} Title:",
                key=f"ab_v_title_{idx}"
            )

            # Input Message Text
            v_msg = st.text_area(
                f"Variant {lbl} Message Text:",
                height=100,
                key=f"ab_v_msg_{idx}"
            )

            c1, c2 = st.columns(2)
            with c1:
                if f"ab_v_offer_{idx}" not in st.session_state or st.session_state[f"ab_v_offer_{idx}"] not in ab_val.ALLOWED_OFFER_TYPES:
                    st.session_state[f"ab_v_offer_{idx}"] = stored_v.offer_type if stored_v else "none"
                v_offer = st.selectbox(
                    f"Offer Type ({lbl}):",
                    ab_val.ALLOWED_OFFER_TYPES,
                    key=f"ab_v_offer_{idx}"
                )
            with c2:
                if f"ab_v_inc_{idx}" not in st.session_state:
                    st.session_state[f"ab_v_inc_{idx}"] = float(stored_v.incentive_value) if stored_v else 0.0
                v_inc = st.number_input(
                    f"Incentive Value ({lbl}):",
                    min_value=0.0,
                    max_value=100.0,
                    key=f"ab_v_inc_{idx}"
                )

            c3, c4 = st.columns(2)
            tone_options = ["commercial", "empathetic", "informational", "exclusive"]
            with c3:
                if f"ab_v_tone_{idx}" not in st.session_state or st.session_state[f"ab_v_tone_{idx}"] not in tone_options:
                    st.session_state[f"ab_v_tone_{idx}"] = stored_v.tone if stored_v else "commercial"
                v_tone = st.selectbox(
                    f"Tone ({lbl}):",
                    tone_options,
                    key=f"ab_v_tone_{idx}"
                )
            with c4:
                v_cta = st.text_input(
                    f"Call to Action ({lbl}):",
                    key=f"ab_v_cta_{idx}"
                )

            edited_var = ABVariant(
                variant_label=lbl,
                variant_title=v_title or f"Strategy {lbl}",
                message_text=v_msg or f"Variant {lbl} communication message.",
                offer_type=v_offer,
                incentive_value=float(v_inc),
                channel=channel,
                tone=v_tone,
                call_to_action=v_cta or "Click Here",
                expected_behavior=stored_v.expected_behavior if stored_v else "Customer engagement"
            )
            edited_variants.append(edited_var)

    # Persist current edited variants into session state
    st.session_state["ab_test_variants"] = edited_variants

    # Live Deterministic Validation Check
    val_check = ab_val.validate_ab_variants(edited_variants, ent_row, objective=objective)
    st.session_state["ab_test_validation_status"] = val_check

    if val_check["errors"]:
        for err in val_check["errors"]:
            st.error(f"Validation Error: {err}")
    elif val_check["warnings"]:
        for warn in val_check["warnings"]:
            st.warning(f"Validation Warning: {warn}")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # SECTION C: Digital Twin Response Simulation
    # --------------------------------------------------------
    st.markdown(section_header_html("3. Digital Twin Response Simulation", "Search"), unsafe_allow_html=True)

    col_sim_btn, col_spacer2 = st.columns([3.5, 6.5])
    with col_sim_btn:
        run_sim_btn = st.button("🔬 Run Digital Twin Response Simulation", width="stretch", type="primary", key="btn_run_ab_sim")

    if run_sim_btn:
        if not val_check["is_valid"]:
            st.error("Cannot run simulation while validation errors exist. Please fix errors above.")
        else:
            with st.spinner("Simulating Digital Twin behavioral responses across all variants..."):
                experiment_name = st.session_state.get(
                    "ab_test_experiment_name", f"A/B Test ({objective.title()}): {selected_entity_id}"
                )
                experiment_obj = ABExperiment(
                    entity_id=selected_entity_id,
                    experiment_name=experiment_name,
                    admin_question=admin_question,
                    objective=objective,
                    target_segment=ent_row.get("customer_segment"),
                    target_persona=ent_row.get("customer_persona"),
                    status="Simulated",
                    llm_generated=st.session_state.get("ab_test_is_llm_generated", False)
                )

                eval_result = ab_eval.evaluate_ab_experiment(experiment_obj, edited_variants, ent_row)
                st.session_state["last_ab_eval_result"] = eval_result
                st.success("Digital Twin Response Simulation completed successfully!")

    # Render Simulation Results Card
    if "last_ab_eval_result" in st.session_state:
        res: ab_eval.ABEvaluationResult = st.session_state["last_ab_eval_result"]
        rec = res.recommendation
        responses = res.responses

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # Winner Banner
        st.markdown(f"""
        <div style='background: rgba(52,211,153,0.08); border: 1.5px solid #34d399; 
                    border-radius: 12px; padding: 18px; margin-bottom: 16px;'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h4 style='margin:0; color:#34d399;'>🏆 Winning Variant: Variant {rec.winning_variant_label}</h4>
                <span style='background:rgba(52,211,153,0.2); color:#34d399; padding:4px 10px; border-radius:6px; font-weight:700; font-size:12px;'>
                    Confidence: {rec.confidence_score*100:.0f}%
                </span>
            </div>
            <p style='margin:10px 0 6px 0; color:#cbd5e1; font-size:13.5px;'><strong>Recommendation Summary:</strong> {rec.recommendation_summary}</p>
            <p style='margin:0 0 6px 0; color:#94a3b8; font-size:12.5px;'><strong>Decision Reason:</strong> {rec.decision_reason}</p>
            <p style='margin:0; color:#fb7185; font-size:12px;'><strong>Risks & Caveats:</strong> {rec.risk_notes}</p>
        </div>
        """, unsafe_allow_html=True)

        # Variant Metrics Comparison Table
        st.markdown("<p style='font-size:14px; font-weight:700; color:#38bdf8;'>Simulated Response Comparison Table:</p>", unsafe_allow_html=True)

        comp_data = []
        for r in responses:
            v_match = next((v for v in res.variants if v.variant_label == r.variant_label), None)
            comp_data.append({
                "Variant": f"Variant {r.variant_label}",
                "Title": v_match.variant_title if v_match else f"Variant {r.variant_label}",
                "Response Score": r.response_score,
                "Simulated Outcome": r.simulated_response_type,
                "Open %": f"{r.predicted_open_probability*100:.1f}%",
                "Click %": f"{r.predicted_click_probability*100:.1f}%",
                "Conversion %": f"{r.predicted_conversion_probability*100:.1f}%",
                "Complaint %": f"{r.predicted_complaint_probability*100:.1f}%",
                "Churn Delta": f"{r.predicted_churn_delta*100:+.1f}%",
                "CLV Lift": f"+{r.predicted_clv_delta:.0f} MAD",
            })

        comp_df = pd.DataFrame(comp_data)
        st.dataframe(comp_df, width="stretch", hide_index=True)

        # Bar Chart of Response Scores
        chart_df = pd.DataFrame({
            "Variant": [f"Variant {r.variant_label}" for r in responses],
            "Response Score": [r.response_score for r in responses]
        }).set_index("Variant")
        st.bar_chart(chart_df, color="#38bdf8")

        # --------------------------------------------------------
        # SECTION E: Governance Actions
        # --------------------------------------------------------
        st.markdown(section_header_html("4. Governance & Human Approval Actions", "Lock"), unsafe_allow_html=True)

        act_col1, act_col2, act_col3 = st.columns(3)

        with act_col1:
            if st.button("💾 Save A/B Experiment Records", width="stretch", key="btn_save_ab_exp"):
                saved_id = ab_repo.save_ab_experiment(res)
                if saved_id:
                    st.success(f"Saved Experiment #{saved_id} ('{res.experiment.experiment_name}') in PostgreSQL successfully!")

        with act_col2:
            if st.button("📣 Convert Winner to Campaign Draft", width="stretch", key="btn_convert_ab_draft"):
                saved_id = ab_repo.save_ab_experiment(res)
                if saved_id:
                    winning_var_id = next((v.variant_id for v in res.variants if v.variant_label == rec.winning_variant_label), None)
                    draft_id = ab_repo.convert_variant_to_campaign_draft(saved_id, winning_var_id or 1)
                    if draft_id:
                        st.success(f"Converted Variant {rec.winning_variant_label} to Campaign Draft #{draft_id}!")

        with act_col3:
            if st.button("⚡ Apply Response as Event (Admin Approved)", width="stretch", key="btn_apply_ab_event"):
                saved_id = ab_repo.save_ab_experiment(res)
                if saved_id:
                    winning_var_id = next((v.variant_id for v in res.variants if v.variant_label == rec.winning_variant_label), None)
                    evt_id = ab_repo.apply_simulated_response_as_event(saved_id, winning_var_id or 1, selected_entity_id)
                    if evt_id:
                        st.success(f"Applied simulated response event [{evt_id}] to PostgreSQL!")

    # --------------------------------------------------------
    # SECTION F: Experiment History
    # --------------------------------------------------------
    st.markdown(section_header_html("5. Entity A/B Experiment History", "History"), unsafe_allow_html=True)
    history_records = ab_repo.get_ab_experiments_for_entity(selected_entity_id, limit=10)
    if history_records:
        h_df = pd.DataFrame(history_records)
        display_cols = ["experiment_id", "experiment_name", "objective", "winning_label", "winning_title", "confidence_score", "status", "created_at"]
        st.dataframe(h_df[[c for c in display_cols if c in h_df.columns]], width="stretch", hide_index=True)
    else:
        st.info(f"No prior A/B test experiments logged for entity [{selected_entity_id}].")
