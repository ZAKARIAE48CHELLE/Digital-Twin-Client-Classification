# OSMOS A/B Test & Digital Twin Response Simulator (Phase 8.8)

## Overview
The **A/B Test & Digital Twin Response Simulator** (`ab_testing/`) allows administrators to formulate business questions, generate candidate campaign variants, and simulate how a selected Digital Twin profile responds to each variant before committing marketing budgets.

---

## Architectural & Governance Principles

```mermaid
flowchart TD
    Question[Admin Business Question] --> LLMGen[LLM Variant Generator (Optional)]
    LLMGen --> CandidateVars[Candidate Campaign Variants A & B]
    CandidateVars --> Validator[Deterministic Rule Validator]
    
    Validator -->|Validation Failed| ErrorUI[Display Errors & Fix Inputs]
    Validator -->|Validation Passed| Simulator[Digital Twin Response Simulator]
    
    DTProfile[Selected Digital Twin Profile] --> Simulator
    Simulator --> Metrics[Predicted Open, Click, Conversion, Churn & CLV Deltas]
    Metrics --> Evaluator[A/B Test Evaluator]
    
    Evaluator --> WinnerCard[Winning Variant & Recommendation Summary]
    WinnerCard --> Governance[Human-Supervised Actions]
    
    Governance --> SaveRecord[Save Experiment to PostgreSQL]
    Governance --> CampaignDraft[Convert Winner to Campaign Draft]
    Governance --> ApplyEvent[Apply Simulated Response Event (Admin Approved)]
```

### Strict Governance & Safety Rules:
1. **Advisory Role Only**: The local LLM proposes candidate variants only; it does **not** update customer profiles or dispatch real campaigns.
2. **Button-Triggered Execution**: LLM variant generation and simulation runs occur strictly upon explicit user button click. Zero calls occur on page load or inside data retrieval functions.
3. **Deterministic Validation**: Variants undergo 14 strict validation rules (discount ceiling $\le 30\%$, low CLV cost inefficiency blocks, frustrated client service recovery mandate, PII safety checks).
4. **Deterministic Response Simulation**: Digital Twin reaction probabilities, metric deltas, and response scores ($0 - 100$) are calculated using rule-based behavioral domain logic.
5. **Human Approval Mandate**: Creating campaign drafts or logging event history records requires explicit administrator button action.

---

## Database Persistence Tables

- **`ab_test_experiments`**: Experiment metadata, admin question, strategic objective, target segment, and persona.
- **`ab_test_variants`**: Variant titles, message texts, offer types, incentive values, channels, tones, and call-to-actions.
- **`ab_test_simulated_responses`**: Predicted open, click, conversion, complaint probabilities, churn delta, CLV lift, and response score.
- **`ab_test_recommendations`**: Winning variant label, confidence score, recommendation summary, decision reasoning, and risk notes.

---

## Module Component Inventory

- `ab_test_schemas.py`: Dataclass models (`ABExperiment`, `ABVariant`, `SimulatedResponse`, `ABRecommendation`, `ABEvaluationResult`).
- `ab_test_repository.py`: PostgreSQL persistence methods and fallback helpers.
- `ab_test_variant_generator.py`: Local LLM variant generator with fallback rules.
- `ab_test_validator.py`: Deterministic 14-rule variant validation engine.
- `digital_twin_response_simulator.py`: Core Digital Twin behavioral response simulator.
- `ab_test_evaluator.py`: Multi-variant ranking and recommendation synthesis engine.
- `ab_test_dashboard.py`: Streamlit user interface page.
- `test_ab_testing.py`: Comprehensive unit test suite.
