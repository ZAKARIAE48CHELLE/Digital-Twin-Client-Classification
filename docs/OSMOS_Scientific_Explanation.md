# OSMOS — Scientific Explanation & Conceptual Framework

## 1. Executive Summary & Project Identification

* **Project Name**: OSMOS — Optimal Smart Marketing Operation System
* **Domain**: Artificial Intelligence in Customer Relationship Management (CRM) & Marketing Operations
* **System Type**: AI-Powered Digital Twin & Multi-Layered Action Intelligence Platform

### Definition
**OSMOS (Optimal Smart Marketing Operation System)** is an enterprise AI-powered Digital Twin CRM and marketing intelligence platform. It dynamically models individual customers and prospects through continuously evolving digital representations, multi-dimensional predictive score vectors (RFM-ES, CLV, Churn Risk), segment-level persona blueprints, advanced historical audit tracking, and button-triggered local LLM action recommendations.

---

## 2. Core Objectives

The primary scientific and operational objectives of OSMOS are:

1. **Individual-Level Dynamic Representation**: Transform static CRM database records into living, event-driven Digital Twins that evolve in real time with each customer interaction or simulation.
2. **Predictive Value & Risk Estimation**: Provide multi-variate continuous scoring including Recency-Frequency-Monetary-Engagement-Sentiment (RFM-ES) vectors, Customer Lifetime Value (CLV in MAD), and Churn Risk probabilities.
3. **Decoupled Cohort Segmentation & Persona Modeling**: Separate individual entity behavior from group-level persona archetypes to eliminate arbitrary persona tagging and enforce scientific segment resolution (`entity_id` ➔ `customer_segment` ➔ `persona_library` ➔ `persona`).
4. **Historical Intelligence & Drift Auditing**: Track long-term CLV evolution, segment transition matrices, and prediction distribution drift over historical timeframes using PostgreSQL versioning.
5. **Cognitive Action Support**: Integrate local LLMs (Ollama Qwen3-8B / Llama 3.1 8B) as an advisory layer to explain deterministic alerts and suggest high-converting, personalized marketing actions without substituting deterministic core analytics.

---

## 3. Scientific Contribution & Innovation Framework

OSMOS bridges the gap between raw machine learning analytics and actionable marketing operations through a unified 7-layer architecture:

```mermaid
graph TD
    Layer1["1. Data Ingestion & Storage Abstraction<br/>(PostgreSQL + Excel Fallback)"] --> Layer2["2. Feature Engineering & Behavioral Vectorization"]
    Layer2 --> Layer3["3. Deterministic Scoring & Machine Learning<br/>(RFM-ES, CLV Regression, Dynamic Classification)"]
    Layer3 --> Layer4["4. Historical Persistence & Version Audit<br/>(Time-Series Track Records & Drift Monitoring)"]
    Layer4 --> Layer5["5. Individual Digital Twin Builder"]
    Layer5 --> Layer6["6. Segment-First Persona Resolution Chain"]
    Layer6 --> Layer7["7. Local LLM Cognitive Action Intelligence"]
```

### Key Innovations:
- **Hybrid Storage Abstraction**: High-performance PostgreSQL persistence combined with zero-friction Excel fallback for lightweight environments.
- **Single-Entity Snapshot Delta Saves**: Low latency event simulations (< 1s execution) achieved by updating only affected entity rows instead of re-processing full dataset frames.
- **AHP-Weighted Multi-Criteria Scoring**: Analytical Hierarchy Process (AHP) weighting for custom, scientifically sound RFM-ES score synthesis.
- **Deterministic-first AI Architecture**: Machine learning models and mathematical formulas handle 100% of calculations; LLM models are restricted to qualitative explanation and advice generation.
- **Multi-Agent Supervision Layer (Phase 8)**: Coordinates specialized analytical agents (Digital Twin, CLV, Churn Risk, Persona) under a deterministic Orchestrator to synthesize entity-level risks, opportunities, evidence traceability, and Next Best Actions in read-only mode.

---

## 4. Multi-Agent Supervision, Debate & Knowledge Layer (Phase 8.1 - 8.5)

The **Multi-Agent Supervision Layer** extends OSMOS into a coordinated intelligent supervision system. An **Orchestrator Agent** constructs the customer context and delegates analysis to 8 specialized agents responsible for Digital Twin consistency, CLV value evolution, churn risk detection, persona consistency, campaign outcomes, journey step integrity, database auditability, and UI/demo readiness.

Phase 8.4 introduced **Agent Collaboration & Debate Mode**, where agents compare findings, detect risk vs. opportunity conflicts, and synthesize consensus decisions.

Phase 8.5 introduces **Agent Knowledge Base & Documentation Memory**. The multi-agent system can retrieve internal OSMOS documentation, system governance rules, prior agent supervision runs (`agent_runs`, `agent_outputs`), and administrative approval queue history (`agent_approval_queue`). This allows agents to cite system rules, detect previously rejected or approved recommendations, and explain decisions with full auditability. All indexing and retrieval operations remain 100% read-only, deterministic, and human-governed.

