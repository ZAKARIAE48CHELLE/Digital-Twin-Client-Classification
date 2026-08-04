# OSMOS Multi-Agent Supervision Layer (Phase 8.2)

## Overview
The **Multi-Agent Supervision Layer** (Phase 8) transforms OSMOS from a static dashboard into a **supervised intelligent CRM system**.

A central **Multi-Agent Orchestrator** coordinates 8 specialized analytical and operational agents to inspect customer state, Digital Twin evolution, Customer Lifetime Value (CLV), churn risk, persona consistency, campaign history, journey transitions, database integrity, and UI/demo readiness.

---

## Key Architecture Principles

1. **Read-Only First Guarantee**:
   All 8 agents analyze, evaluate risks/opportunities, audit database integrity, and generate advice in pure **READ-ONLY** mode. Agents **never** write to PostgreSQL, modify Excel storage, alter DataFrames, dispatch real/simulated campaigns, or simulate events.

2. **Deterministic Execution First**:
   All core agent evaluations run using pure, high-speed, deterministic Python algorithms. No LLM call is made automatically.

3. **On-Demand Button-Triggered LLM Summaries**:
   An administrator can click **"Generate LLM Executive Supervision Summary"** in the Agent Supervision Center to produce a bilingual (FR/EN) executive report via local Ollama. If Ollama is offline, a structured fallback report is returned gracefully.

4. **Evidence Traceability**:
   Every specialized agent report includes an **Evidence Traceability Matrix** detailing `metric_name`, observed `value`, reference `threshold`, and domain `interpretation`.

---

## Agent Roster & Categories (8 Active Agents)

### Core Customer Intelligence Agents
| Agent Name | Agent ID | Core Role & Responsibilities | Key Metrics & Evidence |
| :--- | :--- | :--- | :--- |
| **Digital Twin Agent** | `digital_twin` | Inspects Digital Twin profile completeness, Prospect vs Client consistency, and event frequency. | `profile_completeness`, `entity_type`, `recent_event_count` |
| **CLV Agent** | `clv` | Evaluates predicted CLV monetary amount, CLV segment, value collapse risk, and VIP protection strategy. | `predicted_clv_mad`, `clv_score`, `clv_segment` |
| **Churn Risk Agent** | `churn` | Detects churn risk probabilities, inactivity thresholds, complaint counts, and sentiment friction points. | `churn_risk_score`, `recency_days`, `complaint_count_90d` |
| **Persona Agent** | `persona` | Verifies segment-first stable persona resolution and clarifies differences between fixed vs dynamic personas. | `customer_segment`, `stable_persona`, `resolution_rule` |

### Operational Supervision Agents
| Agent Name | Agent ID | Core Role & Responsibilities | Key Metrics & Evidence |
| :--- | :--- | :--- | :--- |
| **Campaign Agent** | `campaign` | Inspects campaign dispatches, customer response types, unsubscribed/ignored outcomes, and strategy alignment. | `campaign_dispatch_count`, `latest_campaign_status`, `latest_response_type` |
| **Journey Agent** | `journey` | Inspects customer journey scenarios, step transition sequences (especially `P_DEMO_001`), and trigger event references. | `journey_step_count`, `scenario_status`, `missing_trigger_event_refs` |
| **Database Audit Agent** | `database_audit` | Audits PostgreSQL table completeness, orphaned event references, history versioning, and storage mode fallback status. | `storage_mode`, `digital_twin_snapshots`, `orphaned_event_references` |
| **UI/UX Agent** | `ui_ux` | Evaluates UI presentation readiness, entity demo suitability, presentation mode availability, and demonstration quality. | `demo_entity_suitability`, `presentation_readiness_score`, `has_journey_history` |

---

## File Structure

```
agents/
├── __init__.py               # Package initialization & exports
├── base_agent.py             # Abstract BaseAgent with crash-proof exception handling & read-only guard
├── agent_schemas.py          # Dataclass schemas (AgentContext, AgentOutput, OrchestratorOutput, EvidenceItem)
├── agent_registry.py         # Central agent registry (8 active agents)
├── context_builder.py        # Read-only entity context assembler (Postgres & Excel fallback)
├── orchestrator_agent.py     # Deterministic orchestrator & button-triggered LLM summary engine
├── result_aggregator.py      # Status aggregation, risk/opportunity merging, and Next Best Action rules
├── digital_twin_agent.py     # Digital Twin behavioral & profile completeness agent
├── clv_agent.py              # CLV monetary tier & VIP protection agent
├── churn_agent.py            # Churn probability & friction detection agent
├── persona_agent.py          # Segment-first stable persona verification agent
├── campaign_agent.py         # Campaign dispatch & response alignment agent
├── journey_agent.py          # Customer journey scenario & step reference agent
├── database_audit_agent.py   # PostgreSQL schema & orphaned event reference audit agent
├── ui_ux_agent.py            # UI readiness & demo suitability agent
├── agent_dashboard.py        # Streamlit Agent Supervision Center UI (Presentation mode support)
├── README.md                 # Technical architecture & developer guide
└── test_agents.py            # Comprehensive unit test suite
```

---

## Deterministic Next Best Action Rules

The Orchestrator selects the Next Best Action (NBA) using the following priority hierarchy:
1. **Critical CLV + Critical Churn**: `"URGENT VIP RETENTION: Initiate high-priority executive outreach and service recovery protocol."`
2. **Critical / High Churn Risk ($\ge 0.70$)**: `"RETENTION INTERVENTION: Execute churn prevention campaign with targeted customer incentive."`
3. **Database Orphaned Event References**: `"DATABASE AUDIT AUDIT REQUIRED: Verify PostgreSQL event persistence to fix orphaned foreign key references."`
4. **Journey Incomplete / Stuck**: `"JOURNEY SCENARIO CONTINUATION: Execute remaining stages in Journey Simulator to complete lifecycle tree."`
5. **Warning Churn + Missing Campaign**: `"PREPARE RETENTION CAMPAIGN SIMULATION: High churn risk detected with no active campaign engagement."`
6. **High-Value VIP ($\ge 8000$ MAD)**: `"VIP LOYALTY ENROLLMENT: Apply premium account perks and targeted cross-sell offering."`
7. **Prospect Entity**: `"PROSPECT CONVERSION: Launch personalized introductory onboarding campaign."`
8. **Default Operational Monitoring**: `"AUTOMATED NURTURING: Continue standard monitoring and routine digital campaign dispatches."`

---

## Testing

Run the multi-agent unit test suite:
```bash
python -m unittest agents/test_agents.py
```
Or run full workspace tests:
```bash
python -m unittest discover -s . -p "test_*.py"
```
