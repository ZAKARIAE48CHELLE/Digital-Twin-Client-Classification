# OSMOS Storage Integration and Abstraction (Phase 2)

This folder contains the abstraction layer decoupling the Streamlit frontend (`app.py`) from local spreadsheet files. It introduces configurable dual-storage engine support (Excel and PostgreSQL) selectable via a feature flag.

---

## Configuration

The active storage engine is governed by the environment variable `OSMOS_STORAGE_BACKEND` which is read from a root `.env` file (copied from `.env.example`).

```ini
OSMOS_STORAGE_BACKEND=postgres
```

Once the `.env` file contains your database credentials and backend selection, the application can be started directly with:

```bash
streamlit run app.py
```

---

## Storage Modes

### 1. Excel Mode (Default)
In this mode, all entity states, calculations, and simulations are read from and written to `osmos_digital_twin_data.xlsx`.

```bash
# Start OSMOS in local Excel mode
OSMOS_STORAGE_BACKEND=excel streamlit run app.py
```

---

### 2. PostgreSQL Mode
In this mode, the platform directly stores and reads all profiles, digital twins, RFM-ES parameters, classification and CLV metrics, and cohort segments inside your PostgreSQL database.

Predictions are saved **historically** (versioned rows per prediction/event run), enabling trend tracking and prediction drift analytics.

#### Prerequisites for PostgreSQL Mode:
Before running in PostgreSQL mode, verify:
1. PostgreSQL server is online and database is created (`CREATE DATABASE osmos_db;`).
2. Schema tables are loaded successfully (`database/schema.sql`).
3. Connection check passes (`python database/test_db_connection.py`).
4. Excel data is fully migrated to PostgreSQL (`python database/migrate_excel_to_postgres.py`).

```bash
# Start OSMOS in PostgreSQL mode
OSMOS_STORAGE_BACKEND=postgres streamlit run app.py
```

---

### 3. Automatic Failover Fallback
If `OSMOS_STORAGE_BACKEND=postgres` is selected but the database connection fails:
- The app will not crash.
- A warning card will display in the Streamlit sidebar highlighting the connection error.
- The app will transparently fail over to the local Excel sheet to guarantee operational continuity.

---

> [!NOTE]
> **Phase 3 Integration**: Phase 3 adds PostgreSQL historical monitoring through the Database Intelligence dashboard.

