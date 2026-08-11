# OSMOS Documentation Directory

Welcome to the official technical and architectural documentation package for **OSMOS** (Omnichannel Supervised Marketing Optimization System).

OSMOS is an enterprise-grade, human-supervised Digital Twin CRM and marketing intelligence platform. It integrates customer lifecycle classification, RFM-ES scoring, Customer Lifetime Value (CLV) forecasting, persona modeling, closed-loop campaign simulation, controlled lifecycle journey generation, RAG-driven knowledge memory, multi-agent supervision orchestrated via LangGraph, and executive reporting.

---

## Documentation Structure

The documentation package is organized into specialized analytical and architectural guides:

| Document | Description |
| :--- | :--- |
| [OSMOS Roadmap](OSMOS_Roadmap.md) | Development roadmap detailing completed Phases 1 through 8.7 and future Phase 9 targets. |
| [Technical Architecture](OSMOS_Technical_Architecture.md) | High-level system architecture, multi-agent supervision, LangGraph orchestration, storage abstraction, and PostgreSQL persistence. |
| [Scientific Explanation](OSMOS_Scientific_Explanation.md) | Theoretical foundations, mathematical formulations (RFM-ES, CLV, Churn), and deterministic governance rules. |
| [Data Flow Architecture](OSMOS_Data_Flow.md) | End-to-end data pipeline, state transition sequence, event history tracking, and RAG knowledge retrieval flow. |
| [AI Modules](OSMOS_AI_Modules.md) | Overview of machine learning models, segment-first persona mapping, local LLM integration, and LangGraph multi-agent supervision. |
| [Digital Twin & Persona Modeling](OSMOS_Digital_Twin_and_Persona_Modeling.md) | Specification of the Digital Twin profile architecture, stable business personas, and dynamic clustering. |
| [LLM-Assisted Action Intelligence](OSMOS_LLM_Assisted_Action_Intelligence.md) | Governance framework for button-triggered local LLM guidance, journey planning, validation, and human approval queues. |
| [PostgreSQL & Historical Intelligence](OSMOS_PostgreSQL_and_Historical_Intelligence.md) | Database schema design, audit logs, event persistence, and live connection/concurrency load statistics. |
| [Demo Presentation Guide](OSMOS_Demo_Guide.md) | Step-by-step demonstration walkthrough, demo entity readiness checks (`P_DEMO_001`), and presentation workflows. |

---

## Core System Architectural Principles

1. **Human-Supervised & Advisory AI**: All machine learning predictions, multi-agent debate findings, and LLM proposals operate in an advisory capacity. Zero automated database mutations or campaign dispatches occur without explicit administrator approval.
2. **LangGraph Workflow Orchestration**: Multi-agent supervision is orchestrated as a stateful, modular, inspectable directed graph using LangGraph, wrapping 8 specialized deterministic agents without replacing their core logic.
3. **Domain-Aware Agent Debate**: Conflict detection evaluates agent status within dedicated domains (Customer Intelligence vs Operational Supervision), resolving cross-domain status differences logically and eliminating false contradictions.
4. **Deterministic Storage & Auto-Healing**: PostgreSQL 18 serves as the primary historical persistence layer with an automatic fallback to an Excel storage engine. Concurrency management supports up to 500 connections with connection pool auto-healing.
5. **Traceable Knowledge & Decision Memory**: Internal documentation memory and approval histories are indexed into chunked vector/text stores (`knowledge_documents`, `knowledge_chunks`), enabling agents to leverage historical organizational context.
