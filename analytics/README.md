# OSMOS Advanced Historical Intelligence (Phase 4)

This folder contains read-only analytical modules querying PostgreSQL database tables to monitor customer lifecycles and predictions over time.

---

## Capabilities

### 1. CLV Trend Alerts (`clv_trend_alerts.py`)
Tracks changes between each entity's latest Customer Lifetime Value (CLV) prediction and their immediately preceding prediction.
* **Alert Levels**:
  * **Low Drop**: Drop between 10% and 20%. Action: *Monitor customer activity*.
  * **Medium Drop**: Drop between 20% and 35%. Action: *Send personalized offer*.
  * **High Drop**: Drop greater than 35%. Action: *Trigger retention campaign*.
* **Explainability**: Allows marketing operators to detect drop trends before customers churn.

### 2. Segment Transition Matrix (`segment_transitions.py`)
Analyzes transitions in customer segment classification over time.
* **Transitions**: Traces segment-to-segment trajectories and classifies them into:
  * **Upgrade** (e.g. *New Customers* ➔ *Growth Potential Clients*)
  * **Downgrade** (e.g. any segment ➔ *Dormant Low-Value Clients*)
  * **Risk Increase** (e.g. *High-Value Loyalists* ➔ *At-Risk Premium Clients*)
  * **Stable** (no change)
  * **New Assignment** (initial classification)
* **Transition Matrix**: Generates a matrix summarizing transition traffic.

### 3. Prediction Drift Monitoring (`prediction_drift.py`)
Detects shifts in the dynamic class predictions distribution.
* **Logic**: Compares the distribution over the last 30 days (current window) against the previous 90 days (baseline window).
* **Levels**: Categorizes class frequency drift as *Low*, *Medium*, or *High* (when drift >= 25%).
* **Lineage**: Detects if client distributions shift over time.

---

## Database Telemetry Requirements
* These features require historical database logs populated through PostgreSQL.
* If running in **Excel mode**, the dashboard will display a notice stating that Advanced Historical Intelligence requires PostgreSQL database tables.
* If running in **PostgreSQL mode** but with insufficient records (e.g., initial setup without run events), the dashboard will safely indicate that more events must be simulated to compute the metrics.
