import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db import get_connection, test_connection

def check_tables():
    expected_tables = [
        "entities",
        "customer_profiles",
        "digital_twin_snapshots",
        "event_history",
        "rfm_es_scores",
        "classification_predictions",
        "clv_predictions",
        "customer_segments",
        "model_registry",
        "audit_logs"
    ]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Fetch actual tables in the schema
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE';
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print("\nChecking database schema...")
        all_exist = True
        for table in expected_tables:
            if table in existing_tables:
                print(f"  [OK] Table '{table}' exists.")
            else:
                print(f"  [ERROR] Table '{table}' is MISSING.")
                all_exist = False
                
        return all_exist
    except Exception as e:
        print(f"Error checking tables: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def test_transaction_rollback():
    print("\nTesting transaction insert and rollback...")
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Insert a dummy entity
        cursor.execute("""
            INSERT INTO entities (
                entity_id, entity_type, created_at, region, marketing_consent
            ) VALUES (
                'TEST99999', 'Prospect', '2026-07-14', 'Casablanca-Settat', TRUE
            );
        """)
        print("  Test insert into 'entities' succeeded.")
        
        # Verify it exists in this transaction
        cursor.execute("SELECT entity_type FROM entities WHERE entity_id = 'TEST99999';")
        res = cursor.fetchone()
        print(f"  Verification read inside transaction: {res}")
        
        # Roll back transaction
        conn.rollback()
        print("  Rollback succeeded.")
        
        # Verify it no longer exists
        cursor.close()
        cursor = conn.cursor()
        cursor.execute("SELECT entity_type FROM entities WHERE entity_id = 'TEST99999';")
        res = cursor.fetchone()
        if res is None:
            print("  [OK] Entity successfully deleted via rollback.")
            return True
        else:
            print("  [ERROR] Entity still exists after rollback!")
            return False
            
    except Exception as e:
        print(f"  [ERROR] Transaction test encountered error: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def generate_setup_script():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    setup_path = os.path.join(project_root, 'setup.py')
    
    code = """#!/usr/bin/env python3
\"\"\"
OSMOS: Omnichannel Supervised Marketing Optimization System
One-Shot Automated Setup, Database Creation, Data Migration & Environment Configuration Script.

This script installs dependencies, configures environment variables (.env), auto-healing starts
PostgreSQL if needed, creates the target database, applies database schema, and imports initial data.

Usage:
    python setup.py
    python setup.py --db-password mysecretpassword
    python setup.py --non-interactive --db-password postgres
\"\"\"

import os
import sys
import time
import argparse
import getpass
import subprocess
import urllib.parse

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

def print_header(title):
    print("\\n" + "=" * 64)
    print(f"  {title}")
    print("=" * 64)

def print_step(step_num, title):
    print(f"\\n[STEP {step_num}] {title}")
    print("-" * 64)

def prompt_db_credentials(args):
    \"\"\"Interactively prompt user for database credentials if not supplied.\"\"\"
    print_header("OSMOS DATABASE & ENVIRONMENT CONFIGURATION")
    
    db_host = args.db_host or os.environ.get("DB_HOST", "127.0.0.1")
    db_port = args.db_port or os.environ.get("DB_PORT", "5432")
    db_user = args.db_user or os.environ.get("DB_USER", "postgres")
    db_name = args.db_name or os.environ.get("DB_NAME", "osmos_db")
    db_password = args.db_password or os.environ.get("DB_PASSWORD", "")

    if not args.non_interactive:
        print("Please configure your PostgreSQL database connection parameters.")
        print("Press ENTER to keep the default value in brackets [ ].\\n")

        inp_host = input(f"PostgreSQL Host [{db_host}]: ").strip()
        if inp_host:
            db_host = inp_host

        inp_port = input(f"PostgreSQL Port [{db_port}]: ").strip()
        if inp_port:
            db_port = inp_port

        inp_user = input(f"PostgreSQL User [{db_user}]: ").strip()
        if inp_user:
            db_user = inp_user

        inp_name = input(f"Target Database Name [{db_name}]: ").strip()
        if inp_name:
            db_name = inp_name

        if not db_password:
            default_pass_prompt = " [default: postgres]" if not db_password else ""
            pwd_input = getpass.getpass(f"Enter PostgreSQL Password for user '{db_user}'{default_pass_prompt}: ").strip()
            db_password = pwd_input if pwd_input else "postgres"
        else:
            pwd_input = getpass.getpass(f"Enter PostgreSQL Password for user '{db_user}' (leave empty to keep existing password): ").strip()
            if pwd_input:
                db_password = pwd_input
    else:
        if not db_password:
            db_password = "postgres"

    return {
        "DB_HOST": db_host,
        "DB_PORT": db_port,
        "DB_USER": db_user,
        "DB_NAME": db_name,
        "DB_PASSWORD": db_password,
    }

def update_env_files(db_config):
    \"\"\"Write or update .env and database/.env configuration files.\"\"\"
    root_env = os.path.join(PROJECT_ROOT, ".env")
    db_env_dir = os.path.join(PROJECT_ROOT, "database")
    db_env = os.path.join(db_env_dir, ".env")

    if not os.path.exists(root_env):
        print(f"  [NOTE] Root '.env' file not found. Creating new .env file with user-configured credentials...")
    else:
        print(f"  [NOTE] Updating existing '.env' file with latest connection parameters...")

    env_content = f\"\"\"# OSMOS Environment Configuration
# Automatically generated by setup.py

OSMOS_STORAGE_BACKEND=postgres
DB_HOST={db_config['DB_HOST']}
DB_PORT={db_config['DB_PORT']}
DB_NAME={db_config['DB_NAME']}
DB_USER={db_config['DB_USER']}
DB_PASSWORD={db_config['DB_PASSWORD']}

# LLM Assistant Layer Configurations
OSMOS_LLM_ENABLED=true
OSMOS_LLM_PROVIDER=ollama
OSMOS_LLM_MODEL=qwen3:8b
OSMOS_LLM_BASE_URL=http://localhost:11434
OSMOS_LLM_LANGUAGE=fr_en
OSMOS_LLM_TIMEOUT=120
\"\"\"

    os.makedirs(db_env_dir, exist_ok=True)

    with open(root_env, "w", encoding="utf-8") as f:
        f.write(env_content)
    print(f"  [OK] Successfully created root environment file: {root_env}")

    with open(db_env, "w", encoding="utf-8") as f:
        f.write(env_content)
    print(f"  [OK] Successfully created database environment file: {db_env}")

    for k, v in db_config.items():
        os.environ[k] = str(v)
    os.environ["OSMOS_STORAGE_BACKEND"] = "postgres"

def install_python_dependencies(skip_pip=False):
    \"\"\"Install Python packages listed in requirements.txt.\"\"\"
    if skip_pip:
        print("  [SKIP] Skipping pip dependencies installation (--skip-pip specified).")
        return

    req_file = os.path.join(PROJECT_ROOT, "requirements.txt")
    if not os.path.exists(req_file):
        print(f"  [WARNING] requirements.txt not found at {req_file}.")
        return

    print("  Installing Python packages from requirements.txt...")
    cmd = [sys.executable, "-m", "pip", "install", "-r", req_file]
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("  [OK] Python dependencies installed successfully.")
    else:
        print(f"  [WARNING] Pip install exited with code {res.returncode}. Proceeding with setup.")

def auto_start_postgres_windows():
    \"\"\"Attempt auto-starting PostgreSQL service on Windows if stopped.\"\"\"
    if sys.platform != "win32":
        return False

    pg_ctl_path = r"C:\\Program Files\\PostgreSQL\\18\\bin\\pg_ctl.exe"
    pg_data_path = r"C:\\Program Files\\PostgreSQL\\18\\data"

    if not os.path.exists(pg_ctl_path) or not os.path.exists(pg_data_path):
        base_dir = r"C:\\Program Files\\PostgreSQL"
        if os.path.exists(base_dir):
            for item in sorted(os.listdir(base_dir), reverse=True):
                candidate_ctl = os.path.join(base_dir, item, "bin", "pg_ctl.exe")
                candidate_data = os.path.join(base_dir, item, "data")
                if os.path.exists(candidate_ctl) and os.path.exists(candidate_data):
                    pg_ctl_path = candidate_ctl
                    pg_data_path = candidate_data
                    break

    if not os.path.exists(pg_ctl_path) or not os.path.exists(pg_data_path):
        return False

    print(f"  PostgreSQL Auto-Healing Engine: Starting server via '{pg_ctl_path}'...")
    try:
        log_dir = os.path.join(pg_data_path, "log")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "pg_ctl_start.log")

        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_NO_WINDOW = 0x08000000
        flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW

        subprocess.Popen(
            [pg_ctl_path, "start", "-D", pg_data_path, "-l", log_file],
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        time.sleep(3)
        return True
    except Exception as e:
        print(f"  [WARNING] Could not auto-start PostgreSQL service: {e}")
        return False

def create_database_if_missing(db_config):
    \"\"\"Connect to postgres server and create target database if it does not exist.\"\"\"
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    host = db_config["DB_HOST"]
    port = db_config["DB_PORT"]
    user = db_config["DB_USER"]
    password = db_config["DB_PASSWORD"]
    target_db = db_config["DB_NAME"]

    print(f"  Connecting to PostgreSQL server at {host}:{port} as user '{user}'...")
    
    conn = None
    try:
        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname="postgres", connect_timeout=5
        )
    except Exception as e:
        err_str = str(e).lower()
        if "connection refused" in err_str or "could not connect" in err_str:
            print("  PostgreSQL server appears to be offline. Attempting auto-healing server start...")
            auto_start_postgres_windows()
            time.sleep(2)
            try:
                conn = psycopg2.connect(
                    host=host, port=port, user=user, password=password, dbname="postgres", connect_timeout=5
                )
            except Exception as retry_err:
                print(f"\\n  [ERROR] Failed to connect to PostgreSQL server: {retry_err}")
                print("  Please ensure PostgreSQL is installed and running on your system.")
                sys.exit(1)
        else:
            print(f"\\n  [ERROR] PostgreSQL connection failed: {e}")
            print("  Please check your PostgreSQL password and user permissions.")
            sys.exit(1)

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (target_db,))
    exists = cursor.fetchone()

    if not exists:
        print(f"  Target database '{target_db}' does not exist. Creating database '{target_db}'...")
        cursor.execute(f'CREATE DATABASE "{target_db}";')
        print(f"  [OK] Database '{target_db}' created successfully.")
    else:
        print(f"  [OK] Target database '{target_db}' exists.")

    cursor.close()
    conn.close()

def apply_database_schema(db_config):
    \"\"\"Apply database/schema.sql to target database.\"\"\"
    import psycopg2

    host = db_config["DB_HOST"]
    port = db_config["DB_PORT"]
    user = db_config["DB_USER"]
    password = db_config["DB_PASSWORD"]
    target_db = db_config["DB_NAME"]

    schema_file = os.path.join(PROJECT_ROOT, "database", "schema.sql")
    if not os.path.exists(schema_file):
        print(f"  [ERROR] Schema file missing at: {schema_file}")
        sys.exit(1)

    print(f"  Applying schema DDL from database/schema.sql to '{target_db}'...")
    conn = psycopg2.connect(
        host=host, port=port, user=user, password=password, dbname=target_db
    )
    cursor = conn.cursor()

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    cursor.execute(schema_sql)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"  [OK] Schema DDL applied successfully to database '{target_db}'.")

def run_data_migration(db_config, skip_migration=False):
    \"\"\"Run Excel data migration to PostgreSQL.\"\"\"
    if skip_migration:
        print("  [SKIP] Skipping data migration (--skip-migration specified).")
        return

    excel_file = os.path.join(PROJECT_ROOT, "osmos_digital_twin_data.xlsx")
    if not os.path.exists(excel_file):
        print(f"  [WARNING] Excel data file not found at {excel_file}. Skipping migration.")
        return

    print("  Migrating digital twin data from osmos_digital_twin_data.xlsx to PostgreSQL...")
    migration_script = os.path.join(PROJECT_ROOT, "database", "migrate_excel_to_postgres.py")
    
    cmd = [sys.executable, migration_script, "--excel-path", excel_file]
    res = subprocess.run(cmd)

    if res.returncode == 0:
        print("  [OK] Data migration completed successfully.")
    else:
        print(f"  [WARNING] Data migration script exited with code {res.returncode}.")

def verify_installation(db_config):
    \"\"\"Run database query tests and check subsystem health.\"\"\"
    import psycopg2

    print_step(5, "SYSTEM HEALTH & SETUP VERIFICATION")

    host = db_config["DB_HOST"]
    port = db_config["DB_PORT"]
    user = db_config["DB_USER"]
    password = db_config["DB_PASSWORD"]
    target_db = db_config["DB_NAME"]

    try:
        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=target_db
        )
        cursor = conn.cursor()

        tables = [
            "entities", "customer_profiles", "digital_twin_snapshots",
            "rfm_es_scores", "classification_predictions", "clv_predictions",
            "customer_segments", "event_history", "model_registry", "audit_logs",
            "ab_test_experiments", "ab_test_variants", "ab_test_simulated_responses",
            "ab_test_recommendations"
        ]

        print("  Database Table Verification:")
        for tbl in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
            count = cursor.fetchone()[0]
            print(f"    - Table '{tbl}': {count} rows")

        cursor.close()
        conn.close()
        print("  [OK] PostgreSQL Database connection & schema checks passed!")

    except Exception as e:
        print(f"  [ERROR] Verification check failed: {e}")

    # Check Ollama LLM status
    try:
        import urllib.request
        ollama_url = os.environ.get("OSMOS_LLM_BASE_URL", "http://localhost:11434")
        req = urllib.request.Request(f"{ollama_url}/api/tags", headers={"User-Agent": "OSMOS Setup"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                print("  [OK] Local Ollama LLM service detected at http://localhost:11434.")
    except Exception:
        print("  [NOTE] Ollama local LLM service not currently running (optional for copywriting).")

def create_launcher_scripts():
    \"\"\"Create convenience launch scripts for Windows and Unix.\"\"\"
    bat_content = "@echo off\\npython -m streamlit run app.py\\npause\\n"
    bat_file = os.path.join(PROJECT_ROOT, "run_app.bat")
    with open(bat_file, "w", encoding="utf-8") as f:
        f.write(bat_content)
        
    sh_content = "#!/bin/bash\\npython -m streamlit run app.py\\n"
    sh_file = os.path.join(PROJECT_ROOT, "run_app.sh")
    with open(sh_file, "w", encoding="utf-8") as f:
        f.write(sh_content)
    try:
        os.chmod(sh_file, 0o755)
    except Exception:
        pass
    print("  [OK] Created application launchers: run_app.bat / run_app.sh")

def main():
    parser = argparse.ArgumentParser(
        description="OSMOS One-Shot Installation, Database Creation & Setup Script"
    )
    parser.add_argument("--db-host", help="PostgreSQL host (default: 127.0.0.1)")
    parser.add_argument("--db-port", help="PostgreSQL port (default: 5432)")
    parser.add_argument("--db-user", help="PostgreSQL user (default: postgres)")
    parser.add_argument("--db-name", help="Target database name (default: osmos_db)")
    parser.add_argument("--db-password", "-p", help="PostgreSQL user password")
    parser.add_argument("--non-interactive", "-y", action="store_true", help="Run setup non-interactively")
    parser.add_argument("--skip-pip", action="store_true", help="Skip pip install requirements")
    parser.add_argument("--skip-migration", action="store_true", help="Skip data migration from Excel")

    args = parser.parse_args()

    print_header("OSMOS ONE-SHOT PROJECT SETUP & DEPLOYMENT ENGINE")

    db_config = prompt_db_credentials(args)
    update_env_files(db_config)

    print_step(1, "DEPENDENCIES INSTALLATION")
    install_python_dependencies(skip_pip=args.skip_pip)

    print_step(2, "POSTGRESQL DATABASE & SCHEMA INITIALIZATION")
    create_database_if_missing(db_config)
    apply_database_schema(db_config)

    print_step(3, "DATA IMPORT & MIGRATION")
    run_data_migration(db_config, skip_migration=args.skip_migration)

    print_step(4, "LAUNCHERS GENERATION")
    create_launcher_scripts()

    verify_installation(db_config)

    print_header("OSMOS SETUP & MIGRATION COMPLETED SUCCESSFULLY")
    print("To launch the OSMOS platform, run:")
    print("  streamlit run app.py")
    print("  OR double-click run_app.bat (Windows) / ./run_app.sh (Linux/Mac)")
    print("=" * 64 + "\\n")

if __name__ == "__main__":
    main()
"""
    with open(setup_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Generated setup script at {setup_path}")

def main():
    generate_setup_script()
    print("============================================================")
    print("OSMOS Database Connection and Schema Test")
    print("============================================================")
    
    success, message = test_connection()
    if not success:
        print(f"\n[CRITICAL ERROR] Connection test failed: {message}")
        print("\nPlease check your env settings in database/.env or system environment variables.")
        sys.exit(1)
        
    print(f"\n[SUCCESS] Connected to database: {message}")
    
    schema_ok = check_tables()
    tx_ok = test_transaction_rollback()
    
    print("\n------------------------------------------------------------")
    if schema_ok and tx_ok:
        print("DATABASE FOUNDATION TEST PASSED!")
    else:
        print("DATABASE FOUNDATION TEST FAILED. Please resolve the errors above.")
    print("============================================================")
    
    if not (schema_ok and tx_ok):
        sys.exit(1)

if __name__ == "__main__":
    main()
