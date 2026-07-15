import pandas as pd
from sqlalchemy import text
from database.db import get_connection_string
from admin.database_metrics import is_postgres_available

def get_engine():
    from sqlalchemy import create_engine
    return create_engine(get_connection_string())

def get_class_distribution(window_days=30):
    """Retrieve classification prediction count distribution within specified days window."""
    if not is_postgres_available():
        return pd.DataFrame()
        
    engine = get_engine()
    query = """
        SELECT 
            dynamic_class, 
            COUNT(*) as count
        FROM classification_predictions
        WHERE predicted_at >= NOW() - CAST(:days_interval AS INTERVAL)
        GROUP BY dynamic_class;
    """
    try:
        days_str = f"{window_days} days"
        return pd.read_sql(text(query), engine, params={"days_interval": days_str})
    except Exception:
        return pd.DataFrame()

def compare_class_distribution(current_days=30, baseline_days=90):
    """Compare current class distributions with baseline class distributions."""
    if not is_postgres_available():
        return pd.DataFrame()
        
    engine = get_engine()
    
    # Baseline query: from (current_days + baseline_days) days ago to current_days days ago
    query_baseline = """
        SELECT 
            dynamic_class, 
            COUNT(*) as baseline_count
        FROM classification_predictions
        WHERE predicted_at >= NOW() - CAST(:total_interval AS INTERVAL)
          AND predicted_at < NOW() - CAST(:current_interval AS INTERVAL)
        GROUP BY dynamic_class;
    """
    
    # Current query: from current_days days ago to now
    query_current = """
        SELECT 
            dynamic_class, 
            COUNT(*) as current_count
        FROM classification_predictions
        WHERE predicted_at >= NOW() - CAST(:current_interval AS INTERVAL)
        GROUP BY dynamic_class;
    """
    
    try:
        current_str = f"{current_days} days"
        total_str = f"{current_days + baseline_days} days"
        
        baseline_df = pd.read_sql(text(query_baseline), engine, params={
            "total_interval": total_str,
            "current_interval": current_str
        })
        current_df = pd.read_sql(text(query_current), engine, params={
            "current_interval": current_str
        })
        
        # Merge datasets
        df = pd.merge(baseline_df, current_df, on="dynamic_class", how="outer").fillna(0)
        
        total_baseline = df["baseline_count"].sum()
        total_current = df["current_count"].sum()
        
        df["baseline_percent"] = df["baseline_count"] / total_baseline if total_baseline > 0 else 0.0
        df["current_percent"] = df["current_count"] / total_current if total_current > 0 else 0.0
        df["change_percent"] = df["current_percent"] - df["baseline_percent"]
        
        return df
    except Exception:
        return pd.DataFrame()

def detect_prediction_drift(threshold=0.15):
    """Detect prediction distribution drift using threshold limits."""
    df = compare_class_distribution(current_days=30, baseline_days=90)
    if df.empty:
        return pd.DataFrame()
        
    drift_flags = []
    drift_levels = []
    
    for _, row in df.iterrows():
        change = abs(row["change_percent"])
        flag = change >= threshold
        
        if change >= 0.25:
            level = "High"
        elif change >= 0.15:
            level = "Medium"
        elif change >= 0.10:
            level = "Low"
        else:
            level = "None"
            
        drift_flags.append(flag)
        drift_levels.append(level)
        
    df["drift_flag"] = drift_flags
    df["drift_level"] = drift_levels
    
    return df
