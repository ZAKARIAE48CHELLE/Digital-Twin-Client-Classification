# OSMOS Multi-Agent Supervision Layer (Phase 8.1)

## Overview
The **Multi-Agent Supervision Layer** represents Phase 8 in the evolution of OSMOS. It transforms OSMOS from a static dashboard and recommendation platform into a **supervised intelligent CRM system**.

A central **Multi-Agent Orchestrator** coordinates specialized analytical agents to inspect customer/prospect state, Digital Twin evolution, Customer Lifetime Value (CLV), churn risk probabilities, persona consistency, campaign dispatch outcomes, and journey step transitions.

---

## Key Architecture Principles

1. **Read-Only First Guarantee**:
   Agents analyze, evaluate risks/opportunities, and generate advice. Agents **never** write to PostgreSQL, modify Excel files, mutate DataFrames, or automatically execute customer actions.

2. **Deterministic Execution First**:
   All core agent evaluations run using pure, high-speed, deterministic Python algorithms. No LLM call is made automatically.

3. **On-Demand Button-Triggered LLM Summaries**:
   An administrator can click **"Generate LLM Executive Supervision Summary"** in the Agent Supervision Center to produce a bilingual (FR/EN) executive report via local Ollama. If Ollama is offline, a structured fallback report is returned gracefully.

4. **Evidence Traceability**:
   Every specialized agent report includes an **Evidence Traceability Matrix** detailing `metric_name`, observed `value`, reference `threshold`, and domain `interpretation`.

5. **Separation of Computation and Action**:
   Analytical computation produces structured advice. Execution requires human administrator review and approval.

---

## Agent Roster & Roles

| Agent Name | Agent ID | Core Role & Responsibilities | Key Metrics & Evidence |
| :--- | :--- | :--- | :--- |
| **Orchestrator Agent** | `orchestrator` | Coordinates context assembly, agent execution, risk/opportunity aggregation, and Next Best Action selection. | Global Status, Confidence Score, NBA |
| **Digital Twin Agent** | `digital_twin` | Inspects Digital Twin profile completeness, Prospect vs Client behavioral consistency, and event frequency. | `profile_completeness`, `entity_type`, `recent_event_count` |
| **CLV Agent** | `clv` | Evaluates predicted CLV monetary amount, CLV segment, value collapse risk, and VIP protection strategy. | `predicted_clv_mad`, `clv_score`, `clv_segment` |
| **Churn Risk Agent** | `churn` | Detects churn risk probabilities, inactivity thresholds, complaint counts, and sentiment friction points. | `churn_risk_score`, `recency_days`, `complaint_count_90d` |
| **Persona Agent** | `persona` | Verifies segment-first stable persona resolution and clarifies differences between fixed vs dynamic personas. | `customer_segment`, `stable_persona`, `resolution_rule` |

---

## File Structure

```
agents/
├── __init__.py               # Package initialization & exports
├── base_agent.py             # Abstract BaseAgent with crash-proof exception handling & read-only guard
├── agent_schemas.py          # Dataclass schemas (AgentContext, AgentOutput, OrchestratorOutput, EvidenceItem)
├── agent_registry.py         # Central agent registry & placeholder support
├── context_builder.py        # Read-only entity context assembler (Postgres & Excel fallback)
├── orchestrator_agent.py     # Deterministic orchestrator & button-triggered LLM summary engine
├── result_aggregator.py      # Status aggregation, risk/opportunity merging, and Next Best Action rules
├── digital_twin_agent.py     # Digital Twin behavioral & profile completeness agent
├── clv_agent.py              # CLV monetary tier & VIP protection agent
├── churn_agent.py            # Churn probability & friction detection agent
├── persona_agent.py          # Segment-first stable persona verification agent
├── agent_dashboard.py        # Streamlit Agent Supervision Center UI (Presentation mode support)
├── README.md                 # Technical architecture & developer guide
└── test_agents.py            # Comprehensive unit test suite
```

---

## Deterministic Next Best Action Rules

The Orchestrator selects the Next Best Action (NBA) using the following priority hierarchy:
1. **Critical CLV + Critical Churn**: `"URGENT VIP RETENTION: Initiate high-priority executive outreach and service recovery protocol."`
2. **Critical Churn Risk ($\ge 0.70$)**: `"RETENTION INTERVENTION: Execute churn prevention campaign with targeted customer incentive."`
3. **Warning Churn / Inactivity**: `"SERVICE RECOVERY: Schedule satisfaction survey and re-engagement campaign."`
4. **High-Value VIP ($\ge 8000$ MAD)**: `"VIP LOYALTY ENROLLMENT: Apply premium account perks and targeted cross-sell offering."`
5. **Prospect Entity**: `"PROSPECT CONVERSION: Launch personalized introductory onboarding campaign."`
6. **Missing Context / Profile Deficit**: `"DATA ENRICHMENT: Review profile completeness and verify entity event ingestion."`

---

## How to Add a New Specialized Agent

To add a new agent (e.g. `CampaignAgent` or `JourneyAgent`):

1. Subclass `BaseAgent` in `agents/my_new_agent.py`:
   ```python
   from agents.base_agent import BaseAgent
   from agents.agent_schemas import AgentContext, AgentOutput, EvidenceItem

   class MyNewAgent(BaseAgent):
       def __init__(self):
           super().__init__(
               agent_id="my_new_agent",
               agent_name="My New Agent",
               agent_role="Analyzes domain specific signals",
           )

       def _analyze_implementation(self, context: AgentContext) -> AgentOutput:
           # Pure deterministic logic reading context fields...
           return self.format_output(...)
   ```

2. Register the agent in `agents/agent_registry.py`:
   ```python
   AGENT_REGISTRY["my_new_agent"] = MyNewAgent()
   ```

3. Add unit tests in `agents/test_agents.py`.

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
