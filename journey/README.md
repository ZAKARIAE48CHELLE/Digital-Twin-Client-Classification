# OSMOS — Digital Twin Journey Tree Simulator (`journey/`)

## 1. Overview & Purpose

The **Digital Twin Journey Tree Simulator** (`journey/`) is the controlled lifecycle generator for OSMOS. It prepares a complete demo entity by creating real PostgreSQL `event_history` records, `journey_steps`, Digital Twin snapshots, predictive histories, segment/persona transitions, and validation checks.

Phase 8.7 adds an **LLM-assisted journey planner**: the LLM proposes a structured scenario, OSMOS validates it deterministically, the admin approves it, and only then the Journey Runner applies valid events into the normal database history.

```
1. New Prospect Discovery ➔ 2. Warm Prospect Engagement ➔ 3. Prospect-to-Client Conversion ➔ 4. VIP Client Growth ➔ 5. Churn-Risk Deterioration ➔ 6. Optional Service Recovery
```

This feature allows administrators, researchers, and supervision agents to visualize how simulated customer events mutate an entity's Digital Twin state, trigger automated score recalculations (RFM-ES, CLV, Churn Risk), update dynamic lifecycle classification, transition customer segments, and resolve segment-first persona blueprints in real time.

---

## 2. Architecture & LLM Safety Workflow

```
LLM proposes journey plan proposal (JSON)
        ↓
Deterministic validator checks 14 structural & domain rules
        ↓
Admin reviews preview, validation status & approves plan
        ↓
Journey Simulator applies valid events with realistic timestamps
        ↓
Real PostgreSQL event_history rows created for P_DEMO_001
        ↓
Digital Twin / RFM / CLV / Classification / Persona updated
        ↓
Journey ready for supervision agents, debate, campaigns, & reports
```

> **Strict Rules**:
> 1. LLM button-triggered ONLY (zero automatic calls, zero calls on page load).
> 2. LLM proposes JSON ONLY. Zero direct database writes.
> 3. Admin approval MANDATORY before applying any proposed plan.
> 4. Deterministic Journey Runner executes valid events.
> 5. All generated events are real `event_history` rows targeting `P_DEMO_001`.

---

## 3. Component Structure

| Module File | Purpose & Responsibilities |
| :--- | :--- |
| **[`journey_repository.py`](file:///D:/EMSI/PFA-Summer/journey/journey_repository.py)** | PostgreSQL repository for `journey_scenarios` and `journey_steps` tables. |
| **[`journey_scenarios.py`](file:///D:/EMSI/PFA-Summer/journey/journey_scenarios.py)** | 6-stage customer lifecycle scenario definitions and event triggers. |
| **[`journey_runner.py`](file:///D:/EMSI/PFA-Summer/journey/journey_runner.py)** | Execution engine for deterministic journey runs, full demo preparation, and plan application. |
| **[`llm_journey_planner.py`](file:///D:/EMSI/PFA-Summer/journey/llm_journey_planner.py)** | Button-triggered LLM journey plan generator proposing structured JSON scenarios. |
| **[`journey_plan_validator.py`](file:///D:/EMSI/PFA-Summer/journey/journey_plan_validator.py)** | Deterministic 14-rule validator inspecting LLM proposals before admin approval. |
| **[`journey_readiness_validator.py`](file:///D:/EMSI/PFA-Summer/journey/journey_readiness_validator.py)** | Demo entity readiness auditor evaluating database integrity, recency, step count, and persona resolution. |
| **[`journey_tree.py`](file:///D:/EMSI/PFA-Summer/journey/journey_tree.py)** | Mermaid tree generator and HTML step card formatting. |
| **[`journey_dashboard.py`](file:///D:/EMSI/PFA-Summer/journey/journey_dashboard.py)** | Streamlit interface with 5 control sections (Preparation, LLM Planner, Readiness Audit, Final State, Visual Tree). |
| **[`test_journey.py`](file:///D:/EMSI/PFA-Summer/journey/test_journey.py)** | Unit test suite covering deterministic execution, readiness checks, LLM planning, and validation rules. |
