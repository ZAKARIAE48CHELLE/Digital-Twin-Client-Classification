# OSMOS: Omnichannel Supervised Marketing Optimization System
## Master Technical & Architectural Specification Document

---

## Document Control & System Identification

- **System Name**: OSMOS (Omnichannel Supervised Marketing Optimization System)
- **Version**: Phase 8.8 (Production Candidate Specification)
- **Classification**: Master Technical Specification & Architecture Manual
- **Target Audience**: Systems Engineers, Data Scientists, Software Architects, and Technical Auditors
- **Formatting Protocol**: Professional Technical Markdown (Strictly Zero Emojis)

---

## Table of Contents

1. Executive Summary & Core Architectural Philosophy
2. System Architecture & High-Level Topologies
3. LangGraph Multi-Agent Supervision & Domain-Aware Debate Engine
4. Predictive Machine Learning Suite & Segment-First Persona Resolution
5. A/B Test & Digital Twin Response Simulator
   - 5.1 System Overview & Operational Capabilities
   - 5.2 Deterministic Controller vs. Advisory LLM Copywriting Layer
   - 5.3 Complete Execution Sequence (12-Step Pipeline)
   - 5.4 Deterministic Variant Blueprints
   - 5.5 LLM Failure Handling & Fallback Strategy
   - 5.6 Streamlit Session State Synchronization
   - 5.7 Dynamic Variant Rendering Architecture
   - 5.8 Digital Twin Behavioral Response Simulation Engine
   - 5.9 Human-Supervised Governance & Auditability
6. PostgreSQL Database Schema & Relational Data Dictionary
7. Local LLM Governance, Privacy, & Safety Engineering
8. RAG Knowledge Memory & Executive Report Generation
9. End-to-End Operational Demonstration Protocols
10. Known Technical Limitations & System Scope Constraints
11. Strategic Roadmap & Future Horizons
12. Comprehensive Revision History & Latest Changelog

---

## 1. Executive Summary & Core Architectural Philosophy

**OSMOS** is an enterprise-grade, human-supervised Digital Twin CRM and marketing intelligence platform designed for privacy-preserving, high-precision customer lifecycle management. Modern enterprise marketing automation systems frequently suffer from brittle heuristic rules, uncalibrated AI hallucinations, and unconstrained automated campaign dispatch risks. OSMOS addresses these structural vulnerabilities by implementing a multi-layered, decoupled system architecture governed by four fundamental engineering principles:

1. **Human-in-the-Loop Governance**: Artificial intelligence, machine learning models, multi-agent supervision workflows, and Large Language Model (LLM) copywriting routines operate strictly in an advisory capacity. Zero autonomous database state mutations or external campaign dispatches occur without explicit human administrative authorization.
2. **Deterministic Control Primacy**: Quantitative decision boundaries, business validation rules, customer lifecycle stage transitions, financial incentive guardrails, and experiment blueprint structures are governed by deterministic algorithms. Generative AI layers are restricted to copywriting enrichment and descriptive explanation.
3. **Domain-Aware Multi-Agent Supervision**: Multi-agent analysis is orchestrated via stateful graph workflows (LangGraph), decoupling core customer intelligence from operational execution supervision and evaluating position conflicts within bounded functional domains to eliminate false positive contradictions.
4. **Local Infrastructure Privacy**: Generative language models (Qwen3:8B via Ollama) and predictive machine learning models execute entirely within local infrastructure. Zero customer telemetry, behavioral metrics, or Personally Identifiable Information (PII) are transmitted to external third-party cloud APIs.

---

## 2. System Architecture & High-Level Topologies

OSMOS is structured as a decoupled, multi-layered architecture separating presentation, multi-agent orchestration, predictive machine learning, decision support simulation, and historical database storage layers.

`mermaid
flowchart TD
    UI[Streamlit Web User Interface] --> Orchestration[LangGraph Supervision Layer]
    UI --> ABModule[A/B Test Simulator Module]
    Orchestration --> CoreAgents[Customer Intelligence Domain Agents]
    Orchestration --> OpAgents[Operational Supervision Domain Agents]
    CoreAgents --> DT[Digital Twin Agent]
    CoreAgents --> CLV[CLV Agent]
    CoreAgents --> Churn[Churn Risk Agent]
    CoreAgents --> Persona[Persona Agent]
    OpAgents --> Campaign[Campaign Agent]
    OpAgents --> Journey[Journey Agent]
    OpAgents --> DBAudit[Database Audit Agent]
    OpAgents --> UIUX[UI/UX Agent]
    Orchestration --> Debate[Domain-Aware Debate Engine]
    Debate --> Consensus[Consensus Synthesis]
    Consensus --> Approval[Human Approval Queue]
    ABModule --> Blueprints[Deterministic Variant Blueprints]
    Blueprints --> LLMClient[Local Ollama Qwen3:8B Client]
    LLMClient --> Validator[Deterministic Rule Validator]
    Validator --> Sync[Streamlit Session State Sync]
    Sync --> ABSim[Digital Twin Response Simulator]
    ABSim --> DBStore[(PostgreSQL Storage Engine)]
    Orchestration --> RAG[RAG Knowledge Base & Memory]
    RAG --> DocStore[(knowledge_chunks Table)]
    Orchestration --> DBStore
    DBStore --> StorageManager[Storage Abstraction & Failover Engine]
    StorageManager -->|Fallback| Excel[(Excel Storage Engine)]
`

---
## 3. LangGraph Multi-Agent Supervision & Domain-Aware Debate Engine

Multi-agent supervision in OSMOS is managed by **LangGraph** (`agents/langgrapf_supervision/`), which coordinates eight specialized analytical agents across two distinct functional domains:

### Customer Intelligence Domain:
1. **Digital Twin Agent (digital_twin)**: Audits behavioral metric completeness, profile integrity, and identity consistency.
2. **CLV Agent (clv)**: Evaluates monetary Customer Lifetime Value projections, value tiering, and high-value collapse risks.
3. **Churn Risk Agent (churn)**: Calculates customer dropout probabilities, complaint frequencies, and inactivity windows.
4. **Persona Agent (persona)**: Verifies deterministic mapping between quantitative customer segments and official business personas.

3## Operational Supervision Domain:
5. **Campaign Agent (campaign)**: Reviews historical campaign dispatches, gap intervals, and customer response alignments.
6. **Journey Agent (journey)**: Tracks lifecycle scenario stage transitions and event trigger sequences.
7. **Database Audit Agent (database_audit)**: Monitors table row counts, orphaned foreign key references, and storage mode status.
8. ** UI/UZ Agent (ui_ux)**: Evaluates demonstration readiness, presentation quality, and PII exposure safety.

3## Domain-Aware Debate Engine Logic:
To prevent false-positive status contradictions, the **Debate Engine** (`agents/debate_engine.py`) enforces strict domain boundaries during conflict resolution:
- **CLV vs. Churn Status**: A status of `CLV Agent OK` indicates model calculation validity, not customer health. Therefore, a combination of `CLV OK` and `Churn Critical` is not flagged as an agent conflict. Instead, the engine synthesizes a contextual insight: "High churn risk with low CLV mandates low-cost automated retention or service recovery rather than expensive financial incentives."
- **Database Readiness Classification**: A `Database Audit Warning with 0 orphaned foreign key references is classified as a demo initialization note rather than a structural data corruption error.

---

## 4. Predictive Machine Learning Suite & Segment-First Persona Resolution

### 4.1 Analytical Machine Learning Models
OSMOS combines three quantitative modeling engines:
0. **RFM-ES Calculator (`analytics/rfm_es_calculator.py`)**: Computes a 5-dimension normalized composite score combining Recency, Frequency, Monetary spend, Engagement intensity, and Satisfaction ratings weighted using Analytic Hierarchy Process (AHP) matrices.
2. **Customer Lifecycle Classification Engine (`models/`)**: Multi-class classification model categorizing entities into five standard cohorts: `Cold Prospect`, `Warm Prospect`, `Active Client`, `VIP Client`, and `Churn Risk Client`.
3. **CLV Forecasting Engine (`analytics/clv_calculator.py`)**: Predicts monetary CLV projections (in Moroccan Dirhams, MAD] and value scores using purchase velocity, average basket size, and dropout probability.

### 4.2 Segment-First Persona Resolution
The **Persona Library** (`personas/`) enforces deterministic mapping from quantitative segments to official business personas:
- `Prospect` / `New Customers` -> `New Explorer`
- `High-Value Loyalists` -> `Premium Loyalist`
- `At-Risk Premium Clients` -> `Silent VIO at Risk`
- `Complaint-Driven Risk Clients` -> `Frustrated Client`
- `Dormant Low-Value Clients` -> `Sleeping Client`
- `Social Advocates` -> `Brand Advocate`
- `Standard Active Clients` -> `Regular Buyer`

---
## 5. A/B Test & Digital Twin Response Simulator

### 5.1 System Overview & Operational Capabilities
The **A/B Test Simulator (`ab_testing/`) enables marketing administrators to formulate strategic business questions, configure multi-variant marketing campaigns (A/B or A/B/C), simulate Digital Twin behavioral reactions, rank competing strategies, and execute human-supervised governance actions.

#### Administrator Workflow Capabilities:
-  Select a target client or prospect entity and inspect real-time Digital Twin profile metrics.
-  Formulate a specific business hypothesis or question.
-  Select a strategic objective (`retention`, `conversion`, `upsell`, `reactivation`, `complaint_recovery`, `engagement`).
-  Select a communication delivery channel (`email`, `sms`, `phone`, `web_notification`, `simulated_only`).
-  Select variant count (`A/B` [2 variants] or `A/B/C` [3 variants]).
-  Synthesize candidate variants via local LLM copywriting or deterministic blueprints.
-  Inspect and manually edit all visible variant fields.
-  Execute Digital Twin behavioral response simulation across all active variants.
-  Evaluate predicted metric deltas, rank strategies, and review winning variant recommendations.
-  Convert the winning strategy into a campaign draft or apply the simulated response as a historical event upon human approval.

---

5.2 Deterministic Controller vs. Advisory LLM Copywriting Layer
A core architectural requirement of OSMOS is that the Large Language Model is **never** the experiment controller. Generative language models excel at natural language copywriting, but lack structural reliability and deterministic state guarantees.

---

### 5.3 Complete Execution Sequence (12-Step Pipeline)
1. **Entity & Question Selection**: Administrator selects customer entity ID directly.
2. **Digital Twin Reading**: System extracts current profile attributes.
3. **Blueprint Construction**: OSMOS builds deterministic variant skeletons (`build_variant_blueprints`).
4. **LLM Copywriting Enrichment**: Local LLM is prompted with blueprints to refine titles, message text, CTAs, and tones.
5. **Validation & Normalization**: Output is parsed (`repair_and_parse_ison`), checked by `validate_ab_variants()`, and normalized.
6. **Fallback Completion**: Any missing or invalid LLM fields are populated from deterministic blueprints.
7. **Session State Synchronization**: Generated fields are synchronized into Streamlit keys (`sync_variants_to_widget_state`) and `st.rerun()` is triggered.
8. **Administrative Editing**: Administrator inspects and edits visible widget inputs in Streamlit UI.
9. **Live Input Collection**: Simulation collects currently visible input values using `collect_variants_from_widget_state()`.
10. **Digital Twin Behavioral Simulation**: Simulator scores all active variants against Digital Twin state.
11. **Strategy Recommendation**: System calculates composite response scores ($0-100$) and recommends winning strategy.
12. **Human Governance Approval**: Administrator confirms conversion to campaign draft or event history insertion.

---

### 5.4 Deterministic Variant Blueprints

To protect the platform against local LLM output instability, OSMOS constructs deterministic variant skeletons prior to LLM synthesis:

#### Blueprint Matrix for A/B Experiments (2 Variants):
- **Variant A Blueprint**: Service Recovery / Apology / Priority Support Resolution (`offer_type = "service_recovery", incentive_value = 0.0`)
- **Variant B Blueprint**: Commercial Incentive / Discount / Goodwill Credit (`offer_type = "discount", incentive_value = 15.0`)

#### Blueprint Matrix for A/B/C Experiments (3 Variants):
- **Variant A Blueprint**: Service Recovery / Apology (`offer_type = "service_recovery", incentive_value = 0.0`)
- **Variant B Blueprint**: Commercial Discount (`offer_type = "discount", incentive_value = 15.0`)
- **Variant C Blueprint**: Contextual Alternative based on segment and persona (`offer_type = "vip_perk", "reactivation", or "onboarding", incentive_value = 0.0`)

5.5 LLM Failure Handling & Fallback Strategy

In OSMOS, local LLM fallback is treated as a routine, safe operational state rather than a system failure. Fallback automatically activates under the following conditions:
-  Local LLM service is offline or unconfigured.
-  LLM inference request times out.
-  LLM returns empty raw text output.
-  LLM returns malformed or unparseable JSON syntax.
-  LLM returns partial or truncated JSON.
-  LLM returns a JSON object with an empty evariants` array.
-  LLM returns fewer variants than requested.
-  LLM output fails semantic domain validation rules.
-  LLM output contains disallowed offer types or unrecognized tone labels.

#### System Status Codes:
- `llm_success_valid`: Full LLM output successfully validated and parsed.
- `llm_partial_merged:X/YX: Partial LLM output merged; remaining completed via blueprints.
- `local_llm_offline`: Local Ollama service unavailable.
- `timeout`: LLM execution exceeded request timeout.
- `empty_llm_output`: LLM returned empty string.
- `invalid_json`: Unparseable JSON syntax.
- `partial_json`: Truncated JSON structure.
- `empty_variants`: Variants array present but empty.
- `incomplete_variant_count`: Fewer variants returned than requested.
- `semantic_validation_failed`: Output violated domain governance guardrails.
- `fallback_used`: Pure deterministic blueprint fallback executed.

5.6 Streamlit Session State Synchronization

#CCCCC Widget Key Naming Pattern:
- `ab_variant_A_title`, `ab_variant_A_message`, `ab_variant_A_offer_type`, `ab_variant_A_incentive_value`, `ab_variant_A_tone`, `ab_variant_A_cta`
- `ab_variant_B_title`, `ab_variant_B_message`, `ab_variant_B_offer_type`, `ab_variant_B_incentive_value`, `ab_variant_B_tone`, `ab_variant_B_cta`
- `ab_variant_C_title`, `ab_variant_C_message`, `ab_variant_C_offer_type`, `ab_variant_C_incentive_value`, `ab_variant_C_tone`, `ab_variant_C_cta`

---

### 5.7 Dynamic Variant Rendering Architecture
Variant field rendering in Streamlit is executed dynamically in a loop over active variant labels:
- **A/B Selection**: Active labels = `["A", "B"]X
™[™\œÈˆÛÛ[[ˆšY[ÊK‚‹H
ŠKÐ‹ÐÈÙ[XÝ[ÛŠŠŽˆXÝ]™HX™[ÈHÈH‹ˆ‹È—V‡&VæFW'226öÇVÖâf–VÆG2’à £Rã‚F–v—FÂGv–â&V†f–÷&Â&W7öç6R6–×VÆF–öâVæv–æP¥F†RF–v—FÂGv–â&W7öç6R6–×VÆF÷"†%÷FW7EöWfÇVF÷"ç–’WfÇVFW26æF–FFRf&–çG2v–ç7B&VÂ×F–ÖR7W7FöÖW"7FFR&ÖWFW'2FòW7F–ÖFR&V†f–÷&ÂÖWG&–73  ¢22226–×VÆFVB÷WGWBÖWG&–73 ¢Ò¢¥&VF–7FVB÷Vâ&ö&&–Æ—G’‚E÷¶÷vçÒB’¢£¢W7F–ÖFVBÆ–¶VÆ–†ööBöbVÖ–Âöæ÷F–f–6F–öâ÷Væ–ær‚CãÒãB’à¢Ò¢¥&VF–7FVB6Æ–6²&ö&&–Æ—G’‚E÷¶6Æ–6·ÒB’¢£¢W7F–ÖFVB6ÆÂ×FòÖ7F–öâ6Æ–6²&ö&&–Æ—G’‚CãÒãB’à¢Ò¢¥&VF–7FVB6öçfW'6–öâ&ö&&–Æ—G’‚E÷¶6öçgÒB’¢£¢W7F–ÖFVBW&6†6Rö66WFæ6R&ö&&–Æ—G’‚CãÒãB’à¢Ò¢¥&VF–7FVB6ö×Æ–çB&ö&&–Æ—G’‚E÷¶6ö×ÒB’¢£¢W7F–ÖFVBæVvF—fRg&–7F–öâö6ö×Æ–çB&ö&&–Æ—G’‚CãÒãB’à¢Ò¢¤6‡W&â&—6²FVÇF…ÄFVÇF÷¶6‡W&çÒB’¢£¢&VF–7FVB66÷&R6†ævR–â6‡W&â&ö&&–Æ—G’à¢Ò¢¤4ÅbÖöæWF'’FVÇF…ÄFVÇF÷´4ÅgÒB’¢£¢&VF–7FVBÖöæWF'’4Åd’Æ–gB–âÔBà¢Ò¢¥$dÒÔU2FVÇF…ÄFVÇF÷µ$d×ÒB’¢£¢&VF–7FVB6ö×÷6—FRVævvVÖVçB66÷&R6†ævRà¢Ò¢¥6F—6f7F–öâFVÇF…ÄFVÇF÷·6GÒB’¢£¢&VF–7FVB7W7FöÖW"&Wf–Wr66÷&R6†ævRà¢Ò¢¤6ö×÷6—FR&W7öç6R66÷&R‚E5÷·&W7ÒB’¢£¢÷fW&ÆÂ7G&FVw’&æ¶–ær66÷&R‚CÒB’à £Rã’‡VÖâÕ7WW'f—6VBv÷fW&ææ6RbVF—F&–Æ—G¢Ô'WGFöâ×G&–vvW&VBW†V7WF–öâv—F‚¦W&òWFöÖFVBF—7F6‚à¢Ò‡VÖâ&÷fÂÖæFFRf÷"6×–vâG&gB6öçfW'6–öâæBWfVçBÆ–6F–öâà ¢ÒÒÐ  ## 6. PostgreSQL Database Schema & Relational Data Dictionary

OSMOS maintains 20 relational storage tables in PostgreSQL 18. Below is the explicit data dictionary for the four A/B testing tables:

``mermaid
erDiagram
    entities ||--o{ ab_test_experiments : tests
    ab_test_experiments ||--o{ ab_test_variants : contains
    ab_test_experiments ||--o{ ab_test_simulated_responses : measures
    ab_test_experiments ||--o{ ab_test_recommendations : recommends
```

### 6.1 `ab_test_experiments`
Stores experiment metadata, target entity, business question, objective, channel, variant count, status, and creation timestamps.
- `experiment_id` (SERIAL, Primary Key): Unique experiment identifier.
- `entity_id` (VARCHAR(50), FK -> `entities.entity_id`): Target customer/prospect entity ID.
- `experiment_name` (VARCHAR(255)): Descriptive experiment title.
- `admin_question` (TEXT): Business hypothesis or question posed by the administrator.
- `objective` (VARCHAR(50)): Strategic objective (`retention`, `conversion`, `upsell`, `reactivation`, `complaint_recovery`, `engagement`).
- `target_segment` (VARCHAR(100)): Target customer segment at time of test formulation.
- `target_persona` (VARCHAR(100)): Target customer persona at time of test formulation.
- `status` (VARCHAR(50)): Experiment state (`Simulated`, `Converted to Draft`, `Event Applied`).
- `llm_generated` (BOOLEAN): Flag indicating whether variant copy was synthesized via local LLM.
- `created_at` (TIMESTAMP WITH TIME ZONE): Experiment setup timestamp.

### 6.2 `ab_test_variants`
Stores variant definitions including variant label, title, message text, offer type, incentive value, tone, channel, call to action, and deterministic validation status.
- `variant_id` (SERIAL, Primary Key): Unique variant record identifier.
- `experiment_id` (INTEGER, FK -> ab_test_experiments.experiment_id): Parent experiment link.
- `variant_label` (VARCHAR(10)): Variant label (`A`, `B`, or `C`).
- `variant_title` (VARCHAR(255)): Short title for the variant.
- `message_text` (TEXT): Customer-facing copy text.
- `offer_type` (VARCHAR(50)): Offer classification (`none`, `service_recovery`, `discount`, `goodwill_credit`, `reactivation`, `vip_perk`, (hhybrid`).
-  incentive_value` (NUMERIC(10,2)): Numerical financial incentive value.
- `channel` (VARCHAR(50)): Communication channel (email, sms, phone, web_notification, simulated_only).
- `tone` (VARCHAR(50)): Strategic tone (empathetic, commercial, informational, exclusive, reassuring).
- `call_to_action` (VARCHAR(100)): Action button/link text.
- `expected_behavior` (TEXT): Hypothesized behavioral reaction.
-  is_valid` (BOOLEAN): Result of deterministic rule validation check.
- `validation_warnings` (JSONB): Array of rule validation warnings or notes.
- `created_at` (TIMESTAMP WITH TIME ZONE): Creation timestAmp.html

### 6.3 `ab_test_simulated_responses`
Stores simulated Digital Twin behavioral response metrics and composite scores for each variant.
- `response_id` (SERIAL, Primary Key): Unique response record identifier.
- `experiment_id` (INTEGER, FK -> ab_test_experiments.experiment_id): Parent experiment link.
- `variant_id` (INTEGER, FK -> ab_test_variants.variant_id): Linked variant identifier.
- `variant_label` (VARCHAR(10)): Variant label (`A`, bB`, or `C`).
- `simulated_response_type` (VARCHAR(50)): Modeled outcome (`Opened`, `Clicked`, `Converted`, `Complained`, `Ignored`).
- `predicted_open_probability` (NUMERIC(5,4)): Estimated open probability ($0.0 - 1.0$).
- `predicted_click_probability` (NUMERIC(5,4)): Estimated click probability ($0.0 - 1.0$).
- `predicted_conversion_probability` (NUMERIC(5,4)): Estimated conversion probability ($0.0 - 1.0$).
- `predicted_complaint_probability` (NUMERIC(5,4)): Estimated complaint probability ($0.0 - 1.0$).
- `predicted_churn_delta` (NUMERIC(5,4)): Estimated churn risk score change.
- `predicted_clv_delta` (NUMERIC(12,2)): Estimated monetary CLVI lift in MAD.
- `predicted_rfm_delta` (NUMERIC(5,4)): Estimated RFM2composite score change.
- `predicted_satisfaction_delta` (NUMERIC(5,4)): Estimated satisfaction rating change.
- `response_score` (NUMERIC(5,2)): Composite evaluation score ($0 - 100$).
- `created_at` (TIMESTAMP WITH TIME ZONE): Simulation timestamp.

### 6.4 `ab_test_recommendations`
Stores executive decision recommendations, winning variant selection, confidence scores, decision reasons, and risk notes.
- `recommendation_id` (SERIAL, Primary Key): Unique recommendation record identifier.
- `experiment_id` (INTEGER, FK -> ab_test_experiments.experiment_id): Parent experiment link.
- `winning_variant_id` (INTEGER, FK -> ab_test_variants.variant_id): Winning variant identifier.
- `winning_variant_label` (VARCHAR(10)): Label of recommended variant (`A`, bB`, or `C`).
- `confidence_score` (NUMERIC(5,4)): Algorithmic confidence probability ($0.0 - 1.0$).
- `recommendation_summary` (TEXT): Executive summary of the winning strategy.
- `decision_reason` (TEXT): Analytical justification explaining why this variant won.
- `risk_notes` (TEXT): Risk assessment notes and operational caveats.
- `created_at` (TIMESTAMP WITH TIME ZONE): Recommendation timestamp.

---

## 7. Local LLM Governance, Privacy, & Safety Engineering
-  Local Execution Target: Ollama running `qwen3:8B` on local infrastructure (`http://127.0.0.1:11434`).
-  Zero Cloud Transmissions: All data processing remains local; no telemetry is sent to external APIs.
-  Inference Parameter Bounds: `temperature = 0.1`, `num_predict = 500` (for A/B) or `750` (for A/B/C), `num_ctx = 4096`, `stream = False`, `format = "json"`.
-  Output Parsing & Normalization: Multi-endpoint text extraction (`_extract_ollama_text`), JSON repair (`repair_and_parse_json`), and field normalization (`normalize_offer_type`, `normalize_tone`) process raw model output.
-  Human Oversight: LLM proposals are rendered as draft candidates requiring explicit administrator button approval before persistence or campaign conversion.
´´-

## 8. RAG Knowledge Memory & Executive Report Generation
### 8.1 RAG Knowledge Memory
- Storage Tables: `cnowledge_documents` and `knowledge_chunks`.
-  Retrieval Engine: Indexes technical manuals, business rules, and human approval logs to provide historical organizational context during agent supervision.

### 8.2 Executive Report Generator
- Supported Formats: Markdown, HTML, and standalone PDF.
-  Supported Scope: Entity Executive Reports, Agent Run Reports, Journey Reports, and System Overview Reports.

---

## 9. End-to-End Operational Demonstration Protocols
### 9.1 Multi-Agent Supervision Protocol (10 Steps)
1. Start Streamlit application (`streamlit run app.py`).
2. Open Journey Simulator page.
3. Prepare Full Demo Entity `P_DEMO_001`.
4. Generate LLM Journey Plan.
5. Validate and approve plan.
6. Apply scenario to `P_DEMO_001`.
7. Open Agent Supervision Center.
8. Select LangGraph Workflow Engine.
9. Enable Knowledge Memory and Domain Debate Mode.
10. Execute Multi-Agent Analysis and review consensus.

### 9.2 A/B Test Simulator Protocol (14 Steps)
1. Open A/B Test Simulator page.
2. Select target entity `P_DEMO_001`.
3. Confirm Digital Twin state (`Complaint-Driven Risk Clients` / `Frustrated Client`).
4. Enter business question: "Should we use a discount or a service recovery apology?"
5. Select objective: `retention`.
6. Select channel: `email`.
7. Select variant count: `A/B/C (3 Variants)`.
8. Click **Generate A/B Variants with LLM**.
9. Verify that fields for Variant A, B, and C are populated in UI widgets.
10. Manually edit visible variant fields if desired.
11. Click **Run Digital Twin Response Simulation**.
12. Review winning variant recommendation, confidence score, metrics table, and decision reason.
13. Click **Convert Winner to Campaign Draft** after administrative review.
14. Click **Apply Response as Event (Admin Approval)** to write historical event record upon approval.

---

## 10. Known Technical Limitations & System Scope Constraints
1. **Local LLM Output Instability**: Local language models (such as Qwen3:8B) may produce malformed or truncated JSON. OSMOS mitigates this using mandatory deterministic blueprints and field normalization.
2. **Predictive Simulation vs. Real Trials**: Digital Twin response scoring is a predictive decision-support simulation, not a real online randomized controlled trial.
3. **Data Quality Dependence**: Simulation precision depends on the completeness of historical Digital Twin snapshot data.
4. **Deterministic Fallback Requirement**: System operation relies on fallback logic when local LLM services are offline or slow.
5. **Streamlit State Management**: Streamlit widget keys must be explicitly synchronized before rendering to avoid stale UI inputs.

---

## 11. Strategic Roadmap & Future Horizons
1. **Real Measured A/B Testing**: Ingest observed customer campaign responses to benchmark predictive simulations against empirical trials.
2. **Causal Uplift Modeling*i: Integrate causal estimators (T-Learner / X-Learner) to quantify true Individual Treatment Effects (ITE).
3. **Native Constrained Decoding*i: Implement schema-constrained decoding libraries (Outlines / Guidance) for local LLMs.
4. **Advanced Behavioral Modeling**: Deep neural state-transition estimators for fine-grained multi-touch response modeling.
5. **Enterprise CRM Connectors**: Direct integration connectors for Salesforce Marketing Cloud, Braze, and HubSpot upon approval.
6. **Automated PDF Experiment Reports**: Automated executive decision reports summarizing A/B test outcomes.
7. **Role-Based Access Control (RBAC)**: Fine-grained permissions for marketing managers, data scientists, and administrative approvers.

---

## 12. Comprehensive Revision History & Latest Changelog

### System Changelog â€” Phase 8.8 Updates:
- Integrated A/B Test & Digital Twin Response Simulator documentation.
- Architected deterministic variant blueprints (`build_variant_blueprints`), enforcing deterministic control over experiment structure while restricting local LLM to copywriting assistance.
- Documented LLM failure handling and fallback strategies across timeouts, empty output, invalid JSON, partial JSON, and incomplete variant counts.
-  Documented Streamlit session_state widget synchronization (`sync_variants_to_widget_state`, `collect_variants_from_widget_state`).
-  Documented dynamic rendering architecture for A/B (2 variants) and A/B/C (3 variants) configurations.
- Defined PostgreSQL database schema for four A/B testing tables (`ab_test_experiments`, abtest_variants`, ab_test_simulated_responses`, ab_test_recommendations`).
- Established governance rules requiring explicit human administrative approval for campaign draft conversion and event application.
- Added 14-step A/B Test Simulator demonstration walkthrough protocol.
- Updated system limitations and future research roadmap.
