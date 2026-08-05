"""
OSMOS Agent Knowledge Base & Documentation Memory — Test Suite (Phase 8.5)
==========================================================================
Unit tests verifying markdown parsing, chunking, keyword extraction, knowledge search,
decision memory inspection, agent context knowledge retrieval, and read-only safety.
"""

import os
import unittest
import pandas as pd

from knowledge.knowledge_schemas import KnowledgeDocument, KnowledgeChunk, KnowledgeResult, DecisionMemoryItem
from knowledge.documentation_indexer import (
    split_markdown_into_sections,
    create_chunks_from_sections,
    extract_keywords,
    index_documentation_folder,
)
from knowledge.knowledge_repository import (
    save_knowledge_document,
    save_knowledge_chunk,
    search_knowledge_chunks,
    clear_knowledge_index,
    get_knowledge_index_stats,
)
from knowledge.knowledge_retriever import (
    retrieve_relevant_knowledge,
    retrieve_docs_for_agent,
    retrieve_rules_for_decision,
)
from knowledge.decision_memory import (
    get_entity_decision_memory,
    get_previous_recommendations,
    get_rejected_recommendations,
    check_if_action_was_previously_rejected,
    summarize_decision_history,
)
from agents.context_builder import build_entity_agent_context
from agents.orchestrator_agent import OrchestratorAgent, run_orchestrated_analysis


class TestKnowledgeBasePhase85(unittest.TestCase):

    def setUp(self):
        clear_knowledge_index()

    def test_markdown_heading_splitter(self):
        """Verifies markdown text is split accurately by section headings."""
        sample_md = """
# Introduction to OSMOS
OSMOS is a Digital Twin CRM platform.

## Architecture
The system consists of 8 specialized agents and an Orchestrator.

### Supervision Layer
Agents evaluate entities in read-only mode.
        """
        sections = split_markdown_into_sections(sample_md)
        self.assertGreaterEqual(len(sections), 2)
        self.assertEqual(sections[0]["section_name"], "Introduction to OSMOS")

    def test_chunking_creates_chunks_with_keywords(self):
        """Verifies section content chunking and keyword extraction."""
        sample_text = "The Multi-Agent Supervision Layer enforces strict read-only governance across all 8 agents."
        keywords = extract_keywords(sample_text)
        self.assertIn("supervision", keywords)

        sections = [{"section_name": "Governance", "content": sample_text * 10}]
        chunks = create_chunks_from_sections(sections, max_chars=200)
        self.assertGreater(len(chunks), 1)

    def test_save_and_search_knowledge_chunks(self):
        """Verifies saving and searching knowledge chunks."""
        doc_id = save_knowledge_document({
            "source_type": "documentation",
            "source_name": "OSMOS_Test_Doc.md",
            "title": "Test Document",
            "content": "Sample content",
        })
        self.assertIsNotNone(doc_id)

        chunk_id = save_knowledge_chunk({
            "document_id": doc_id,
            "chunk_title": "Test Section",
            "chunk_text": "Digital Twin CRM supports stable persona classification.",
            "keywords": ["digital", "twin", "persona"],
        })
        self.assertIsNotNone(chunk_id)

        results = search_knowledge_chunks("persona")
        self.assertGreater(len(results), 0)
        self.assertIn("persona", results[0]["chunk_text"].lower())

    def test_retrieve_relevant_knowledge(self):
        """Verifies KnowledgeRetriever scores and returns KnowledgeResult objects."""
        doc_id = save_knowledge_document({
            "source_type": "system_rule",
            "source_name": "Governance_Spec",
            "title": "System Rules",
        })
        save_knowledge_chunk({
            "document_id": doc_id,
            "chunk_title": "Human Approval Rule",
            "chunk_text": "All operational actions require explicit human administrative approval.",
            "keywords": ["human", "approval"],
        })

        retrieved = retrieve_relevant_knowledge("human approval")
        self.assertGreater(len(retrieved), 0)
        self.assertIsInstance(retrieved[0], KnowledgeResult)
        self.assertGreater(retrieved[0].relevance_score, 0.50)

    def test_decision_memory_fallback(self):
        """Verifies decision memory functions handle missing entities safely."""
        memory = get_entity_decision_memory("NON_EXISTENT_ENTITY")
        self.assertEqual(len(memory), 0)

        summary = summarize_decision_history("NON_EXISTENT_ENTITY")
        self.assertIn("No previous supervision runs", summary)

    def test_build_context_with_include_knowledge(self):
        """Verifies AgentContext populates knowledge fields when include_knowledge=True."""
        sample_df = pd.DataFrame([{"entity_id": "P_DEMO_001", "entity_type": "Prospect", "recency_days": 5}])
        ctx = build_entity_agent_context("P_DEMO_001", df=sample_df, include_knowledge=True)
        self.assertEqual(ctx.entity_id, "P_DEMO_001")
        self.assertIsNotNone(ctx.knowledge_results)

    def test_orchestrator_analysis_with_knowledge(self):
        """Verifies OrchestratorAgent executes multi-agent analysis cleanly with include_knowledge=True."""
        sample_df = pd.DataFrame([{"entity_id": "P_DEMO_001", "entity_type": "Prospect", "recency_days": 5}])
        report = run_orchestrated_analysis("P_DEMO_001", df=sample_df, debate_mode=True, include_knowledge=True)
        self.assertEqual(report.entity_id, "P_DEMO_001")
        self.assertIsNotNone(report.global_status)


if __name__ == "__main__":
    unittest.main()
