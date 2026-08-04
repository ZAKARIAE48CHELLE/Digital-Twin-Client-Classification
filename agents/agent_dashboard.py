"""
OSMOS Multi-Agent Supervision Layer — Agent Dashboard (Phase 8.2)
==================================================================
Streamlit dashboard page for the Agent Supervision Center.
Allows administrators to inspect core customer intelligence and operational
supervision across all 8 specialized agents with System Readiness summaries,
evidence traceability, presentation mode, and button-triggered LLM executive summaries.
"""

import logging
from typing import Optional, List, Dict, Any
import pandas as pd
import streamlit as st

from agents.orchestrator_agent import OrchestratorAgent, run_orchestrated_analysis
from agents.agent_registry import list_agents, CORE_AGENT_IDS, OPERATIONAL_AGENT_IDS
from agents.result_aggregator import compute_system_readiness_summary
from ui.icons import icon_html

logger = logging.getLogger("OSMOS_AGENT_DASHBOARD")


def render_agent_status_badge(status: str) -> str:
    """Renders a color-coded HTML badge for agent status."""
    colors = {
        "OK": ("#10B981", "rgba(16, 185, 129, 0.15)"),
        "Warning": ("#F59E0B", "rgba(245, 158, 11, 0.15)"),
        "Critical": ("#EF4444", "rgba(239, 68, 68, 0.15)"),
        "Insufficient Data": ("#6B7280", "rgba(107, 114, 128, 0.15)"),
        "Error": ("#DC2626", "rgba(220, 38, 38, 0.15)"),
    }
    text_color, bg_color = colors.get(status, ("#60A5FA", "rgba(96, 165, 250, 0.15)"))
    return (
        f'<span style="background-color: {bg_color}; color: {text_color}; '
        f'padding: 4px 10px; border-radius: 9999px; font-weight: 700; font-size: 12px; '
        f'border: 1px solid {text_color}; display: inline-block;">{status}</span>'
    )


def render_agent_dashboard(df: Optional[pd.DataFrame] = None, history_df: Optional[pd.DataFrame] = None):
    """Main rendering entrypoint for the Agent Supervision Center page."""
    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <h1 style="font-size: 28px; font-weight: 800; margin-bottom: 4px; display: flex; align-items: center; gap: 10px;">
                {icon_html('bot')} Agent Supervision Center
            </h1>
            <p style="color: var(--osmos-muted, #94A3B8); font-size: 14px;">
                8-Agent Multi-Agent Intelligent CRM Supervision Layer & Read-Only Next Best Action Engine
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Top Control Bar: Entity Selection & Presentation Mode Toggle
    col_ent, col_mode = st.columns([3, 1])

    available_entities = []
    if df is not None and not df.empty and "entity_id" in df.columns:
        available_entities = sorted(df["entity_id"].dropna().astype(str).unique().tolist())

    if "P_DEMO_001" not in available_entities:
        available_entities.insert(0, "P_DEMO_001")
    if "C00001" not in available_entities:
        available_entities.append("C00001")
    if "P00001" not in available_entities:
        available_entities.append("P00001")

    with col_ent:
        selected_entity = st.selectbox(
            "Select Entity to Inspect:",
            options=available_entities,
            index=0,
            help="Choose a customer or prospect entity for multi-agent supervision.",
        )

    with col_mode:
        st.write("")
        st.write("")
        presentation_mode = st.checkbox("Presentation Mode", value=False, help="Hide raw evidence tables for executive presentation.")

    # Categorized Agent Selection
    st.markdown("##### Agent Selection & Presets")
    preset_col1, preset_col2, preset_col3, _ = st.columns([1.5, 1.5, 1.5, 3.5])

    if "selected_agents_set" not in st.session_state:
        st.session_state["selected_agents_set"] = set(CORE_AGENT_IDS)

    with preset_col1:
        if st.button("Select All (8 Agents)", use_container_width=True):
            st.session_state["selected_agents_set"] = {"digital_twin", "clv", "churn", "persona", "campaign", "journey", "database_audit", "ui_ux"}

    with preset_col2:
        if st.button("Default Core (5 Agents)", use_container_width=True):
            st.session_state["selected_agents_set"] = set(CORE_AGENT_IDS)

    with preset_col3:
        if st.button("Clear Selection", use_container_width=True):
            st.session_state["selected_agents_set"] = set()

    # Category Group 1: Core Customer Intelligence
    st.markdown("**Core Customer Intelligence Agents:**")
    c1, c2, c3, c4 = st.columns(4)
    selected_agent_ids = []

    with c1:
        if st.checkbox("Digital Twin Agent", value="digital_twin" in st.session_state["selected_agents_set"], key="chk_dt"):
            selected_agent_ids.append("digital_twin")
    with c2:
        if st.checkbox("CLV Agent", value="clv" in st.session_state["selected_agents_set"], key="chk_clv"):
            selected_agent_ids.append("clv")
    with c3:
        if st.checkbox("Churn Risk Agent", value="churn" in st.session_state["selected_agents_set"], key="chk_churn"):
            selected_agent_ids.append("churn")
    with c4:
        if st.checkbox("Persona Agent", value="persona" in st.session_state["selected_agents_set"], key="chk_persona"):
            selected_agent_ids.append("persona")

    # Category Group 2: Operational Supervision
    st.markdown("**Operational Supervision Agents:**")
    o1, o2, o3, o4 = st.columns(4)
    with o1:
        if st.checkbox("Campaign Agent", value="campaign" in st.session_state["selected_agents_set"], key="chk_campaign"):
            selected_agent_ids.append("campaign")
    with o2:
        if st.checkbox("Journey Agent", value="journey" in st.session_state["selected_agents_set"], key="chk_journey"):
            selected_agent_ids.append("journey")
    with o3:
        if st.checkbox("Database Audit Agent", value="database_audit" in st.session_state["selected_agents_set"], key="chk_db"):
            selected_agent_ids.append("database_audit")
    with o4:
        if st.checkbox("UI/UX Agent", value="ui_ux" in st.session_state["selected_agents_set"], key="chk_ui"):
            selected_agent_ids.append("ui_ux")

    st.session_state["selected_agents_set"] = set(selected_agent_ids)

    st.write("")
    if st.button("Run Multi-Agent Analysis", type="primary", use_container_width=True):
        with st.spinner(f"Orchestrator building context and executing {len(selected_agent_ids)} agents..."):
            report = run_orchestrated_analysis(
                entity_id=selected_entity,
                df=df,
                history_df=history_df,
                selected_agent_ids=selected_agent_ids,
            )
            st.session_state["agent_supervision_report"] = report
            st.session_state.pop("agent_llm_summary", None)  # Reset previous LLM summary

    # Display Analysis Results if available in session state
    report = st.session_state.get("agent_supervision_report")
    if report and report.entity_id == selected_entity:
        st.markdown("---")

        # Global Status Callout Card
        st.markdown(
            f"""
            <div style="background: var(--osmos-card-bg, #111827); border: 1px solid var(--osmos-border, #334155); 
                        border-radius: 12px; padding: 20px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div>
                        <span style="color: var(--osmos-muted, #94A3B8); font-size: 12px; font-weight: 700; text-transform: uppercase;">
                            Multi-Agent Orchestrator Supervision Report
                        </span>
                        <h3 style="margin: 4px 0 0 0; font-size: 20px; font-weight: 800;">Entity [{report.entity_id}]</h3>
                    </div>
                    <div>
                        {render_agent_status_badge(report.global_status)}
                    </div>
                </div>
                <p style="font-size: 14px; margin-bottom: 16px; color: var(--osmos-text, #F8FAFC); line-height: 1.5;">
                    {report.final_summary}
                </p>
                <div style="background: var(--osmos-bg-soft, #020617); border-left: 4px solid var(--osmos-primary, #60A5FA); 
                            padding: 14px 16px; border-radius: 6px;">
                    <span style="font-size: 11px; font-weight: 800; color: var(--osmos-primary, #60A5FA); text-transform: uppercase; letter-spacing: 0.5px;">
                        Recommended Next Best Action (Read-Only Advice)
                    </span>
                    <p style="margin: 4px 0 0 0; font-size: 15px; font-weight: 700; color: var(--osmos-text, #F8FAFC);">
                        {report.recommended_next_best_action}
                    </p>
                </div>
                <div style="margin-top: 12px; font-size: 12px; color: var(--osmos-muted, #94A3B8); text-align: right;">
                    Global Confidence Score: <strong>{report.confidence_score * 100:.0f}%</strong> | Mode: <strong>Read-Only</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # System Readiness Summary Panel
        agent_outputs_list = [AgentOutput(**d) if isinstance(d, dict) else d for d in report.agent_outputs]
        sys_summary = compute_system_readiness_summary(agent_outputs_list)

        st.markdown("##### System Readiness Summary")
        sr1, sr2, sr3, sr4 = st.columns(4)
        with sr1:
            st.metric("Database Integrity", sys_summary["database_integrity"])
        with sr2:
            st.metric("Journey Readiness", sys_summary["journey_readiness"])
        with sr3:
            st.metric("Campaign Activity", sys_summary["campaign_readiness"])
        with sr4:
            st.metric("Demo Readiness", sys_summary["demo_readiness"])

        # On-Demand LLM Executive Supervision Summary Button
        st.markdown("##### Executive Summary Generation (Button-Triggered Only)")
        col_btn, col_info = st.columns([2, 3])
        with col_btn:
            if st.button("Generate LLM Executive Supervision Summary", use_container_width=True):
                with st.spinner("Calling local Ollama LLM to synthesize 8-agent executive report..."):
                    orchestrator = OrchestratorAgent()
                    llm_result = orchestrator.generate_llm_executive_summary(report)
                    st.session_state["agent_llm_summary"] = llm_result

        with col_info:
            st.caption("Executes local Ollama client using Orchestrator output across all 8 agents.")

        # Display LLM Executive Summary if generated
        llm_summary = st.session_state.get("agent_llm_summary")
        if llm_summary:
            st.write("")
            with st.expander("Executive Supervision Summary (Bilingual FR / EN)", expanded=True):
                if not llm_summary.get("available", True):
                    st.info(f"Ollama Offline / Fallback Mode: {llm_summary.get('reason')}")

                tab_en, tab_fr = st.tabs(["English Summary", "Résumé Français"])
                with tab_en:
                    st.markdown(f"**Executive Summary:** {llm_summary.get('executive_summary_en')}")
                    st.markdown(f"**Primary Action:** {llm_summary.get('final_recommendation_en')}")
                    rec_en = llm_summary.get("suggested_admin_actions_en", [])
                    if rec_en:
                        st.markdown("**Suggested Administrator Actions:**")
                        for r in rec_en:
                            st.markdown(f"- {r}")

                with tab_fr:
                    st.markdown(f"**Résumé Exécutif:** {llm_summary.get('executive_summary_fr')}")
                    st.markdown(f"**Action Principale:** {llm_summary.get('final_recommendation_fr')}")
                    rec_fr = llm_summary.get("suggested_admin_actions_fr", [])
                    if rec_fr:
                        st.markdown("**Actions Administrateur Suggérées:**")
                        for r in rec_fr:
                            st.markdown(f"- {r}")

        st.markdown("---")
        st.markdown("### Specialized Agent Reports")

        # Display Agent Cards
        agent_outputs = report.agent_outputs
        if not agent_outputs:
            st.warning("No specialized agents were selected for analysis.")

        for agent_dict in agent_outputs:
            st.write("")
            with st.container():
                st.markdown(
                    f"""
                    <div style="border: 1px solid var(--osmos-border, #334155); border-radius: 10px; padding: 16px; 
                                background: var(--osmos-card-bg, #111827); margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4 style="margin: 0; font-size: 16px; font-weight: 800;">{agent_dict.get('agent_name')}</h4>
                                <span style="font-size: 12px; color: var(--osmos-muted, #94A3B8);">{agent_dict.get('agent_role')}</span>
                            </div>
                            <div>
                                {render_agent_status_badge(agent_dict.get('status', 'OK'))}
                            </div>
                        </div>
                        <p style="margin: 10px 0; font-size: 13.5px; color: var(--osmos-text, #F8FAFC);">
                            <strong>Summary:</strong> {agent_dict.get('summary')}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Risks & Opportunities grid
                r_col, o_col = st.columns(2)
                with r_col:
                    risks = agent_dict.get("risks", [])
                    if risks:
                        st.markdown("**Identified Risks:**")
                        for r in risks:
                            st.markdown(f"- :warning: {r}")
                    else:
                        st.caption("No critical risks identified by this agent.")

                with o_col:
                    opps = agent_dict.get("opportunities", [])
                    if opps:
                        st.markdown("**Opportunities & Strengths:**")
                        for o in opps:
                            st.markdown(f"- :rocket: {o}")
                    else:
                        st.caption("No specific expansion opportunities logged.")

                recs = agent_dict.get("recommendations", [])
                if recs:
                    st.markdown("**Recommended Actions:**")
                    for rec in recs:
                        st.markdown(f"- :bulb: {rec}")

                # Evidence Traceability (Hidden in presentation mode unless expanded)
                evidence_list = agent_dict.get("evidence", [])
                if evidence_list:
                    if presentation_mode:
                        with st.expander(f"View Evidence Traceability ({len(evidence_list)} metrics)", expanded=False):
                            st.table(pd.DataFrame(evidence_list))
                    else:
                        st.markdown("**Evidence Traceability Matrix:**")
                        st.dataframe(pd.DataFrame(evidence_list), use_container_width=True)

    else:
        st.info("Select an entity and click **Run Multi-Agent Analysis** to trigger the supervision layer.")
