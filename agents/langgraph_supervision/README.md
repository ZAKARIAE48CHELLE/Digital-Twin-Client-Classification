# OSMOS LangGraph Multi-Agent Supervision Layer (Phase 8.7)

## Overview
The **LangGraph Supervision Layer** introduces [LangGraph](https://github.com/langchain-ai/langgraph) as an explicit, stateful workflow orchestration engine for OSMOS's 8-agent Multi-Agent Supervision Layer.

Existing deterministic agent classes (`DigitalTwinAgent`, `CLVAgent`, `ChurnRiskAgent`, `PersonaAgent`, `CampaignAgent`, `JourneyAgent`, `DatabaseAuditAgent`, `UIUXAgent`), debate engine, conflict detector, consensus builder, and memory tables remain intact. They are wrapped inside clean, read-only LangGraph nodes.

```
                    ┌─────────────────────────┐
                    │      START WORKFLOW     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                     build_context_node (8.5)
                                 │
                                 ▼
                      run_core_agents_node (4)
                                 │
                                 ▼
                   run_operational_agents_node (4)
                                 │
                                 ▼
                      aggregate_results_node
                                 │
                       ┌─────────┴─────────┐
                       │ debate_mode=True? │
                       └────┬──────────┬────┘
                     YES    │          │    NO
                     ┌──────┘          └──────┐
                     ▼                        ▼
                debate_node              finalize_node
                     │                        │
                     └──────────┬─────────────┘
                                │
                                ▼
                   prepare_approval_actions_node
                                │
                                ▼
                       END (OrchestratorOutput)
```

> 🛡️ **Read-Only Governance & Safety Rules**:
> - LangGraph nodes are **100% read-only**, deterministic, and non-mutating.
> - Nodes do **not** write to customer data (`entities`, `customer_event_history`, etc.) or alter DataFrames.
> - Zero automatic LLM calls inside graph nodes. LLM executive & debate summaries remain **strictly button-triggered**.
> - Automatic fallback to legacy `OrchestratorAgent` if LangGraph encounters an environment or runtime issue.

---

## File Structure

```
agents/langgraph_supervision/
├── __init__.py                # Package exports
├── graph_state.py             # TypedDict SupervisionGraphState schema definition
├── graph_nodes.py             # Read-only node functions wrapping existing OSMOS agents
├── graph_router.py            # Conditional edge routing logic (errors, debate mode)
├── graph_builder.py           # StateGraph compilation engine
├── graph_runner.py            # Entrypoint run_langgraph_supervision() & OrchestratorOutput converter
├── README.md                  # Package technical documentation
└── test_langgraph_supervision.py # Comprehensive unit test suite
```

---

## Testing

Run Phase 8.7 unit tests:
```bash
python -m unittest agents/langgraph_supervision/test_langgraph_supervision.py
```
Or run full workspace tests:
```bash
python -m unittest discover -s . -p "test_*.py"
```
