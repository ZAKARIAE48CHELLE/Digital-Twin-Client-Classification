# OSMOS Digital Twin Modeling Layer (Phase 6)

## Overview
The **Digital Twin** in OSMOS represents the individual-level virtual state of a customer or prospect entity. It captures entity identity, real-time behavioral metrics, multi-dimensional scores, model predictions, and full historical track records.

---

## Scientific Distinction: Digital Twin vs. Persona
In OSMOS, **Digital Twin** and **Persona** are strictly decoupled:
* **Digital Twin**: Belongs to **one specific individual entity** (e.g. `C00001` or `P00005`). It is dynamic, real-time, and backed by event timelines and ML model outputs.
* **Persona**: Belongs to a **customer segment** (e.g. `High-Value Loyalists`). It is a marketing abstraction representing collective behavior, value, risk profiles, and strategic communications.

### Resolution Chain
```
Entity ID (Client / Prospect)
      ↓
Digital Twin (Individual state & score vectors)
      ↓
Scores & Predictions (RFM-ES, CLV, Churn Risk, Classification)
      ↓
Customer Segment (Cohort bucket)
      ↓
Persona (Segment-level marketing representation)
      ↓
Recommended Marketing Action
```

---

## Module Components
- `digital_twin_builder.py`: Combines identity, behavioral state, scores, predictions, persona context, and track records into a unified Digital Twin dictionary.
- `digital_twin_explainer.py`: Provides rule-based deterministic state explainers (Risk, Value, Engagement, Actions) and on-demand LLM cognitive summaries.
- `digital_twin_dashboard.py`: Streamlit explorer page rendering summary cards, multi-dimensional states, history tabs, and persona cards.
