# OSMOS Executive Report Generator (Phase 8.6)

## Overview
The **Executive Report Generator** compiles Digital Twin profile states, ML/RFM/CLV metrics, 8-agent supervision reports, debate consensus decisions, knowledge evidence, approval queue history, campaign dispatches, and journey step traces into clean, professional, downloadable reports (Markdown `.md`, styled HTML `.html`, and PDF `.pdf`).

```
 Digital Twin State  ML / RFM / CLV Metrics  8-Agent Supervision Reports  Debate Consensus (8.4)  Knowledge Evidence (8.5)
         │                       │                         │                        │                        │
         └───────────────────────┴────────────┬────────────┴────────────────────────┴────────────────────────┘
                                              │
                                              ▼
                                 report_context_builder.py
                                              │
                                              ▼
                                    report_templates.py
                                              │
                                              ▼
                                     report_exporter.py
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
            Markdown (.md)              HTML (.html)                PDF (.pdf)
```

> 🛡️ **Read-Only & Safety Governance Guarantee**:
> - Report context assembly and file generation are **100% read-only**, deterministic, and offline.
> - Reports **never** modify customer entity data (`entities`, `customer_event_history`, etc.) or alter DataFrames.
> - LLM polished executive summaries are **strictly button-triggered only** ("LLM Executive Polish").

---

## File Structure

```
reports/
├── __init__.py               # Package exports
├── report_schemas.py          # Dataclass schemas (ReportContext, ReportSection, ReportExportResult)
├── report_context_builder.py # Context assembly for Entity, Agent Run, Journey, and System reports
├── report_templates.py       # Markdown/HTML section renderers for title page, summary, twin state, scores, etc.
├── report_generator.py       # Report compiler building complete structured markdown documents
├── report_exporter.py        # File export engine saving .md, .html, and .pdf files to reports/generated/
├── report_dashboard.py       # Streamlit UI dashboard (Type selection, parameters, preview, download buttons)
├── README.md                 # Technical package architecture documentation
└── test_reports.py          # Phase 8.6 unit test suite
```

---

## Supported Report Types

1. **Entity Executive Report**: Full 360° overview of a single customer or prospect (`entity_id`).
2. **Agent Supervision Run Report**: Executive summary of a specific saved supervision run (`run_id`).
3. **Customer Journey Report**: Customer lifecycle stage transitions and event traces (`scenario_id`).
4. **System Overview Report**: High-level platform health & analytics summary.

---

## Testing

Run Phase 8.6 unit tests:
```bash
python -m unittest reports/test_reports.py
```
Or run full workspace tests:
```bash
python -m unittest discover -s . -p "test_*.py"
```
