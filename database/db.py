import os
import logging
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

def get_connection_string():
    """Build connection string from environment variables or DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url
        
    host = os.environ.get("DB_HOST")
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ.get("DB_NAME")
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    
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

def get_connection():
    """Get a raw connection to the PostgreSQL database."""
    conn_str = get_connection_string()
    try:
        conn = psycopg2.connect(conn_str)
        return conn
    except Exception as e:
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
    """Tests if the database connection can be established successfully."""
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
            # Query didn't return rows (e.g., INSERT, UPDATE)
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
