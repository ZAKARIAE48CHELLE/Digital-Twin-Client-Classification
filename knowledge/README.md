# OSMOS Agent Knowledge Base & Documentation Memory (Phase 8.5)

## Overview
The **Agent Knowledge Base & Documentation Memory Layer** connects OSMOS's 8-Agent Multi-Agent Supervision Layer with:
1. **Internal Documentation**: Heading-based indexing of markdown files in `docs/`.
2. **System Governance Rules**: Immutable rules enforcing read-only agents, human-in-the-loop validation, button-triggered advisory LLMs, stable vs. dynamic personas, and closed-loop campaign simulation.
3. **Decision Memory**: Entity-specific historical memory of prior supervision runs (`agent_runs`, `agent_outputs`) and human approval outcomes (`agent_approval_queue`).

```
                    ┌────────────────────────┐
                    │     docs/ Markdown     │
                    │ & Governance Rules     │
                    └───────────┬────────────┘
                                │ (offline heading indexer)
                                ▼
  ┌───────────────────────────────────────────────────────────┐
  │ knowledge_documents & knowledge_chunks (PostgreSQL/Memory) │
  └─────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
                       Knowledge Retriever
                                │ (evidence citations)
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ 8-Agent Multi-Agent Supervision Layer & Decision Memory     │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
                      Human Approval Queue
```

> 🛡️ **Read-Only & Safety Governance Guarantee**:
> - Documentation indexing and knowledge retrieval are **100% read-only**, deterministic, and offline (zero LLM or internet calls required).
> - Agents **never** write directly to customer entity data (`entities`, `customer_event_history`, etc.).
> - All operational actions require explicit administrative validation in the **Human Approval Queue**.

---

## File Structure

```
knowledge/
├── __init__.py                # Package exports
├── knowledge_schemas.py       # Dataclass schemas (KnowledgeDocument, KnowledgeChunk, KnowledgeResult, DecisionMemoryItem)
├── knowledge_repository.py    # PostgreSQL & in-memory persistence repository for documents and chunks
├── documentation_indexer.py   # Markdown parser, section splitter, chunking & keyword extraction engine
├── knowledge_retriever.py     # Search & relevance engine retrieving documentation snippets and governance rules
├── decision_memory.py         # Read-only decision memory explorer checking prior runs & approval history
├── knowledge_dashboard.py     # Streamlit UI dashboard (Index Status, Knowledge Search, Decision Memory Explorer, Rules)
├── README.md                  # Package technical architecture documentation
└── test_knowledge.py          # Unit test suite verifying indexing, search relevance, decision memory & safety
```

---

## Key Functions

| Module | Function | Description |
| :--- | :--- | :--- |
| `documentation_indexer` | `index_documentation_folder()` | Parses and indexes all markdown files in `docs/`. |
| `documentation_indexer` | `reindex_all_docs()` | Clears existing index and reindexes documentation. |
| `knowledge_retriever` | `retrieve_relevant_knowledge()` | Performs keyword overlap and section matching search. |
| `decision_memory` | `get_entity_decision_memory()` | Retrieves historical agent runs and approval queue outcomes for an entity. |
| `decision_memory` | `check_if_action_was_previously_rejected()` | Checks if a proposed action was previously rejected by an admin. |

---

## Testing

Run Phase 8.5 unit tests:
```bash
python -m unittest knowledge/test_knowledge.py
```
Or run full workspace tests:
```bash
python -m unittest discover -s . -p "test_*.py"
```
