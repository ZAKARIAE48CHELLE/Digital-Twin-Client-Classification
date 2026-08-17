# OSMOS Documentation Directory

Welcome to the official technical and architectural documentation package for **OSMOS** (Omnichannel Supervised Marketing Optimization System).

OSMOS is an enterprise-grade, human-supervised Digital Twin CRM and marketing intelligence platform. It integrates customer lifecycle classification, RFM-ES scoring, Customer Lifetime Value (CLV) forecasting, persona modeling, closed-loop campaign simulation, controlled lifecycle journey generation, RAG-driven knowledge memory, multi-agent supervision orchestrated via LangGraph, A/B testing and Digital Twin response simulation, executive reporting, and database concurrency management.

---

## Documentation Index

| Document | Description |
| :--- | :--- |
| [OSMOS Complete Project Documentation](OSMOS_Complete_Project_Documentation.md) | Consolidated master technical specification document covering all system modules, architecture, A/B simulator blueprints, database dictionary, demo protocols, and changelog. |
| [OSMOS Roadmap](OSMOS_Roadmap.md) | Development roadmap detailing completed Phases 1 through 8.8 and future Phase 9 production deployment targets. |
| [Technical Architecture](OSMOS_Technical_Architecture.md) | High-level system architecture, multi-agent supervision, LangGraph orchestration, storage abstraction, and PostgreSQL persistence. |
| [Scientific Explanation](OSMOS_Scientific_Explanation.md) | Theoretical foundations, mathematical formulations (RFM-ES, CLV, Churn), and deterministic governance rules. |
| [Data Flow Architecture](OSMOS_Data_Flow.md) | End-to-end data pipeline, state transition sequence, event history tracking, and RAG knowledge retrieval flow. |
| [AI Modules](OSMOS_AI_Modules.md) | Overview of machine learning models, segment-first persona mapping, local LLM integration, A/B response simulator, and LangGraph supervision. |
| [Multi-Agent Supervision & Debate](OSMOS_Multi_Agent_Supervision_and_Debate.md) | Detailed guide on 8 supervision agents, LangGraph graph topology, domain-aware debate rules, and approval queues. |
| [Executive Reports & RAG Knowledge](OSMOS_Executive_Reports_and_RAG_Knowledge.md) | Architectural guide for RAG Knowledge Base memory, document indexing, and multi-format Executive Reports (MD, HTML, PDF). |
| [API & Database Schema Data Dictionary](OSMOS_API_and_Database_Dictionary.md) | Complete schema specification and data dictionary for all 20 PostgreSQL relational tables including A/B experiment tables. |
| [Digital Twin & Persona Modeling](OSMOS_Digital_Twin_and_Persona_Modeling.md) | Specification of the Digital Twin profile architecture, stable business personas, and dynamic clustering. |
| [LLM-Assisted Action Intelligence](OSMOS_LLM_Assisted_Action_Intelligence.md) | Governance framework for button-triggered local LLM guidance, A/B blueprint synthesis, validation, and human approval queues. |
| [PostgreSQL & Historical Intelligence](OSMOS_PostgreSQL_and_Historical_Intelligence.md) | Database schema design, audit logs, event persistence, and live connection/concurrency load statistics. |
| [Demo Presentation Guide](OSMOS_Demo_Guide.md) | Step-by-step demonstration walkthrough, demo entity readiness checks (`P_DEMO_001`), and 14-step A/B simulator protocol. |

---

## Core System Architectural Principles

1. **Human-Supervised & Advisory AI**: All machine learning predictions, multi-agent debate findings, LLM copywriting proposals, and A/B variant simulations operate in an advisory capacity. Zero automated database mutations or campaign dispatches occur without explicit administrator approval.
2. **Deterministic Variant Blueprints**: In the A/B Test Simulator, the deterministic system controls experiment structure (variant count, labels, offer types, incentive values, channel), while the local LLM acts strictly as a copywriting assistant.
3. **LangGraph Workflow Orchestration**: Multi-agent supervision is orchestrated as a stateful, modular, inspectable directed graph using LangGraph, wrapping 8 specialized deterministic agents without replacing their core logic.
4. **Domain-Aware Agent Debate**: Conflict detection evaluates agent status within dedicated domains (Customer Intelligence vs Operational Supervision), resolving cross-domain status differences logically and eliminating false contradictions.
5. **Deterministic Storage & Auto-Healing**: PostgreSQL 18 serves as the primary historical persistence layer with an automatic fallback to an Excel storage engine. Concurrency management supports up to 500 connections with connection pool auto-healing.
6. **Traceable Knowledge & Decision Memory**: Internal documentation memory and approval histories are indexed into chunked vector/text stores (`knowledge_documents`, `knowledge_chunks`), enabling agents to leverage historical organizational context.
