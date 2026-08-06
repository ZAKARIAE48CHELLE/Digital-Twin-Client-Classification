"""
OSMOS Multi-Agent Supervision Layer — Agent Dashboard (Phase 8.4)
==================================================================
Streamlit dashboard page for the Agent Supervision Center.
Supports 8 specialized agents, persistent Agent Memory (supervision runs),
Human Approval Queue, and Agent Collaboration & Debate Mode.
"""

import logging
from typing import Optional, List, Dict, Any
import pandas as pd
import streamlit as st

from agents.agent_schemas import AgentOutput
from agents.orchestrator_agent import OrchestratorAgent, run_orchestrated_analysis
from agents.langgraph_supervision import run_langgraph_supervision
from agents.agent_registry import list_agents, CORE_AGENT_IDS, OPERATIONAL_AGENT_IDS

from agents.result_aggregator import compute_system_readiness_summary
from agents.agent_repository import (
    is_agent_db_available,
    save_agent_run,
    save_agent_outputs,
    get_agent_memory_for_entity,
    get_agent_outputs,
    create_approval_item,
    get_approval_queue,
    update_approval_status,
    convert_approved_action_to_campaign_draft,
)
from ui.icons import icon_html

logger = logging.getLogger("OSMOS_AGENT_DASHBOARD")


def _rep_val(rep: Any, attr: str, default: Any = None) -> Any:
    """Safely extracts an attribute or dict key from OrchestratorOutput or dict."""
    if rep is None:
        return default
    if isinstance(rep, dict):
        return rep.get(attr, default)
    return getattr(rep, attr, default)


def _to_dict(obj: Any) -> Dict[str, Any]:
    """Converts object to dict if it has to_dict or __dict__, or returns dict as-is."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return {}


def format_arrow_safe_df(records: Any) -> pd.DataFrame:
    """Converts records list or DataFrame into a PyArrow-safe string DataFrame."""
    if isinstance(records, pd.DataFrame):
        df_out = records.copy()
    else:
        df_out = pd.DataFrame(records)
    for col in df_out.columns:
        df_out[col] = df_out[col].astype(str)
    return df_out


def render_agent_status_badge(status: str) -> str:
    """Renders a color-coded HTML badge for agent status."""
    colors = {
        "OK": ("#10B981", "rgba(16, 185, 129, 0.15)"),
        "Warning": ("#F59E0B", "rgba(245, 158, 11, 0.15)"),
        "Critical": ("#EF4444", "rgba(239, 68, 68, 0.15)"),
        "Insufficient Data": ("#6B7280", "rgba(107, 114, 128, 0.15)"),
        "Error": ("#DC2626", "rgba(220, 38, 38, 0.15)"),
        "Pending": ("#3B82F6", "rgba(59, 130, 246, 0.15)"),
        "Approved": ("#10B981", "rgba(16, 185, 129, 0.15)"),
        "Rejected": ("#EF4444", "rgba(239, 68, 68, 0.15)"),
        "Converted to Campaign Draft": ("#8B5CF6", "rgba(139, 92, 246, 0.15)"),
        "Ignored": ("#6B7280", "rgba(107, 114, 128, 0.15)"),
    }
    text_color, bg_color = colors.get(status, ("#60A5FA", "rgba(96, 165, 250, 0.15)"))
    return (
        f'<span style="background-color: {bg_color}; color: {text_color}; '
        f'padding: 4px 10px; border-radius: 9999px; font-weight: 700; font-size: 12px; '
        f'border: 1px solid {text_color}; display: inline-block;">{status}</span>'
    )


def render_consensus_badge(status: str) -> str:
    """Renders a color-coded HTML badge for debate consensus status."""
    colors = {
        "Strong Consensus": ("#10B981", "rgba(16, 185, 129, 0.15)"),
        "Partial Consensus": ("#3B82F6", "rgba(59, 130, 246, 0.15)"),
        "Conflict Detected": ("#F59E0B", "rgba(245, 158, 11, 0.15)"),
        "Critical Conflict": ("#EF4444", "rgba(239, 68, 68, 0.15)"),
        "Insufficient Data": ("#6B7280", "rgba(107, 114, 128, 0.15)"),
    }
    text_color, bg_color = colors.get(status, ("#8B5CF6", "rgba(139, 92, 246, 0.15)"))
    return (
        f'<span style="background-color: {bg_color}; color: {text_color}; '
        f'padding: 5px 12px; border-radius: 9999px; font-weight: 800; font-size: 13px; '
        f'border: 1.5px solid {text_color}; display: inline-block;">{status}</span>'
    )


def render_agent_dashboard(df: Optional[pd.DataFrame] = None, history_df: Optional[pd.DataFrame] = None):
    """Main rendering entrypoint for the Agent Supervision Center page."""
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 28px; font-weight: 800; margin-bottom: 4px; display: flex; align-items: center; gap: 10px;">
                {icon_html('bot')} Agent Supervision Center
            </h1>
            <p style="color: var(--osmos-muted); font-size: 14px; margin-bottom: 8px;">
                8-Agent Multi-Agent CRM Supervision, Agent Collaboration & Debate, Memory & Human Approval Queue
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Mandatory Human-in-the-Loop Governance Notice
    st.info("🛡️ **Human-in-the-Loop Governance**: Agents recommend actions but never execute them automatically. All actions require admin validation.")

    # Main Navigation Tabs: Live Analysis, Agent Memory, Human Approval Queue
    tab_live, tab_memory, tab_queue = st.tabs([
        "🔬 Live Supervision & Analysis",
        "🧠 Agent Memory (History)",
        "📋 Human Approval Queue",
    ])

    # ------------------------------------------------------------------
    # TAB 1: LIVE SUPERVISION & ANALYSIS
    # ------------------------------------------------------------------
    with tab_live:
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
                key="sel_entity_live",
                help="Choose a customer or prospect entity for multi-agent supervision.",
            )

        with col_mode:
            st.write("")
            st.write("")
            presentation_mode = st.checkbox("Presentation Mode", value=False, help="Hide raw evidence tables for executive presentation.")

        # Categorized Agent Selection
        st.markdown("##### Agent Selection & Presets")
        preset_col1, preset_col2, preset_col3, preset_col4 = st.columns([1.5, 1.5, 1.5, 2.5])

        if "selected_agents_set" not in st.session_state:
            st.session_state["selected_agents_set"] = set(CORE_AGENT_IDS)

        with preset_col1:
            if st.button("Select All (8 Agents)", use_container_width=True, key="btn_sel_all"):
                st.session_state["selected_agents_set"] = {"digital_twin", "clv", "churn", "persona", "campaign", "journey", "database_audit", "ui_ux"}

        with preset_col2:
            if st.button("Default Core (5 Agents)", use_container_width=True, key="btn_sel_core"):
                st.session_state["selected_agents_set"] = set(CORE_AGENT_IDS)

        with preset_col3:
            if st.button("Clear Selection", use_container_width=True, key="btn_sel_clear"):
                st.session_state["selected_agents_set"] = set()

        with preset_col4:
            enable_debate_mode = st.toggle("Enable Agent Debate Mode", value=True, key="tgl_debate", help="Cross-review agent findings, detect risk/opportunity conflicts, and synthesize consensus.")

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

        eng_col1, eng_col2 = st.columns([2.5, 2.5])
        with eng_col1:
            include_knowledge_memory = st.checkbox("Include Knowledge Memory (Docs, Rules & Decision History)", value=False, key="chk_knowledge_memory")
        with eng_col2:
            execution_engine = st.selectbox(
                "Agent Execution Engine:",
                options=["LangGraph Workflow (StateGraph)", "Legacy Orchestrator"],
                index=0,
                key="sel_exec_engine",
                help="Select between stateful LangGraph workflow engine and legacy orchestrator.",
            )

        # Visual LangGraph Workflow Summary Diagram
        st.markdown(
            f"""
            <div style="background: var(--osmos-bg-soft); border: 1px solid var(--osmos-border); border-radius: 8px; 
                        padding: 10px 16px; margin: 8px 0 16px 0; font-size: 13px; color: var(--osmos-text);">
                <div style="font-weight: 700; color: var(--osmos-primary-accent); margin-bottom: 4px;">
                    ⚡ Execution Pipeline: {execution_engine}
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px; font-size: 12px; font-weight: 600;">
                    <span style="background: var(--osmos-card-bg); padding: 4px 8px; border-radius: 4px; border: 1px solid var(--osmos-border);">Context Builder</span> ➔
                    <span style="background: var(--osmos-card-bg); padding: 4px 8px; border-radius: 4px; border: 1px solid var(--osmos-border);">Core Agents</span> ➔
                    <span style="background: var(--osmos-card-bg); padding: 4px 8px; border-radius: 4px; border: 1px solid var(--osmos-border);">Operational Agents</span> ➔
                    <span style="background: var(--osmos-card-bg); padding: 4px 8px; border-radius: 4px; border: 1px solid var(--osmos-border);">Debate Engine</span> ➔
                    <span style="background: var(--osmos-card-bg); padding: 4px 8px; border-radius: 4px; border: 1px solid var(--osmos-border);">Consensus</span> ➔
                    <span style="background: var(--osmos-card-bg); padding: 4px 8px; border-radius: 4px; border: 1px solid var(--osmos-border);">Approval Prep</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Run Multi-Agent Analysis", type="primary", use_container_width=True, key="btn_run_analysis"):
            with st.spinner(f"Executing {execution_engine} for {len(selected_agent_ids)} agents..."):
                if "LangGraph" in execution_engine:
                    report = run_langgraph_supervision(
                        entity_id=selected_entity,
                        df=df,
                        selected_agents=selected_agent_ids,
                        include_knowledge=include_knowledge_memory,
                        debate_mode=enable_debate_mode,
                    )
                else:
                    report = run_orchestrated_analysis(
                        entity_id=selected_entity,
                        df=df,
                        history_df=history_df,
                        selected_agent_ids=selected_agent_ids,
                        debate_mode=enable_debate_mode,
                        include_knowledge=include_knowledge_memory,
                    )
                st.session_state["agent_supervision_report"] = report
                st.session_state["execution_engine_used"] = execution_engine
                st.session_state.pop("agent_llm_summary", None)
                st.session_state.pop("agent_llm_debate_summary", None)

        # Display Analysis Results
        report = st.session_state.get("agent_supervision_report")
        engine_used = st.session_state.get("execution_engine_used", "LangGraph Workflow")
        rep_entity_id = _rep_val(report, "entity_id")
        if report and rep_entity_id == selected_entity:
            st.markdown("---")

            # Global Status Callout Card
            rep_status = _rep_val(report, "global_status", "OK")
            rep_summary = _rep_val(report, "final_summary", "")
            rep_nba = _rep_val(report, "recommended_next_best_action", "Maintain active supervision")
            rep_conf = _rep_val(report, "confidence_score", 1.0)

            st.markdown(
                f"""
                <div style="background: var(--osmos-card-bg); border: 1px solid var(--osmos-border); 
                            border-radius: 12px; padding: 20px; margin-bottom: 24px; box-shadow: var(--osmos-shadow-sm);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div>
                            <span style="color: var(--osmos-muted); font-size: 12px; font-weight: 700; text-transform: uppercase;">
                                Multi-Agent Orchestrator Supervision Report ({engine_used})
                            </span>
                            <h3 style="margin: 4px 0 0 0; font-size: 20px; font-weight: 800; color: var(--osmos-text);">Entity [{rep_entity_id}]</h3>
                        </div>
                        <div>
                            {render_agent_status_badge(rep_status)}
                        </div>
                    </div>
                    <p style="font-size: 14px; margin-bottom: 16px; color: var(--osmos-text); line-height: 1.5;">
                        {rep_summary}
                    </p>
                    <div style="background: var(--osmos-bg-soft); border-left: 4px solid var(--osmos-primary-accent); 
                                padding: 14px 16px; border-radius: 6px;">
                        <span style="font-size: 11px; font-weight: 800; color: var(--osmos-primary-accent); text-transform: uppercase; letter-spacing: 0.5px;">
                            Recommended Next Best Action (Read-Only Advice)
                        </span>
                        <p style="margin: 4px 0 0 0; font-size: 15px; font-weight: 700; color: var(--osmos-text);">
                            {rep_nba}
                        </p>
                    </div>
                    <div style="margin-top: 12px; font-size: 12px; color: var(--osmos-muted); text-align: right;">
                        Engine: <strong>{engine_used}</strong> | Confidence: <strong>{rep_conf * 100:.0f}%</strong> | Mode: <strong>Read-Only</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # PHASE 8.4: AGENT COLLABORATION & DEBATE SECTION
            deb = _rep_val(report, "debate_output")
            if deb and enable_debate_mode:
                st.markdown("### 🤝 Agent Collaboration & Debate Engine")
                consensus = _rep_val(deb, "consensus", {})
                if not isinstance(consensus, dict): consensus = _to_dict(consensus)
                c_status = consensus.get("consensus_status", "Strong Consensus")
                priority_action = consensus.get("priority_action", rep_nba)
                conflicts = _rep_val(deb, "conflicts", [])
                statements = _rep_val(deb, "agent_statements", [])

                # Debate Banner
                st.markdown(
                    f"""
                    <div style="background: var(--osmos-card-bg); border: 1.5px solid var(--osmos-primary-accent); 
                                border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: var(--osmos-shadow-sm);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <div>
                                <span style="color: var(--osmos-primary-accent); font-size: 12px; font-weight: 800; text-transform: uppercase;">
                                    Cross-Agent Consensus Synthesis
                                </span>
                                <h4 style="margin: 2px 0 0 0; font-size: 18px; font-weight: 800; color: var(--osmos-text);">Debate Decision & Conflict Audit</h4>
                            </div>
                            <div>
                                {render_consensus_badge(c_status)}
                            </div>
                        </div>
                        <p style="font-size: 14px; color: var(--osmos-text); margin-bottom: 12px;">
                            <strong>Reasoning:</strong> {consensus.get('reasoning_summary')}
                        </p>
                        <div style="background: var(--osmos-bg-soft); border-left: 4px solid #8B5CF6; padding: 12px 14px; border-radius: 6px;">
                            <span style="font-size: 11px; font-weight: 800; color: #8B5CF6; text-transform: uppercase;">Synthesized Priority Action</span>
                            <p style="margin: 2px 0 0 0; font-size: 15px; font-weight: 800; color: var(--osmos-text);">{priority_action}</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if presentation_mode:
                    # Executive View in Presentation Mode
                    st.markdown("##### Executive Agent Debate Summary")
                    st.info(f"**Consensus Status:** {c_status} | **Debate Confidence:** {consensus.get('confidence_score', 0.85)*100:.0f}%")
                    st.markdown(f"**Primary Action Decision:** {priority_action}")
                    if conflicts:
                        st.warning(f"**Resolved Conflicts ({len(conflicts)}):** " + "; ".join([c.get("description", "") for c in conflicts]))
                else:
                    # Full Diagnostic View in Standard Mode
                    tab_stmt, tab_conf, tab_dec = st.tabs(["Agent Statements & Positions", f"Conflicts Detected ({len(conflicts)})", "Consensus Decision Details"])

                    with tab_stmt:
                        st.markdown("##### Agent Statements & Proposed Positions")
                        for stmt in statements:
                            concern = stmt.get("concern_level", "Low")
                            c_color = "#10B981" if concern == "Low" else "#F59E0B" if concern == "Medium" else "#EF4444"
                            st.markdown(
                                f"""
                                <div style="border: 1px solid var(--osmos-border); border-radius: 8px; padding: 12px; margin-bottom: 8px; background: var(--osmos-bg-soft);">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong>{stmt.get('agent_name')}</strong>
                                        <span style="color: {c_color}; font-weight: 700; font-size: 12px;">Concern: {concern}</span>
                                    </div>
                                    <p style="margin: 4px 0 6px 0; font-size: 13px;">{stmt.get('position')}</p>
                                    <div style="font-size: 12px; color: var(--osmos-muted);"><strong>Proposed Action:</strong> {stmt.get('proposed_action')}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                    with tab_conf:
                        if not conflicts:
                            st.success("Zero conflicts detected across active agents! Full alignment reached.")
                        else:
                            st.markdown("##### Identified Risk & Opportunity Disagreements")
                            for conf_item in conflicts:
                                sev = conf_item.get("severity", "Medium")
                                st.markdown(
                                    f"""
                                    <div style="border: 1px solid var(--osmos-border); border-radius: 8px; padding: 14px; margin-bottom: 10px; background: var(--osmos-card-bg);">
                                        <div style="display: flex; justify-content: space-between;">
                                            <strong style="color: var(--osmos-primary-accent);">{conf_item.get('conflict_type')}</strong>
                                            {render_agent_status_badge(sev if sev != 'Low' else 'OK')}
                                        </div>
                                        <p style="margin: 6px 0; font-size: 13.5px;">{conf_item.get('description')}</p>
                                        <div style="background: var(--osmos-bg-soft); padding: 8px 10px; border-radius: 4px; font-size: 12.5px; margin-top: 6px;">
                                            💡 <strong>Resolution Advice:</strong> {conf_item.get('resolution_suggestion')}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                    with tab_dec:
                        st.markdown("##### Consensus Decision Breakdown")
                        r_col, o_col = st.columns(2)
                        with r_col:
                            st.markdown("**Agreed Risks:**")
                            for r in consensus.get("agreed_risks", []):
                                st.markdown(f"- :warning: {r}")
                        with o_col:
                            st.markdown("**Agreed Opportunities:**")
                            for o in consensus.get("agreed_opportunities", []):
                                st.markdown(f"- :rocket: {o}")

                # Button-Triggered LLM Debate Summary Button
                st.markdown("##### LLM Debate Summary Generation (Button-Triggered Only)")
                d_btn_col, d_info_col = st.columns([2, 3])
                with d_btn_col:
                    if st.button("Generate LLM Debate Summary", use_container_width=True, key="btn_gen_llm_debate"):
                        with st.spinner("Synthesizing agent debate with local Ollama LLM..."):
                            orchestrator = OrchestratorAgent()
                            deb_llm_res = orchestrator.generate_llm_debate_summary(report)
                            st.session_state["agent_llm_debate_summary"] = deb_llm_res

                with d_info_col:
                    st.caption("Executes Ollama LLM to produce a bilingual executive synthesis of the agent debate.")

                llm_deb_summary = st.session_state.get("agent_llm_debate_summary")
                if llm_deb_summary:
                    st.write("")
                    with st.expander("LLM Executive Debate Synthesis (Bilingual FR / EN)", expanded=True):
                        if not llm_deb_summary.get("available", True):
                            st.info(f"Ollama Offline / Fallback Mode: {llm_deb_summary.get('reason')}")

                        t_en, t_fr = st.tabs(["English Synthesis", "Synthèse Française"])
                        with t_en:
                            st.markdown(f"**Debate Synthesis:** {llm_deb_summary.get('debate_summary_en')}")
                            st.markdown(f"**Final Decision:** {llm_deb_summary.get('final_decision_en')}")
                            g_en = llm_deb_summary.get("admin_guidance_en", [])
                            if g_en:
                                st.markdown("**Admin Guidance:**")
                                for g in g_en:
                                    st.markdown(f"- {g}")

                        with t_fr:
                            st.markdown(f"**Synthèse du Débat:** {llm_deb_summary.get('debate_summary_fr')}")
                            st.markdown(f"**Décision Finale:** {llm_deb_summary.get('final_decision_fr')}")
                            g_fr = llm_deb_summary.get("admin_guidance_fr", [])
                            if g_fr:
                                st.markdown("**Directives Administrateur:**")
                                for g in g_fr:
                                    st.markdown(f"- {g}")

            # Phase 8.3 & 8.4 Actions: Save Analysis & Create Approval Queue Items
            st.markdown("##### Agent Memory & Governance Actions")
            btn_save_col, btn_appr_col = st.columns(2)

            with btn_save_col:
                if st.button("💾 Save Agent Analysis to Memory", use_container_width=True, key="btn_save_run"):
                    if not is_agent_db_available():
                        st.warning("Agent memory persistence requires PostgreSQL connection.")
                    else:
                        orchestrator = OrchestratorAgent()
                        run_id = orchestrator.save_supervision_run(report, selected_agents=selected_agent_ids)
                        if run_id:
                            st.success(f"Successfully saved Agent Supervision Run #{run_id} to persistent memory!")

            with btn_appr_col:
                if st.button("📋 Create Approval Items from Recommendations", use_container_width=True, key="btn_create_appr"):
                    if not is_agent_db_available():
                        st.warning("Human approval queue creation requires PostgreSQL connection.")
                    else:
                        orchestrator = OrchestratorAgent()
                        actions = orchestrator.prepare_approval_actions(report)
                        created_count = 0
                        for act in actions:
                            appr_id = create_approval_item(run_id=None, entity_id=_rep_val(report, "entity_id"), action_dict=act)
                            if appr_id:
                                created_count += 1
                        st.success(f"Successfully created {created_count} Pending items in the Human Approval Queue!")

            st.write("")

            # System Readiness Summary Panel
            raw_outputs = _rep_val(report, "agent_outputs", [])
            agent_outputs_list = [AgentOutput(**d) if isinstance(d, dict) else d for d in raw_outputs]
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

            # On-Demand LLM Executive Summary Button
            st.markdown("##### Executive Summary Generation (Button-Triggered Only)")
            col_btn, col_info = st.columns([2, 3])
            with col_btn:
                if st.button("Generate LLM Executive Supervision Summary", use_container_width=True, key="btn_gen_llm"):
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
            agent_outputs = [_to_dict(a) for a in raw_outputs]
            if not agent_outputs:
                st.warning("No specialized agents were selected for analysis.")

            for agent_dict in agent_outputs:
                st.write("")
                with st.container():
                    st.markdown(
                        f"""
                        <div style="border: 1px solid var(--osmos-border); border-radius: 10px; padding: 16px; 
                                    background: var(--osmos-card-bg); margin-bottom: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h4 style="margin: 0; font-size: 16px; font-weight: 800; color: var(--osmos-text);">{agent_dict.get('agent_name')}</h4>
                                    <span style="font-size: 12px; color: var(--osmos-muted);">{agent_dict.get('agent_role')}</span>
                                </div>
                                <div>
                                    {render_agent_status_badge(agent_dict.get('status', 'OK'))}
                                </div>
                            </div>
                            <p style="margin: 10px 0; font-size: 13.5px; color: var(--osmos-text);">
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

                    # Evidence Traceability Matrix
                    evidence_list = agent_dict.get("evidence", [])
                    if evidence_list:
                        safe_ev_df = format_arrow_safe_df(evidence_list)
                        if presentation_mode:
                            with st.expander(f"View Evidence Traceability ({len(evidence_list)} metrics)", expanded=False):
                                st.table(safe_ev_df)
                        else:
                            st.markdown("**Evidence Traceability Matrix:**")
                            st.dataframe(safe_ev_df, use_container_width=True)

        else:
            st.info("Select an entity and click **Run Multi-Agent Analysis** to trigger the supervision layer.")

    # ------------------------------------------------------------------
    # TAB 2: AGENT MEMORY (HISTORICAL SUPERVISION RUNS)
    # ------------------------------------------------------------------
    with tab_memory:
        st.markdown("##### Historical Supervision Runs (Agent Memory)")
        if not is_agent_db_available():
            st.info("ℹ️ Agent Memory persistence requires PostgreSQL connection. In Excel fallback mode, runs are kept in session state only.")
        else:
            mem_entity = st.text_input("Filter by Entity ID (leave blank for all):", value="", key="txt_mem_entity")
            runs = get_agent_memory_for_entity(entity_id=mem_entity.strip() if mem_entity.strip() else None, limit=50)

            if not runs:
                st.caption("No saved agent supervision runs found in persistent memory.")
            else:
                for r in runs:
                    with st.expander(f"Run #{r.get('run_id')} — Entity [{r.get('entity_id')}] — {r.get('global_status')} ({r.get('created_at')})", expanded=False):
                        st.markdown(f"**Final Summary:** {r.get('final_summary')}")
                        st.markdown(f"**Recommended Next Best Action:** {r.get('recommended_next_best_action')}")
                        st.markdown(f"**Confidence Score:** {float(r.get('confidence_score', 0.0)) * 100:.0f}% | **Storage Mode:** {r.get('storage_mode')}")

                        # Fetch outputs for run
                        outputs = get_agent_outputs(r.get('run_id'))
                        if outputs:
                            st.markdown("**Specialized Agent Outputs:**")
                            for out_item in outputs:
                                st.markdown(f"- **{out_item.get('agent_name')}** ({out_item.get('status')}): {out_item.get('summary')}")

    # ------------------------------------------------------------------
    # TAB 3: HUMAN APPROVAL QUEUE
    # ------------------------------------------------------------------
    with tab_queue:
        st.markdown("##### Human Approval Queue & Governance")
        st.caption("Review agent-recommended operational actions. Action execution requires explicit admin approval.")

        if not is_agent_db_available():
            st.info("ℹ️ Human Approval Queue requires PostgreSQL connection. In Excel fallback mode, approval items are managed in memory.")
        else:
            filter_status = st.selectbox("Filter Queue by Status:", options=["Pending", "Approved", "Rejected", "All"], index=0, key="sel_queue_status")
            query_status = None if filter_status == "All" else filter_status

            queue_items = get_approval_queue(status=query_status, limit=50)

            if not queue_items:
                st.caption(f"No approval queue items found with status '{filter_status}'.")
            else:
                for item in queue_items:
                    appr_id = item.get("approval_id")
                    st.write("")
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="border: 1px solid var(--osmos-border); border-radius: 10px; padding: 16px; 
                                        background: var(--osmos-card-bg); margin-bottom: 8px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <h4 style="margin: 0; font-size: 15px; font-weight: 800; color: var(--osmos-text);">
                                            Item #{appr_id}: {item.get('proposed_action_title')}
                                        </h4>
                                        <span style="font-size: 12px; color: var(--osmos-muted);">
                                            Entity [{item.get('entity_id')}] | Source: {item.get('source_agent')} | Priority: {item.get('priority')}
                                        </span>
                                    </div>
                                    <div>
                                        {render_agent_status_badge(item.get('status'))}
                                    </div>
                                </div>
                                <p style="margin: 8px 0; font-size: 13.5px; color: var(--osmos-text);">
                                    {item.get('proposed_action_description')}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Admin Actions for Pending Items
                        if item.get("status") == "Pending":
                            ac_col1, ac_col2, ac_col3 = st.columns([3, 1, 1])
                            with ac_col1:
                                comment = st.text_input("Admin Comment (optional):", key=f"cmt_{appr_id}")
                            with ac_col2:
                                if st.button("Approve", key=f"btn_appr_{appr_id}", use_container_width=True):
                                    update_approval_status(appr_id, "Approved", admin_comment=comment)
                                    st.success(f"Approved Item #{appr_id}")
                                    st.rerun()
                            with ac_col3:
                                if st.button("Reject", key=f"btn_rej_{appr_id}", use_container_width=True):
                                    update_approval_status(appr_id, "Rejected", admin_comment=comment)
                                    st.error(f"Rejected Item #{appr_id}")
                                    st.rerun()

                        # Optional Campaign Draft Conversion for Approved Items
                        elif item.get("status") == "Approved":
                            st.caption(f"Approved on {item.get('approved_at')} by {item.get('approved_by')}. Comment: {item.get('admin_comment') or 'None'}")
                            if st.button("Convert Approved Action to Campaign Draft", key=f"btn_conv_{appr_id}"):
                                res = convert_approved_action_to_campaign_draft(appr_id)
                                if res.get("success"):
                                    st.success(res.get("message"))
                                    st.rerun()
                                else:
                                    st.error(res.get("reason"))

                        elif item.get("status") == "Rejected":
                            st.caption(f"Rejected on {item.get('rejected_at')}. Comment: {item.get('admin_comment') or 'None'}")
