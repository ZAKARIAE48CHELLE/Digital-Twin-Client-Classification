"""
OSMOS Executive Report Generator — Dashboard UI (Phase 8.6)
============================================================
Streamlit dashboard for configuring, generating, previewing, and downloading
Entity Executive Reports, Agent Run Reports, Journey Reports, and System Overview Reports.
"""

import logging
from typing import Optional, Dict, Any, List
import pandas as pd
import streamlit as st

from reports.report_schemas import ReportContext, ReportExportResult
from reports.report_generator import (
    generate_entity_executive_report,
    generate_agent_run_report,
    generate_journey_report,
    generate_system_overview_report,
    generate_report_markdown,
)
from reports.report_exporter import export_report_to_file, convert_markdown_to_html
from agents.agent_repository import get_agent_runs, is_agent_db_available
from llm.llm_client import generate_text, check_llm_available
from llm.llm_json_utils import extract_and_parse_json
from ui.icons import icon_html

logger = logging.getLogger("OSMOS_REPORT_DASHBOARD")


def render_report_dashboard(df: Optional[pd.DataFrame] = None, history_df: Optional[pd.DataFrame] = None):
    """Main rendering entrypoint for the Executive Reports page."""
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 28px; font-weight: 800; margin-bottom: 4px; display: flex; align-items: center; gap: 10px;">
                {icon_html('file')} Executive Report Generator
            </h1>
            <p style="color: var(--osmos-muted); font-size: 14px; margin-bottom: 8px;">
                Generate, Preview & Download Executive Reports (Markdown, HTML & PDF) for Entities, Agent Runs, and Journeys
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Report Type & Parameter Configuration
    st.markdown("##### Report Configuration & Parameters")
    r_col1, r_col2 = st.columns([2, 2])

    with r_col1:
        report_type = st.selectbox(
            "Select Report Type:",
            options=[
                "Entity Executive Report",
                "Agent Supervision Run Report",
                "Customer Journey Report",
                "System Overview Report",
            ],
            index=0,
            key="sel_report_type",
        )

    available_entities = []
    if df is not None and not df.empty and "entity_id" in df.columns:
        available_entities = sorted(df["entity_id"].dropna().astype(str).unique().tolist())
    if "P_DEMO_001" not in available_entities:
        available_entities.insert(0, "P_DEMO_001")
    if "C00001" not in available_entities:
        available_entities.append("C00001")

    selected_entity = "P_DEMO_001"
    selected_run_id = 1

    with r_col2:
        if report_type == "Entity Executive Report":
            selected_entity = st.selectbox("Select Entity ID:", options=available_entities, index=0, key="sel_report_ent")
        elif report_type == "Agent Supervision Run Report":
            if is_agent_db_available():
                runs = get_agent_runs(limit=30)
                run_opts = [f"Run #{r.get('run_id')} — Entity [{r.get('entity_id')}] ({r.get('global_status')})" for r in runs]
                if run_opts:
                    sel_run_str = st.selectbox("Select Agent Run:", options=run_opts, index=0, key="sel_report_run_opt")
                    selected_run_id = int(sel_run_str.split("#")[1].split(" ")[0])
                else:
                    selected_run_id = st.number_input("Enter Run ID:", min_value=1, value=1, step=1, key="num_report_run")
            else:
                selected_run_id = st.number_input("Enter Run ID:", min_value=1, value=1, step=1, key="num_report_run")
        elif report_type == "Customer Journey Report":
            selected_entity = st.selectbox("Select Entity ID for Journey:", options=available_entities, index=0, key="sel_report_j_ent")

    st.write("")
    if st.button("🚀 Generate Executive Report", type="primary", use_container_width=True, key="btn_gen_report"):
        with st.spinner(f"Compiling {report_type}..."):
            if report_type == "Entity Executive Report":
                md_text, ctx = generate_entity_executive_report(selected_entity, df=df)
            elif report_type == "Agent Supervision Run Report":
                md_text, ctx = generate_agent_run_report(selected_run_id)
            elif report_type == "Customer Journey Report":
                md_text, ctx = generate_journey_report(selected_entity)
            else:
                md_text, ctx = generate_system_overview_report()

            st.session_state["generated_report_md"] = md_text
            st.session_state["generated_report_ctx"] = ctx
            st.session_state.pop("report_llm_polish", None)

    # Report Display & Downloads
    md_report = st.session_state.get("generated_report_md")
    report_ctx = st.session_state.get("generated_report_ctx")

    if md_report and report_ctx:
        st.markdown("---")

        # Download Buttons Bar
        st.markdown("##### Download & Export Report")
        d_col1, d_col2, d_col3, d_col4 = st.columns(4)

        base_name = f"OSMOS_{report_type.replace(' ', '_')}_{report_ctx.entity_id or report_ctx.run_id or 'System'}"

        with d_col1:
            res_md = export_report_to_file(md_report, file_name_base=base_name, export_format="markdown")
            st.download_button(
                "📥 Download Markdown (.md)",
                data=md_report,
                file_name=res_md.file_name,
                mime="text/markdown",
                use_container_width=True,
                key="btn_dl_md",
            )

        with d_col2:
            html_text = convert_markdown_to_html(md_report)
            res_html = export_report_to_file(md_report, file_name_base=base_name, export_format="html")
            st.download_button(
                "🌐 Download HTML (.html)",
                data=html_text,
                file_name=res_html.file_name,
                mime="text/html",
                use_container_width=True,
                key="btn_dl_html",
            )

        with d_col3:
            res_pdf = export_report_to_file(md_report, file_name_base=base_name, export_format="pdf")
            st.download_button(
                "📄 Download PDF / Document",
                data=html_text,
                file_name=res_pdf.file_name,
                mime="application/octet-stream",
                use_container_width=True,
                key="btn_dl_pdf",
            )

        with d_col4:
            if st.button("✨ LLM Executive Polish", use_container_width=True, key="btn_llm_polish"):
                with st.spinner("Calling local Ollama LLM to polish executive summary..."):
                    avail, reason = check_llm_available()
                    if not avail:
                        st.info(f"Ollama Offline Mode: {reason}")
                    else:
                        prompt = f"""
You are the OSMOS Executive Report Editor.
Polish the following report executive summary into a bilingual FR/EN executive synthesis.

REPORT SUMMARY:
{report_ctx.final_recommendation}

RECOMMENDED ACTION:
{report_ctx.next_best_action}

Return ONLY valid JSON matching this schema:
{{
  "polished_summary_fr": "Synthese executive polie en francais.",
  "polished_summary_en": "Polished executive synthesis in English.",
  "strategic_advice_fr": ["Directive 1", "Directive 2"],
  "strategic_advice_en": ["Directive 1", "Directive 2"]
}}
"""
                        try:
                            raw = generate_text(prompt, temperature=0.2)
                            parsed = extract_and_parse_json(raw)
                            if parsed:
                                st.session_state["report_llm_polish"] = parsed
                        except Exception as e:
                            logger.error(f"Error polishing report: {e}")

        # Optional LLM Polish Display
        llm_polish = st.session_state.get("report_llm_polish")
        if llm_polish:
            st.write("")
            with st.expander("✨ LLM Polished Executive Synthesis (Bilingual FR / EN)", expanded=True):
                p_en, p_fr = st.tabs(["English Polish", "Synthèse Polie Française"])
                with p_en:
                    st.markdown(f"**Executive Synthesis:** {llm_polish.get('polished_summary_en')}")
                    adv_en = llm_polish.get("strategic_advice_en", [])
                    if adv_en:
                        st.markdown("**Strategic Directives:**")
                        for a in adv_en:
                            st.markdown(f"- {a}")
                with p_fr:
                    st.markdown(f"**Synthèse Exécutive:** {llm_polish.get('polished_summary_fr')}")
                    adv_fr = llm_polish.get("strategic_advice_fr", [])
                    if adv_fr:
                        st.markdown("**Directives Stratégiques:**")
                        for a in adv_fr:
                            st.markdown(f"- {a}")

        st.write("")
        st.markdown("##### Report Document Preview")
        with st.expander("📄 Click to View Full Rendered Markdown Report Document", expanded=True):
            st.markdown(md_report)
