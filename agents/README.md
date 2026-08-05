# OSMOS Multi-Agent Supervision Layer (Phase 8.3)

## Overview
The **Multi-Agent Supervision Layer** transforms OSMOS into a **supervised intelligent CRM system**.

A central **Multi-Agent Orchestrator** coordinates 8 specialized analytical and operational agents to inspect customer state, Digital Twin evolution, Customer Lifetime Value (CLV), churn risk, persona consistency, campaign history, journey transitions, database integrity, and UI/demo readiness.

Phase 8.3 introduces **Persistent Agent Memory** (`agent_runs`, `agent_outputs`) and a **Human Approval Queue** (`agent_approval_queue`) for administrative action governance.

> 🛡️ **Human-in-the-Loop Governance Guarantee**:
> Agents recommend actions but never execute them automatically. All operational actions require explicit administrative validation in the Human Approval Queue.

---

## Key Architecture Principles

1. **Read-Only First Guarantee**:
   All 8 agents analyze, evaluate risks/opportunities, audit database integrity, and generate advice in pure **READ-ONLY** mode. Agents **never** write directly to core tables (`entities`, `customer_event_history`, `clv_predictions`, etc.) or alter DataFrames.

2. **Allowed Database Writes**:
   The ONLY database write operations permitted in Phase 8.3 are:
   - Saving agent supervision runs (`agent_runs`)
   - Saving specialized agent outputs (`agent_outputs`)
   - Managing administrative approval items (`agent_approval_queue`)

3. **Deterministic Execution & Optional Button-Triggered LLM**:
   All agent evaluations run deterministically using pure Python logic. Local Ollama LLM executive summaries remain strictly button-triggered ("Generate LLM Executive Supervision Summary").

4. **Evidence Traceability**:
   Every specialized agent report includes an **Evidence Traceability Matrix** detailing `metric_name`, observed `value`, reference `threshold`, and domain `interpretation`.

---

## Database Schema (Phase 8.3 Tables)

| Table Name | Description | Key Columns |
| :--- | :--- | :--- |
| `agent_runs` | Stores auditable multi-agent supervision runs. | `run_id`, `entity_id`, `global_status`, `recommended_next_best_action`, `confidence_score`, `storage_mode` |
| `agent_outputs` | Stores specialized agent outputs linked to a run. | `output_id`, `run_id`, `agent_id`, `status`, `summary`, `observations`, `risks`, `opportunities`, `recommendations`, `evidence` |
| `agent_approval_queue` | Stores pending and processed administrative approval items. | `approval_id`, `run_id`, `entity_id`, `proposed_action_title`, `priority`, `status`, `admin_comment`, `approved_at` |

---

## File Structure

```
agents/
├── __init__.py               # Package initialization & exports
├── base_agent.py             # Abstract BaseAgent with crash-proof exception handling & read-only guard
├── agent_schemas.py          # Dataclass schemas (AgentContext, AgentOutput, OrchestratorOutput, EvidenceItem)
├── agent_registry.py         # Central agent registry (8 active agents)
├── context_builder.py        # Read-only entity context assembler (Postgres & Excel fallback)
├── agent_repository.py       # Persistence layer for agent_runs, agent_outputs, and approval queue
├── orchestrator_agent.py     # Deterministic orchestrator, LLM summary engine & approval action preparer
├── result_aggregator.py      # Status aggregation, risk/opportunity merging, and Next Best Action rules
├── digital_twin_agent.py     # Digital Twin behavioral & profile completeness agent
├── clv_agent.py              # CLV monetary tier & VIP protection agent
├── churn_agent.py            # Churn probability & friction detection agent
├── persona_agent.py          # Segment-first stable persona verification agent
├── campaign_agent.py         # Campaign dispatch & response alignment agent
├── journey_agent.py          # Customer journey scenario & step reference agent
├── database_audit_agent.py   # PostgreSQL schema & orphaned event reference audit agent
├── ui_ux_agent.py            # UI readiness & demo suitability agent
├── agent_dashboard.py        # Streamlit Agent Supervision Center UI (Memory & Approval tabs)
├── README.md                 # Technical architecture & developer guide
├── test_agents.py            # 8-agent execution unit test suite
└── test_agent_memory.py      # Agent memory & human approval queue test suite
```

---

## Human Approval Queue Status Lifecycle

Allowed statuses in `agent_approval_queue`:
- `Pending`: Default status upon creation from agent recommendations.
- `Approved`: Validated by administrator with optional comment.
- `Rejected`: Declined by administrator with audit reason.
- `Converted to Campaign Draft`: (Optional) Approved action converted into a campaign draft in campaign simulator (no real messages sent).
- `Ignored`: Archived without action.

---

## Testing

Run agent memory and approval queue tests:
```bash
python -m unittest agents/test_agent_memory.py
```
Or run full workspace tests:
```bash
python -m unittest discover -s . -p "test_*.py"
```
