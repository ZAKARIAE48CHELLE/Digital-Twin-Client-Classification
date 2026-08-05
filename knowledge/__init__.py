"""
OSMOS Agent Knowledge Base & Documentation Memory Package (Phase 8.5)
======================================================================
"""

from knowledge.knowledge_schemas import (
    KnowledgeDocument,
    KnowledgeChunk,
    KnowledgeResult,
    DecisionMemoryItem,
)
from knowledge.documentation_indexer import index_documentation_folder, reindex_all_docs
from knowledge.knowledge_retriever import (
    retrieve_relevant_knowledge,
    retrieve_docs_for_agent,
    retrieve_rules_for_decision,
)
from knowledge.decision_memory import (
    get_entity_decision_memory,
    check_if_action_was_previously_rejected,
    detect_repeated_recommendation,
)

__all__ = [
    "KnowledgeDocument",
    "KnowledgeChunk",
    "KnowledgeResult",
    "DecisionMemoryItem",
    "index_documentation_folder",
    "reindex_all_docs",
    "retrieve_relevant_knowledge",
    "retrieve_docs_for_agent",
    "retrieve_rules_for_decision",
    "get_entity_decision_memory",
    "check_if_action_was_previously_rejected",
    "detect_repeated_recommendation",
]
