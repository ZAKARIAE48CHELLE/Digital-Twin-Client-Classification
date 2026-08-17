# OSMOS LLM-Assisted Action Intelligence Specification

This document specifies the integration, safety rules, validation workflow, and governance principles for **LLM-Assisted Action Intelligence** in **OSMOS**.

---

## 1. Governance & Safety Rules

OSMOS enforces strict safety rules governing all Large Language Model (LLM) operations:

```mermaid
flowchart TD
    UserTrigger[User Clicks Action Button] --> Ollama[Local Ollama / Qwen Client]
    Ollama --> AdvisoryOutput[Advisory Copywriting Draft]
    AdvisoryOutput --> Validation{Structured Payload?}
    
    Validation -->|Yes| BlueprintCheck[Deterministic Blueprint & Rule Normalizer]
    BlueprintCheck -->|Valid| AdminApproval[Human Admin Approval Queue]
    BlueprintCheck -->|Invalid| Fallback[Apply Deterministic Blueprint Copy]
    
    Validation -->|No| Display[Display Text Guidance]
    
    AdminApproval -->|Approved| Execution[Deterministic Execution Layer]
    AdminApproval -->|Rejected| Discard[Draft Discarded]
```

### Mandatory Governance Rules:
1. **Advisory Role Only**: The LLM operates purely in an advisory copywriting capacity. It cannot modify customer records, update database rows, or dispatch real marketing campaigns autonomously.
2. **Button-Triggered Execution**: LLM invocations occur **only** when an administrator explicitly clicks an action button (e.g. "Generate LLM Recommendation", "Generate A/B Variants with LLM"). Zero automatic LLM calls occur on page load, background timers, or inside data fetch routines (`get_data()`).
3. **No Direct Database Writes**: The LLM client never issues `INSERT`, `UPDATE`, or `DELETE` SQL queries directly against database tables.
4. **Deterministic Validation Required**: Any structured payload proposed by an LLM (such as a multi-stage journey scenario plan or A/B variant text) must be parsed, normalized, and validated by deterministic business rules before presentation to an administrator.
5. **Human Approval Mandate**: Admin review and explicit approval are required before any generated action plan or winning variant can be converted into a campaign draft or applied as a historical event.
6. **Local Deployment Privacy**: The LLM runs via a local **Ollama** instance (`qwen3:8b`). Zero customer data or telemetry is transmitted to external cloud APIs.
7. **Deterministic Fallback**: If the local LLM service is offline or unconfigured, times out, or returns incomplete JSON, system modules fall back gracefully to rule-based blueprint logic without crashing the application.
8. **Structured Output Oversight**: Local LLMs (such as Qwen3:8B) do not guarantee valid JSON formatting or complete variant counts. Therefore, OSMOS enforces mandatory JSON repair, schema parsing, field normalization, deterministic fallback completion, and human oversight.

---

## 2. LLM-Assisted Journey Scenario Planner

The **LLM Journey Planner** (`journey/llm_journey_planner.py`) enables administrators to propose candidate lifecycle scenarios for demo entity `P_DEMO_001`.

### Verification Sequence:
1. **Proposal Generation**: LLM returns a structured candidate JSON proposal containing scenario metadata, target stages, behavioral events, and expected state changes.
2. **JSON Repair & Normalization**: Utility functions (`journey/llm_json_utils.py`) clean trailing commas, repair missing brackets, and extract valid JSON payloads.
3. **Deterministic Validation**: `validate_llm_journey_plan()` evaluates candidate plans against 10 strict business rules:
   - Target entity must equal `P_DEMO_001`.
   - Event types must belong to the allowed telemetry catalog.
   - Event offset days must be chronologically non-decreasing.
   - `purchase` events must occur only after conversion to `Client`.
   - VIP stages must contain high-value purchase telemetry ($>1,000$ MAD).
   - Churn stages must contain negative friction signals (`complaint`, `inactivity_period`).
   - Expected segments must map to valid personas in `persona_library`.
   - Payload must contain zero PII or unknown event fields.
4. **Quality Scoring**: Evaluated plans receive a quality score ($0 - 100$) and quality label (`Excellent`, `Acceptable`, `Weak`, `Invalid`).
5. **Admin Approval & Execution**: Valid plans are rendered as visual cards for administrator review. Upon approval, the deterministic `JourneyRunner` applies events and writes `event_history` records to PostgreSQL.

---

## 3. LLM-Assisted A/B Test Variant Generator

The **A/B Test Variant Generator** (`ab_testing/ab_test_variant_generator.py`) enables administrators to generate marketing campaign variants to answer specific business questions.

### Blueprint-Guided LLM Synthesis Architecture:
- **Button-Triggered Execution**: Triggered solely when an administrator clicks "Generate A/B Variants with LLM".
- **Deterministic Blueprints First**: OSMOS constructs deterministic skeletons with pre-assigned variant count (`2` or `3`), labels (`A`, `B`, `C`), offer types (`service_recovery`, `discount`, `vip_perk`), incentive values, and channels.
- **Copywriting Enrichment Only**: The LLM prompt passes the pre-configured blueprints and instructs the LLM strictly to refine variant titles, message text, CTAs, and tones.
- **Variant Merging**: Successfully generated LLM text is merged into matching blueprint variants; any missing or malformed variant text is filled deterministically.
- **Zero Direct Database Write**: Zero DB writes occur during generation.
- **Deterministic Validator**: Candidate variants are validated by `validate_ab_variants()` (max discount 30%, low CLV protection, frustrated client service recovery option mandate, no PII).
- **Digital Twin Simulation**: Validated variants are simulated deterministically by the Digital Twin Response Simulator (`ab_test_evaluator.py`) to compute predicted open, click, conversion, complaint probabilities, churn reduction, CLV lift, and composite response score ($0-100$).
- **Human Approval & Campaign Conversion**: Converting winning variants into simulated campaign drafts or applying response events requires explicit administrator button confirmation.
