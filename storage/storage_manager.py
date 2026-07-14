import os
import logging
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from database.db import test_connection
from storage.excel_storage import (
    load_excel_data,
    save_excel_data,
    append_excel_event,
    load_excel_event_history
)
from storage.postgres_storage import (
    load_postgres_data,
    save_postgres_data,
    save_postgres_event,
    save_postgres_rfm_score,
    save_postgres_classification_prediction,
    save_postgres_clv_prediction,
    save_postgres_customer_segment,
    load_postgres_event_history
)

logger = logging.getLogger("OSMOS_STORAGE_MANAGER")

# Global state to track fallback status
_fallback_active = False
_fallback_reason = None

def get_storage_backend():
    """Retrieve the storage backend setting, respecting fallback states."""
    global _fallback_active
    requested = os.getenv("OSMOS_STORAGE_BACKEND", "excel").lower()
    if requested == "postgres" and not _fallback_active:
        # Check connection once
        connected, reason = test_connection()
        if not connected:
            logger.warning(f"OSMOS_STORAGE_BACKEND is set to 'postgres' but connection failed. Falling back to Excel. Error: {reason}")
            _fallback_active = True
            global _fallback_reason
            _fallback_reason = reason
            return "excel"
        return "postgres"
    elif requested == "postgres" and _fallback_active:
        return "excel"
    return "excel"

def get_fallback_status():
    """Returns whether fallback to Excel is currently active due to DB failure."""
    return _fallback_active, _fallback_reason

def is_postgres_enabled():
    """Checks if postgres mode is currently active and healthy."""
    return get_storage_backend() == "postgres"

def load_data():
    """Exposes a unified method to load entity data and event history."""
    if is_postgres_enabled():
        try:
            return load_postgres_data()
        except Exception as e:
            logger.error(f"Error loading data from PostgreSQL, falling back to Excel: {e}")
            global _fallback_active, _fallback_reason
            _fallback_active = True
            _fallback_reason = str(e)
            return load_excel_data()
    return load_excel_data()

def save_data(df, history_df=None):
    """Exposes a unified method to save/upsert full entity dataset snapshots."""
    if is_postgres_enabled():
        try:
            return save_postgres_data(df, history_df)
        except Exception as e:
            logger.error(f"Error saving data to PostgreSQL, falling back to Excel: {e}")
            global _fallback_active, _fallback_reason
            _fallback_active = True
            _fallback_reason = str(e)
            return save_excel_data(df, history_df)
    return save_excel_data(df, history_df)

def save_event(event_dict):
    """Saves a single event historically."""
    # Write to Excel first if Excel is requested or as fallback
    history_df = append_excel_event(event_dict)
    
    if is_postgres_enabled():
        try:
            save_postgres_event(event_dict)
        except Exception as e:
            logger.error(f"Failed to log event to PostgreSQL: {e}")
            
    return history_df

def save_rfm_score(entity_id, rfm_dict, event_id=None):
    """Saves an RFM score historically in DB, Excel handles it via snapshot save_data."""
    if is_postgres_enabled():
        try:
            save_postgres_rfm_score(entity_id, rfm_dict, event_id)
        except Exception as e:
            logger.error(f"Failed to log RFM score to PostgreSQL: {e}")

def save_classification_prediction(entity_id, prediction_dict, event_id=None):
    """Saves a classification prediction historically in DB."""
    if is_postgres_enabled():
        try:
            save_postgres_classification_prediction(entity_id, prediction_dict, event_id)
        except Exception as e:
            logger.error(f"Failed to log classification prediction to PostgreSQL: {e}")

def save_clv_prediction(entity_id, clv_dict, event_id=None):
    """Saves a CLV prediction historically in DB."""
    if is_postgres_enabled():
        try:
            save_postgres_clv_prediction(entity_id, clv_dict, event_id)
        except Exception as e:
            logger.error(f"Failed to log CLV prediction to PostgreSQL: {e}")

def save_customer_segment(entity_id, segment_dict, event_id=None):
    """Saves customer segment assignment historically in DB."""
    if is_postgres_enabled():
        try:
            save_postgres_customer_segment(entity_id, segment_dict, event_id)
        except Exception as e:
            logger.error(f"Failed to log customer segment to PostgreSQL: {e}")

def load_event_history(entity_id=None):
    """Loads event history logs."""
    if is_postgres_enabled():
        try:
            return load_postgres_event_history(entity_id)
        except Exception as e:
            logger.error(f"Failed to load event history from PostgreSQL: {e}")
            return load_excel_event_history(entity_id)
    return load_excel_event_history(entity_id)
