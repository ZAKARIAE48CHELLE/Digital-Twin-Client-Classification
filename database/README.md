# OSMOS PostgreSQL Database Foundation

This directory contains the PostgreSQL database schema, connection utility, repository layer, test script, and the Excel migration utility. This foundation is prepared for the transition of data persistence from Excel spreadsheets (`osmos_digital_twin_data.xlsx`) to a robust, normalized relational database structure.

> [!IMPORTANT]
> **Phase 1 creates the database foundation only.**
> `app.py` must **not** be connected to PostgreSQL until `schema.sql`, `test_db_connection.py`, and the migration dry-run all pass successfully.
> Do not modify `app.py` or remove the Excel data sheet during this phase.

---


## Folder Structure

```
database/
├── schema.sql                   # Database schema definitions (10 tables)
├── db.py                       # Connection pooling and transaction management
├── repositories.py             # Relational mapping repository functions
├── migrate_excel_to_postgres.py # Data migration script (Excel -> DB)
├── test_db_connection.py       # Basic database integration test
├── README.md                   # Setup and usage instructions
└── .env.example                # Configuration template
```

---

## 1. Database Creation

To initialize your PostgreSQL server and configure the initial database:

```bash
# Connect to your local PostgreSQL instance and create the database
psql -U postgres -c "CREATE DATABASE osmos_db;"

# Apply the tables defined in the schema file
psql -U postgres -d osmos_db -f database/schema.sql
```

---

## 2. Environment Variables Configuration

Copy `database/.env.example` into a new `.env` file at the project root (`d:\EMSI\PFA-Summer\.env` or `database/.env` if running locally in this folder) and populate it with your local PostgreSQL credentials:

```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=osmos_db
DB_USER=osmos_user
DB_PASSWORD=your_password_here

DATABASE_URL=postgresql://osmos_user:your_password_here@localhost:5432/osmos_db
```

---

## 3. Verifying the Database Connection

Before running the migration utility, run the test script to verify connection pool integrity and check that all 10 expected tables are present:

```bash
python database/test_db_connection.py
```

This script will also execute a test insertion within a transaction and roll it back to verify writing privileges and rollback behavior.

---

## 4. Running the Data Migration

Once connection verification succeeds, run the migration script.

### A. Dry-Run Mode (Analysis only)
Verify mapping sizes and row counts without committing any changes to the database:

```bash
python database/migrate_excel_to_postgres.py --dry-run
```

### B. Full Database Migration
To read the spreadsheets and load all records, run:

```bash
python database/migrate_excel_to_postgres.py --excel-path osmos_digital_twin_data.xlsx
```

*Note: You can use the optional `--truncate` flag to wipe target tables before migration starts.*

---

## Tables Overview

The migration populates the following relational tables:

1. **`entities`**: Identity core records and basic categorical demographic attributes.
2. **`customer_profiles`**: Demographic PII profiles for Clients (age, phone, email).
3. **`digital_twin_snapshots`**: Real-time behavioral snapshots and derived composite scores.
4. **`event_history`**: Audit trail of every simulated action, including JSON changes.
5. **`rfm_es_scores`**: Versioned historical scoring results mapping raw metric indices.
6. **`classification_predictions`**: Versioned historical classification outputs.
7. **`clv_predictions`**: Versioned historical CLV predictions.
8. **`customer_segments`**: Versioned marketing cohorts and recommended actions.
9. **`model_registry`**: Active models and artifacts registered.
10. **`audit_logs`**: System event tracking and missing dependency warnings.

---

## Code Transition in Phase 2

In the next phase, `app.py`'s Excel operations will be modified. The following mapping lists how current functions will be updated to consume repository functions:

- `get_data()` → will query active snapshots, profiles, predictions, and history tables.
- `save_data()` → will execute batch transaction inserts into `digital_twin_snapshots`, `customer_profiles`, `event_history`, and other tables.
- `simulate_event()` → will log event history and predictions to PostgreSQL.
- `update_client_clv()` → will insert new versioned CLV records.
- `update_customer_segmentation()` → will insert new versioned segment records.
