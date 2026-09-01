"""
OSMOS Agent Knowledge Base — Dashboard UI (Phase 8.5)
=====================================================
Streamlit interface for documentation indexing, interactive knowledge retrieval,
entity decision memory explorer, and system governance rules.
"""

import logging
from typing import Optional, Dict, Any, List
import pandas as pd
import streamlit as st

from knowledge.knowledge_repository import (
    is_knowledge_db_available,
    get_knowledge_index_stats,
    search_knowledge_chunks,
)
from knowledge.documentation_indexer import reindex_all_docs, index_documentation_folder
from knowledge.decision_memory import (
    get_entity_decision_memory,
    get_approval_outcomes,
    summarize_decision_history,
)
from ui.icons import icon_html

logger = logging.getLogger("OSMOS_KNOWLEDGE_DASHBOARD")


def render_knowledge_dashboard(df: Optional[pd.DataFrame] = None, history_df: Optional[pd.DataFrame] = None):
    """Main rendering entrypoint for the Knowledge Base page."""
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 28px; font-weight: 800; margin-bottom: 4px; display: flex; align-items: center; gap: 10px;">
                {icon_html('book')} Agent Knowledge Base & Documentation Memory
            </h1>
            <p style="color: var(--osmos-muted); font-size: 14px; margin-bottom: 8px;">
                Internal Documentation Index, System Governance Rules & Entity Decision Memory Explorer (Phase 8.5)
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stats = get_knowledge_index_stats()

    # Index Status Bar
    st.markdown("##### Knowledge Index Status")
    st1, st2, st3, st4 = st.columns(4)
    with st1:
        st.metric("Indexed Documents", stats.get("document_count", 0))
    with st2:
        st.metric("Indexed Text Chunks", stats.get("chunk_count", 0))
    with st3:
        st.metric("Storage Backend", stats.get("storage_backend", "postgres").upper())
    with st4:
        st.write("")
        if st.button("🔄 Reindex OSMOS Documentation", use_container_width=True, key="btn_reindex_docs"):
            with st.spinner("Parsing docs/ markdown files and indexing text chunks..."):
                res = reindex_all_docs()
                st.success(f"Successfully indexed {res.get('indexed_files', 0)} documents ({res.get('total_chunks', 0)} chunks)!")
                st.rerun()

    st.markdown("---")

    # Main Navigation Tabs: Search Knowledge, Decision Memory Explorer, Governance Rules
    tab_search, tab_memory, tab_rules = st.tabs([
        "🔍 Search Documentation & Knowledge",
        "🧠 Entity Decision Memory Explorer",
        "📜 System Governance Rules",
    ])

    # ------------------------------------------------------------------
    # TAB 1: SEARCH KNOWLEDGE BASE
    # ------------------------------------------------------------------
    with tab_search:
        st.markdown("##### Interactive Documentation & Snippet Search")
        search_query = st.text_input("Enter search topic or keyword (e.g., 'stable persona', 'churn risk', 'human approval'):", value="", key="txt_k_search")

        if search_query.strip():
            with st.spinner(f"Searching knowledge index for '{search_query}'..."):
                chunks = search_knowledge_chunks(search_query.strip(), limit=10)

                if not chunks:
                    st.info("No matching knowledge chunks found. Try reindexing documentation or broadening search query.")
                else:
                    st.markdown(f"**Found {len(chunks)} matching knowledge snippet(s):**")
                    for c in chunks:
                        with st.expander(f"📖 {c.get('doc_title', c.get('source_name', 'Doc'))} — {c.get('chunk_title')}", expanded=True):
                            st.markdown(f"**Source Document:** `{c.get('source_name')}` | **Section:** `{c.get('section_name')}`")
                            st.markdown("---")
                            from ui.components import render_rich_markdown_with_diagrams
                            render_rich_markdown_with_diagrams(c.get('chunk_text', ''))
                            keywords = c.get("keywords")
                            if keywords:
                                st.caption(f"Keywords: {', '.join(keywords[:8])}")

    # ------------------------------------------------------------------
    # TAB 2: ENTITY DECISION MEMORY EXPLORER
    # ------------------------------------------------------------------
    with tab_memory:
        st.markdown("##### Historical Decision Memory Explorer")
        st.caption("Inspect previous agent supervision runs, approval queue decisions, and rejection history for an entity.")

        available_entities = []
        if df is not None and not df.empty and "entity_id" in df.columns:
            available_entities = sorted(df["entity_id"].dropna().astype(str).unique().tolist())
        if "P_DEMO_001" not in available_entities:
            available_entities.insert(0, "P_DEMO_001")
        if "C00001" not in available_entities:
            available_entities.append("C00001")

        mem_entity = st.selectbox("Select Entity to Explore Memory:", options=available_entities, index=0, key="sel_k_mem_ent")

        if mem_entity:
            history_summary = summarize_decision_history(mem_entity)
            st.info(f"ℹ️ **Decision Summary**: {history_summary}")

            outcomes = get_approval_outcomes(mem_entity)
            o1, o2, o3, o4 = st.columns(4)
            with o1:
                st.metric("Total Items", outcomes.get("total_approval_items", 0))
            with o2:
                st.metric("Approved Actions", outcomes.get("approved", 0))
            with o3:
                st.metric("Rejected Actions", outcomes.get("rejected", 0))
            with o4:
                st.metric("Pending Actions", outcomes.get("pending", 0))

            st.write("")
            memory_items = get_entity_decision_memory(mem_entity)
            if not memory_items:
                st.caption("No recorded decision memory or supervision runs for this entity yet.")
            else:
                st.markdown("##### Timeline of Agent Supervision Runs & Approval Queue Decisions")
                for item in memory_items:
                    m_dict = item.to_dict()
                    status = m_dict.get("status", "Pending")
                    type_label = m_dict.get("decision_type")

                    color = "#10B981" if status in {"Approved", "Converted to Campaign Draft"} else "#EF4444" if status == "Rejected" else "#3B82F6"

                    with st.expander(f"[{type_label}] {m_dict.get('recommendation')} — Status: {status} ({m_dict.get('created_at')[:19]})", expanded=False):
                        st.markdown(f"**Entity ID:** `{m_dict.get('entity_id')}` | **Decision Type:** `{type_label}`")
                        st.markdown(f"**Proposed Recommendation:** {m_dict.get('recommendation')}")
                        st.markdown(f"**Outcome / Comment:** {m_dict.get('outcome')}")

    # ------------------------------------------------------------------
    # TAB 3: SYSTEM GOVERNANCE RULES
    # ------------------------------------------------------------------
    with tab_rules:
        st.markdown("##### OSMOS Core System Governance Rules")
        st.caption("Immutable system rules enforced across all 8 agents and supervision workflows.")

        rules = [
            ("🛡️ 1. Read-Only Agent Principle", "Agents evaluate, detect, explain, and recommend actions in pure READ-ONLY mode. Agents never modify customer data, alter CLV/RFM, or execute campaigns."),
            ("📋 2. Human-in-the-Loop Governance", "All operational actions require explicit administrative approval in the Human Approval Queue. No automated campaign dispatches or customer updates occur."),
            ("🤖 3. Button-Triggered Advisory LLMs", "LLM executive summaries and debate summaries run strictly on-demand when explicitly triggered by an admin button click."),
            ("🎯 4. Official vs Exploratory Personas", "Stable personas represent official segment representations; dynamic personas represent exploratory behavioral hypotheses."),
            ("🚀 5. Closed-Loop Campaign Simulation", "Campaign simulations generate realistic response events and CLV impact traces without sending real emails or SMS messages."),
            ("🔍 6. Data Integrity Priority", "Database audit alerts override agent confidence scores; database schemas must be verified before presentation mode."),
        ]

        for r_title, r_desc in rules:
            with st.expander(r_title, expanded=True):
                st.markdown(r_desc)
