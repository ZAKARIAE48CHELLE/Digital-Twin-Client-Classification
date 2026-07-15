# OSMOS Database Intelligence & Admin Dashboard (Phase 3)

This folder contains the database monitoring, metrics querying, and audit log analysis modules of the OSMOS platform.

---

## Folder Structure
```
admin/
├── __init__.py
├── database_dashboard.py # Streamlit UI rendering and visualization
├── database_metrics.py   # Safe SQL metrics and history querying
├── test_database_metrics.py # Unit tests
└── README.md             # Documentation
```

---

## Traceability & Explainability
OSMOS uses this module to transition from single-point, static prediction updates to a fully versioned, historically trackable customer intelligence stream:
- **Historical Recalculations**: Monitor every historical transition of RFM-ES parameters, dynamic classification runs, CLV prediction calculations, and persona assignments.
- **Traceability**: Audit log trails document when actions occur, and capture changed states for debugging and compliance.
- **Explainability**: Historical trends show how event actions (such as a positive social review or purchase event) influence lifetime value curves.

---

## Enabling PostgreSQL Mode
To unlock full monitoring statistics, ensure your environment is configured for PostgreSQL:

```bash
# Enable PostgreSQL storage backend
OSMOS_STORAGE_BACKEND=postgres streamlit run app.py
```

*If PostgreSQL mode is inactive, the dashboard will safely fall back to displaying local Excel file telemetry.*

---

## Phase 4: Advanced Historical Intelligence
Phase 4 extends the admin dashboard with advanced historical telemetry:
* **CLV Trend Alerts**: Visualizes customer values that drop over a specific window of days and indicates recommended marketing actions (e.g. Trigger retention campaign).
* **Segment Transition Matrix**: Pivots previous-to-latest segment transitions and lists detailed transition pathways.
* **Prediction Drift Monitoring**: Compares dynamic class predictions over a 30-day window against a 90-day baseline window to verify model stability.

