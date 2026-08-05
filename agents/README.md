# OSMOS Multi-Agent Supervision Layer (Phase 8.1 - 8.6)

## Overview
The **Multi-Agent Supervision Layer** transforms OSMOS into a **supervised intelligent CRM system**.

A central **Multi-Agent Orchestrator** coordinates 8 specialized analytical and operational agents:
1. **Digital Twin Agent** (Profile & state completeness)
2. **CLV Agent** (Monetary value tiering & VIP protection)
3. **Churn Risk Agent** (Probability of churn & friction detection)
4. **Persona Agent** (Segment-first persona consistency verification)
5. **Campaign Agent** (Campaign dispatch & customer response alignment)
6. **Journey Agent** (Lifecycle scenario & stage transition reference)
7. **Database Audit Agent** (PostgreSQL schema & data integrity audit)
8. **UI/UX Agent** (UI readiness & presentation suitability)

Phase 8.4 introduced **Agent Collaboration & Debate Mode**, Phase 8.5 added **Agent Knowledge Base & Documentation Memory**, and Phase 8.6 implements the **Executive Report Generator**:
```
  Documentation & Governance Rules   Decision Memory History (Runs & Approvals)
                  │                                     │
                  └───────────────────┬─────────────────┘
                                      │
                                      ▼
                          Agent Knowledge Base
                                      │
                                      ▼
                          Specialized Agents (8)
                                      │
                                      ▼
                        Agent Debate Engine (8.4)
                                      │
                                      ▼
                            Orchestrator Output
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                     ▼
          Human Approval Queue              Executive Report Generator (8.6)
                                            (Markdown / HTML / PDF Exports)
```

> 🛡️ **Human-in-the-Loop & Read-Only Governance Guarantee**:
> - Knowledge Base retrieval, debate execution, and report generation are **100% read-only** and **deterministic by default**.
> - Agents detect, explain, cite documentation, and recommend actions but **never** modify customer data or execute campaigns automatically.
> - All operational actions require explicit administrative validation in the **Human Approval Queue**.

---

## Agent Debate Engine Components

| Module | Description | Key Functions |
| :--- | :--- | :--- |
| `debate_schemas.py` | Dataclass schemas for statements, conflicts, and consensus. | `AgentDebateStatement`, `AgentConflict`, `AgentConsensus`, `DebateOutput` |
| `conflict_detector.py` | Rule-based conflict detection engine evaluating risk/opportunity clashes and DB audit overrides. | `detect_all_conflicts()`, `detect_priority_conflicts()`, `detect_status_conflicts()`, `detect_data_quality_conflicts()` |
| `consensus_builder.py` | Synthesis engine calculating consensus status, ranking actions, and computing debate confidence. | `build_consensus()`, `compute_consensus_status()`, `choose_priority_action()`, `compute_debate_confidence()` |
| `debate_engine.py` | Main debate execution engine connecting statements, conflicts, and consensus synthesis. | `run_deterministic_debate()`, `build_agent_statements()`, `prepare_llm_debate_payload()` |

---

## Consensus Status Definitions

- **`Strong Consensus`**: All active agents report aligned findings with zero conflicts detected.
- **`Partial Consensus`**: Minor priority alignments or warnings present without high-severity conflicts.
- **`Conflict Detected`**: Risk vs. opportunity or priority clash detected between active agents (e.g., high CLV vs. high churn).
- **`Critical Conflict`**: Database audit critical alert or critical conflict requiring immediate administrative risk resolution before expansion.
- **`Insufficient Data`**: Majority of active agents lack sufficient historical data.

---

## File Structure

```
agents/
├── __init__.py               # Package initialization & exports
├── base_agent.py             # Abstract BaseAgent with crash-proof exception handling & read-only guard
├── agent_schemas.py          # Dataclass schemas (AgentContext, AgentOutput, OrchestratorOutput, EvidenceItem)
├── debate_schemas.py         # Debate schemas (AgentDebateStatement, AgentConflict, AgentConsensus, DebateOutput)
├── conflict_detector.py      # Rule-based conflict detection engine (Phase 8.4)
├── consensus_builder.py     # Consensus synthesis & priority action selection (Phase 8.4)
├── debate_engine.py          # Deterministic agent debate engine (Phase 8.4)
├── agent_registry.py         # Central agent registry (8 active agents)
├── context_builder.py        # Read-only entity context assembler (Postgres & Excel fallback)
├── agent_repository.py       # Persistence layer for agent_runs, agent_outputs, and approval queue
├── orchestrator_agent.py     # Deterministic orchestrator, LLM summary engine & debate mode wrapper
├── result_aggregator.py      # Status aggregation, risk/opportunity merging, and Next Best Action rules
├── digital_twin_agent.py     # Digital Twin behavioral & profile completeness agent
├── clv_agent.py              # CLV monetary tier & VIP protection agent
├── churn_agent.py            # Churn probability & friction detection agent
├── persona_agent.py          # Segment-first stable persona verification agent
├── campaign_agent.py         # Campaign dispatch & response alignment agent
├── journey_agent.py          # Customer journey scenario & step reference agent
├── database_audit_agent.py   # PostgreSQL schema & orphaned event reference audit agent
├── ui_ux_agent.py            # UI readiness & demo suitability agent
├── agent_dashboard.py        # Streamlit Agent Supervision Center UI (Debate, Memory & Approval tabs)
├── test_agents.py            # 8-agent execution unit test suite
├── test_agent_memory.py      # Agent memory & human approval queue test suite
└── test_agent_debate.py      # Agent collaboration & debate test suite (Phase 8.4)
```

---

## Testing

Run Phase 8.4 Agent Debate unit tests:
```bash
python -m unittest agents/test_agent_debate.py
```
Or run full workspace tests:
```bash
python -m unittest discover -s . -p "test_*.py"
```
