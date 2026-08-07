import os
import time
import logging
import subprocess
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OSMOS_DB")

_last_auto_start_time = 0.0


def get_connection_string():
    """Build connection string from environment variables or DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url
        
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ.get("DB_NAME", "postgres")
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASSWORD", "postgres")
    
    missing = []
    if not host: missing.append("DB_HOST")
    if not name: missing.append("DB_NAME")
    if not user: missing.append("DB_USER")
    if not password: missing.append("DB_PASSWORD")
    
    if missing:
        raise ValueError(
            f"Missing required database environment variables: {', '.join(missing)}. "
            "Please check database/.env.example and populate your environment."
        )
        
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def check_and_apply_schema():
    """Checks if public.entities table exists; if missing, auto-applies schema.sql."""
    try:
        conn = psycopg2.connect(get_connection_string())
        cur = conn.cursor()
        cur.execute("SELECT to_regclass('public.entities');")
        res = cur.fetchone()
        table_exists = res and res[0] is not None
        cur.close()

        if not table_exists:
            logger.info("Database table 'public.entities' missing. Auto-applying schema DDL...")
            schema_file = os.path.join(os.path.dirname(__file__), "schema.sql")
            if os.path.exists(schema_file):
                with open(schema_file, "r", encoding="utf-8") as f:
                    ddl = f.read()
                cur = conn.cursor()
                cur.execute(ddl)
                conn.commit()
                cur.close()
                logger.info("PostgreSQL schema DDL applied successfully.")
        conn.close()
    except Exception as e:
        logger.warning(f"Auto schema check warning: {e}")


def ensure_postgres_server_running() -> bool:
    """
    Auto-healing engine: Automatically launches PostgreSQL server on Windows if stopped.
    Uses process detachment (DETACHED_PROCESS) to prevent Streamlit reloads from terminating postgres.
    """
    global _last_auto_start_time
    now = time.time()
    if now - _last_auto_start_time < 15.0:
        return False

    _last_auto_start_time = now

    pg_ctl_path = r"C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe"
    pg_data_path = r"C:\Program Files\PostgreSQL\18\data"

    if not os.path.exists(pg_ctl_path) or not os.path.exists(pg_data_path):
        base_dir = r"C:\Program Files\PostgreSQL"
        if os.path.exists(base_dir):
            for item in sorted(os.listdir(base_dir), reverse=True):
                candidate_ctl = os.path.join(base_dir, item, "bin", "pg_ctl.exe")
                candidate_data = os.path.join(base_dir, item, "data")
                if os.path.exists(candidate_ctl) and os.path.exists(candidate_data):
                    pg_ctl_path = candidate_ctl
                    pg_data_path = candidate_data
                    break

    if not os.path.exists(pg_ctl_path) or not os.path.exists(pg_data_path):
        logger.warning("PostgreSQL auto-start engine: pg_ctl.exe or data directory not found.")
        return False

    logger.info(f"PostgreSQL Auto-Healing Engine: Starting independent detached server via '{pg_ctl_path}'...")
    try:
        log_file = os.path.join(pg_data_path, "server.log")
        
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

        conn_str = get_connection_string()
        for attempt in range(1, 15):
            time.sleep(1)
            try:
                conn = psycopg2.connect(conn_str)
                conn.close()
                logger.info(f"PostgreSQL Auto-Healing Engine: Server online and ready after {attempt}s!")
                check_and_apply_schema()
                return True
            except Exception:
                pass
    except Exception as e:
        logger.error(f"PostgreSQL Auto-Healing Engine failed to start server: {e}")

    return False


def get_connection():
    """Get a raw connection to the PostgreSQL database with auto-healing fallback."""
    conn_str = get_connection_string()
    try:
        conn = psycopg2.connect(conn_str)
        return conn
    except Exception as e:
        err_msg = str(e).lower()
        if "connection refused" in err_msg or "could not connect" in err_msg or "starting up" in err_msg:
            logger.warning("PostgreSQL connection lost or refused; triggering Auto-Healing Engine...")
            if ensure_postgres_server_running():
                try:
                    return psycopg2.connect(conn_str)
                except Exception as retry_err:
                    logger.error(f"PostgreSQL connection retry failed: {retry_err}")
                    raise retry_err
        logger.error(f"Failed to connect to the database: {e}")
        raise


@contextmanager
def get_cursor(commit=True):
    """Context manager for obtaining a database cursor, handling transactions automatically."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction error, rolled back: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


@contextmanager
def transaction():
    """Context manager to wrap operations in a single connection transaction."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Transaction failed, rolled back: {e}")
        raise
    finally:
        conn.close()


def test_connection():
    """Tests if the database connection can be established successfully, triggering auto-heal if down."""
    try:
        conn = get_connection()
        conn.close()
        return True, "Connection successful."
    except Exception as e:
        return False, str(e)


def execute_query(query, params=None):
    """Executes a single query and returns results if applicable."""
    with get_cursor(commit=True) as cur:
        cur.execute(query, params or ())
        try:
            return cur.fetchall()
        except psycopg2.ProgrammingError:
            return None


def execute_many(query, params_list):
    """Executes a batch query for performance."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(query, params_list)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Batch execution failed, rolled back: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
