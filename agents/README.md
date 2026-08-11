# OSMOS Multi-Agent Supervision Layer (Phases 8.1 - 8.7)

## Overview
The **Multi-Agent Supervision Layer** (`agents/`) transforms OSMOS into a human-supervised intelligent CRM system.

Multi-agent supervision is orchestrated using **LangGraph** (`agents/langgraph_supervision/`), which coordinates 8 specialized analytical and operational supervision agents across stateful graph nodes.

---

## Agent Roster

### Customer Intelligence Domain
1. **Digital Twin Agent (`digital_twin_agent.py`)**: Profile completeness and identity state audit.
2. **CLV Agent (`clv_agent.py`)**: Monetary projections, VIP tiering, and value risk audit.
3. **Churn Risk Agent (`churn_risk_agent.py`)**: Friction detection, complaint occurrences, and churn probability analysis.
4. **Persona Agent (`persona_agent.py`)**: Segment-first persona mapping consistency verification.

### Operational Supervision Domain
5. **Campaign Agent (`campaign_agent.py`)**: Campaign dispatch gaps and response alignment audit.
6. **Journey Agent (`journey_agent.py`)**: Digital Twin lifecycle stage transition and scenario reference.
7. **Database Audit Agent (`database_audit_agent.py`)**: PostgreSQL schema, row count, and orphaned reference audit.
8. **UI/UX Agent (`ui_ux_agent.py`)**: Presentation readiness, PII safety, and demo suitability audit.

---

## Key Architectural Principles

- **LangGraph Orchestration**: LangGraph wraps existing deterministic agents as read-only graph nodes without modifying their analytical algorithms.
- **Domain-Aware Debate Mode**: Conflict detection evaluates agent findings within domain groupings (`Customer Intelligence` vs `Operational Supervision`). Cross-domain status differences (such as `Journey OK` vs `Churn Critical`) do not trigger status conflicts.
- **CLV Validity vs Churn Risk**: `CLV Agent OK` indicates that the CLV model executed validly, not customer health. Low CLV + High Churn is resolved as: *"Retention action should be cost-efficient because churn risk is high but CLV is low."*
- **Database Audit Classification**: A Database Audit warning with 0 orphaned references is classified as a *"demo readiness / initialization warning"*, not a data integrity issue.
- **Knowledge Base RAG Integration**: Integrates RAG context from `knowledge_chunks` to support multi-agent evaluations with historical decision memory.
- **Human Approval Queue**: Submits synthesized Next Best Actions (NBA) to `human_approval_queue` for administrator approval before execution.
