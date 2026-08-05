"""
OSMOS Agent Knowledge Base — Retriever (Phase 8.5)
===================================================
Search and relevance engine retrieving documentation snippets, system rules,
and historical decision memory for agent evidence.

Read-Only Guarantee: Pure analytical retrieval. Zero database or DataFrame mutations.
"""

import logging
from typing import Any, Dict, List, Optional
from knowledge.knowledge_schemas import KnowledgeResult
from knowledge.knowledge_repository import search_knowledge_chunks, is_knowledge_db_available

logger = logging.getLogger("OSMOS_KNOWLEDGE_RETRIEVER")

AGENT_DOC_TOPICS = {
    "digital_twin": "digital twin state snapshot behavioral engagement profile completeness",
    "clv": "customer lifetime value clv monetary score VIP protection loyalty tier",
    "churn": "churn risk friction detection complaint recency probability retention",
    "persona": "stable persona dynamic persona segment representation classification",
    "campaign": "campaign simulation draft dispatch customer response closed loop",
    "journey": "customer journey lifecycle scenario stage transition step trigger",
    "database_audit": "database integrity schema PostgreSQL orphaned event reference",
    "ui_ux": "UI UX readiness presentation mode demo suitability",
}


def score_chunk_relevance(query: str, chunk_dict: Dict[str, Any]) -> float:
    """Calculates relevance score based on keyword overlap and title match."""
    q_words = set(query.lower().split())
    if not q_words:
        return 0.50

    text = (chunk_dict.get("chunk_text") or "").lower()
    title = (chunk_dict.get("chunk_title") or "").lower()

    matches = sum(1 for w in q_words if w in text or w in title)
    title_matches = sum(1 for w in q_words if w in title)

    score = 0.50 + (matches / len(q_words)) * 0.35 + (title_matches / len(q_words)) * 0.15
    return min(0.98, round(score, 2))


def retrieve_relevant_knowledge(
    query: str,
    entity_id: Optional[str] = None,
    context: Any = None,
    limit: int = 5,
) -> List[KnowledgeResult]:
    """Retrieves top relevant documentation chunks and governance rules for a query."""
    raw_chunks = search_knowledge_chunks(query, limit=limit * 2)
    results: List[KnowledgeResult] = []

    for c in raw_chunks:
        score = score_chunk_relevance(query, c)
        results.append(
            KnowledgeResult(
                source_name=c.get("source_name", "docs"),
                section_name=c.get("section_name", c.get("chunk_title", "General")),
                chunk_title=c.get("chunk_title", "Documentation Snippet"),
                chunk_text=c.get("chunk_text", "")[:400] + ("..." if len(c.get("chunk_text", "")) > 400 else ""),
                relevance_score=score,
                reason=f"Matched keywords for query '{query}'",
            )
        )

    # Sort by relevance score
    results.sort(key=lambda r: r.relevance_score, reverse=True)
    return results[:limit]


def retrieve_docs_for_agent(agent_id: str, context: Any = None) -> List[KnowledgeResult]:
    """Retrieves specific documentation snippets relevant to a specialized agent."""
    topic = AGENT_DOC_TOPICS.get(agent_id, "OSMOS multi agent supervision")
    return retrieve_relevant_knowledge(query=topic, limit=2)


def retrieve_rules_for_decision(decision_type: str) -> List[KnowledgeResult]:
    """Retrieves system governance rules applicable to a specific decision type."""
    query = f"governance rule read-only human approval {decision_type}"
    return retrieve_relevant_knowledge(query=query, limit=3)


def retrieve_similar_agent_runs(
    entity_id: Optional[str] = None,
    recommendation_type: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Retrieves historical agent supervision runs from persistent memory."""
    from agents.agent_repository import get_agent_runs
    return get_agent_runs(entity_id=entity_id, limit=limit)


def retrieve_approval_history(
    entity_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Retrieves historical administrative approval items from agent_approval_queue."""
    from agents.agent_repository import get_approval_queue
    return get_approval_queue(status=status, entity_id=entity_id, limit=limit)
