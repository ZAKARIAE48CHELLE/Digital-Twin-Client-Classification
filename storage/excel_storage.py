import os
import shutil
import pandas as pd
from pathlib import Path
import streamlit as st

# We import helpers from app.py dynamically if needed or define locally.
# Since we shouldn't change app.py's location, we can define the paths relative to the project root.
EXCEL_PATH = "osmos_digital_twin_data.xlsx"
BACKUP_PATH = "osmos_digital_twin_data_backup.xlsx"

def load_initial_excel_data():
    paths_to_try = [
        Path("base models/RFM/osmos_simulation_data.xlsx"),
        Path("base models/osmos_simulation_data.xlsx"),
        Path("osmos_simulation_data.xlsx")
    ]
    excel_path = None
    for p in paths_to_try:
        if p.exists():
            excel_path = p
            break
            
    if excel_path is None:
        return None

    snapshots = pd.read_excel(excel_path, sheet_name="Digital_Twins")
    profiles = pd.read_excel(excel_path, sheet_name="Customers")
    
    df = snapshots.merge(
        profiles,
        on=["entity_id", "entity_type"],
        how="left",
        suffixes=("", "_profile")
    )
    df = df.loc[:, ~df.columns.duplicated()]
    
    if "snapshot_date" in df.columns:
        df["snapshot_date"] = df["snapshot_date"].astype(str)
    if "created_at" in df.columns:
        df["created_at"] = df["created_at"].astype(str)
        
    return df

def load_excel_data():
    excel_path = Path(EXCEL_PATH)
    backup_path = Path(BACKUP_PATH)
    
    df, history = None, None
    loaded_ok = False
    
    # 1. Try reading the main file
    if excel_path.exists():
        try:
            df = pd.read_excel(excel_path, sheet_name="Digital_Twins")
            history = pd.read_excel(excel_path, sheet_name="Event_History")
            loaded_ok = True
        except Exception as e:
            # Let the caller or manager handle warnings
            pass
            
    # 2. Try reading the backup file if the main file failed
    if not loaded_ok and backup_path.exists():
        try:
            df = pd.read_excel(backup_path, sheet_name="Digital_Twins")
            history = pd.read_excel(backup_path, sheet_name="Event_History")
            loaded_ok = True
        except Exception as e:
            pass
            
    # 3. Fallback bootstrap
    if not loaded_ok:
        df = load_initial_excel_data()
        history = pd.DataFrame(columns=[
            "event_id", "entity_id", "event_type", "event_date", "old_class", "new_class",
            "class_changed", "old_entity_type", "new_entity_type", "prospect_to_client_conversion",
            "completed_client_profile", "changed_variables", "before_values", "after_values"
        ])
        
    return df, history

def backup_excel_file():
    if os.path.exists(EXCEL_PATH):
        try:
            shutil.copy2(EXCEL_PATH, BACKUP_PATH)
            return True
        except Exception:
            return False
    return False

def save_excel_data(df, history_df=None):
    backup_excel_file()
    
    if history_df is None:
        # Load existing history to preserve it if not provided
        _, history_df = load_excel_data()
        
    try:
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Digital_Twins", index=False)
            history_df.to_excel(writer, sheet_name="Event_History", index=False)
        return True, None
    except PermissionError:
        err_msg = "❌ Permission Denied: The data file `osmos_digital_twin_data.xlsx` is currently open in Excel. Please close it."
        return False, err_msg
    except Exception as e:
        return False, str(e)

def append_excel_event(event_dict):
    df, history_df = load_excel_data()
    
    # Standardize dictionary formats as JSON strings if they are dicts
    import json
    for col in ["changed_variables", "before_values", "after_values"]:
        val = event_dict.get(col)
        if isinstance(val, (dict, list)):
            event_dict[col] = json.dumps(val)
            
    new_row = pd.DataFrame([event_dict])
    # Align columns
    for col in history_df.columns:
        if col not in new_row.columns:
            new_row[col] = None
    new_row = new_row[history_df.columns]
    
    history_df = pd.concat([history_df, new_row], ignore_index=True)
    save_excel_data(df, history_df)
    return history_df

def load_excel_event_history(entity_id=None):
    _, history_df = load_excel_data()
    if entity_id:
        history_df = history_df[history_df["entity_id"] == entity_id]
    return history_df
