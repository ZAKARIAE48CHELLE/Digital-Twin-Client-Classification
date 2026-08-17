import os
import sys
import argparse
import json
import logging
import pandas as pd
import numpy as np
import joblib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db import get_connection, transaction, test_connection
from database.repositories import (
    upsert_entity,
    upsert_customer_profile,
    upsert_digital_twin_snapshot,
    insert_rfm_es_score,
    insert_classification_prediction,
    insert_clv_prediction,
    insert_customer_segment,
    insert_event_history,
    register_model,
    insert_audit_log
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OSMOS_MIGRATION")

def clean_float(val):
    if pd.isna(val) or val is None:
        return None
    try:
        return float(val)
    except Exception:
        return None

def clean_int(val):
    if pd.isna(val) or val is None:
        return None
    try:
        return int(val)
    except Exception:
        return None

def clean_str(val):
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    return val_str if val_str else None

def clean_bool(val):
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, bool):
        return val
    val_str = str(val).strip().lower()
    if val_str in ('true', '1', '1.0', 'yes'):
        return True
    if val_str in ('false', '0', '0.0', 'no'):
        return False
    return None

def parse_json_field(val):
    if pd.isna(val) or val is None:
        return {}
    if isinstance(val, (dict, list)):
        return val
    val_str = str(val).strip()
    if not val_str:
        return {}
    try:
        return json.loads(val_str)
    except Exception:
        # Fallback if it's a simple string list or non-JSON string
        return {"raw_value": val_str}

def truncate_tables():
    logger.info("Truncating existing OSMOS tables in PostgreSQL...")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            TRUNCATE TABLE 
                audit_logs,
                classification_predictions,
                clv_predictions,
                customer_segments,
                rfm_es_scores,
                event_history,
                digital_twin_snapshots,
                customer_profiles,
                entities,
                model_registry
            RESTART IDENTITY CASCADE;
        """)
        conn.commit()
        logger.info("All OSMOS tables truncated successfully.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to truncate tables: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def load_pkl_metadata(path):
    if not os.path.exists(path):
        return None, f"File {path} does not exist."
    try:
        # Try loading metadata
        artifact = joblib.load(path)
        return artifact, None
    except Exception as e:
        return None, str(e)
def migrate_models(dry_run):
    registered_count = 0
    warnings = []
    registered_models_dict = {}
    
    paths_to_check = [
        ("classification", ["base models/RFM/osmos_best_model_artifact.pkl", "osmos_best_model_artifact.pkl"]),
        ("clv", ["base models/CLV/osmos_best_clv_model_artifact.pkl", "osmos_best_clv_model_artifact.pkl"])
    ]
    
    for m_type, paths in paths_to_check:
        loaded = False
        for path in paths:
            if os.path.exists(path):
                logger.info(f"Checking model artifact for type '{m_type}' at: {path}")
                artifact, err = load_pkl_metadata(path)
                if err:
                    msg = f"Failed to load metadata for model artifact at {path}: {err}"
                    logger.warning(msg)
                    warnings.append(msg)
                    if not dry_run:
                        insert_audit_log("MODEL_LOAD_WARNING", {"path": path, "error": err, "model_type": m_type})
                    continue
                
                # Success loading! Extract metadata
                model_name = "Unknown Model"
                entity_format = None
                rfm_ver = None
                metric = None
                feat_count = None
                metrics_dict = {}
                export_date = None
                
                if m_type == "classification":
                    model_name = artifact.get("best_model_name", "Dynamic Classification Model")
                    entity_format = artifact.get("entity_type_format")
                    rfm_ver = artifact.get("rfm_version")
                    metric = artifact.get("selection_metric")
                    export_date = artifact.get("export_date")
                    feature_cols = artifact.get("feature_columns", [])
                    feat_count = len(feature_cols)
                    if "results" in artifact and isinstance(artifact["results"], pd.DataFrame):
                        metrics_dict = {"results": artifact["results"].to_dict(orient="records")}
                elif m_type == "clv":
                    model_name = artifact.get("best_amount_model_name", "CLV Amount Model")
                    export_date = artifact.get("export_date")
                    feature_cols = artifact.get("amount_feature_columns", [])
                    feat_count = len(feature_cols)
                    if "results" in artifact and isinstance(artifact["results"], pd.DataFrame):
                        metrics_dict = {"amount_results": artifact["results"].to_dict(orient="records")}
                    if "segment_results" in artifact and isinstance(artifact["segment_results"], pd.DataFrame):
                        metrics_dict["segment_results"] = artifact["segment_results"].to_dict(orient="records")
                        
                model_dict = {
                    "model_type": m_type,
                    "model_name": model_name,
                    "artifact_path": path,
                    "entity_type_format": entity_format,
                    "rfm_version": rfm_ver,
                    "selection_metric": metric,
                    "feature_count": feat_count,
                    "metrics": metrics_dict,
                    "export_date": export_date
                }
                
                registered_models_dict[m_type] = model_name
                
                if not dry_run:
                    register_model(model_dict)
                    logger.info(f"Registered model {model_name} in PostgreSQL.")
                else:
                    logger.info(f"[DRY-RUN] Would register model: {model_name} (export date: {export_date})")
                    
                registered_count += 1
                loaded = True
                break # Only register the first matching model path
                
        if not loaded:
            msg = f"No valid model artifact found for type '{m_type}'"
            logger.warning(msg)
            warnings.append(msg)
            
    return registered_count, warnings, registered_models_dict


def main():
    parser = argparse.ArgumentParser(description="OSMOS Excel to PostgreSQL Migration Script")
    parser.add_argument("--excel-path", default="osmos_digital_twin_data.xlsx", help="Path to Excel data file")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry-run analysis without inserting records")
    parser.add_argument("--truncate", action="store_true", help="Clear target PostgreSQL database tables before migration")
    
    args = parser.parse_args()
    
    print("============================================================")
    print("OSMOS Migration: Excel to PostgreSQL")
    print("============================================================")
    
    if not os.path.exists(args.excel_path):
        logger.error(f"Excel data file not found at: {args.excel_path}")
        sys.exit(1)
        
    if not args.dry_run:
        success, message = test_connection()
        if not success:
            logger.error(f"Database connection check failed: {message}")
            sys.exit(1)
        logger.info("Successfully connected to database.")
    else:
        logger.info("Dry-run mode active. Skipping database connection test.")


    
    if args.truncate and not args.dry_run:
        # Perform truncation
        truncate_tables()
        
    logger.info(f"Reading Excel sheets from {args.excel_path}...")
    try:
        xl = pd.ExcelFile(args.excel_path)
        sheet_names = xl.sheet_names
        dt_sheet = "Digital_Twins" if "Digital_Twins" in sheet_names else sheet_names[0]
        dt_df = pd.read_excel(args.excel_path, sheet_name=dt_sheet)
        if "Event_History" in sheet_names:
            hist_df = pd.read_excel(args.excel_path, sheet_name="Event_History")
        else:
            hist_df = pd.DataFrame()
    except Exception as e:
        logger.error(f"Failed to read Excel file sheets: {e}")
        sys.exit(1)
        
    logger.info(f"Found {len(dt_df)} records in {dt_sheet} sheet.")
    logger.info(f"Found {len(hist_df)} records in Event_History sheet.")
    
    # --------------------------------------------------------
    # Dry-Run Reporting / Counters
    # --------------------------------------------------------
    counts = {
        "entities": 0,
        "profiles": 0,
        "snapshots": 0,
        "rfm_scores": 0,
        "classifications": 0,
        "clvs": 0,
        "segments": 0,
        "events": 0,
        "models": 0
    }
    
    # Let's run model registry migration
    registered_models, model_warnings, registered_models_dict = migrate_models(args.dry_run)
    counts["models"] = registered_models
    classification_model_name = registered_models_dict.get("classification", "Dynamic Classification Model")

    
    # --------------------------------------------------------
    # A. Migrate Digital Twins
    # --------------------------------------------------------
    logger.info("Migrating Digital Twin profiles...")
    migrated_entity_ids = set()
    skipped_rows_count = 0
    for idx, row in dt_df.iterrows():
        entity_id = clean_str(row.get("entity_id"))
        if not entity_id:
            skipped_rows_count += 1
            continue
        migrated_entity_ids.add(entity_id)
            
        entity_type = clean_str(row.get("entity_type"))
        
        # 1. Map to entities table
        entity_data = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "original_entity_type": clean_str(row.get("original_entity_type")),
            "created_at": clean_str(row.get("created_at")),
            "converted_at": clean_str(row.get("converted_at")),
            "conversion_event_id": clean_str(row.get("conversion_event_id")),
            "completed_client_profile": clean_bool(row.get("completed_client_profile")),
            "region": clean_str(row.get("region")),
            "source_channel": clean_str(row.get("source_channel")),
            "segment": clean_str(row.get("segment")),
            "persona": clean_str(row.get("persona")),
            "age_group": clean_str(row.get("age_group")),
            "preferred_device": clean_str(row.get("preferred_device")),
            "preferred_category": clean_str(row.get("preferred_category")),
            "marketing_consent": clean_bool(row.get("marketing_consent")),
            "price_sensitivity": clean_float(row.get("price_sensitivity")),
            "income_power_score": clean_float(row.get("income_power_score")),
            "initial_interest_score": clean_float(row.get("initial_interest_score")),
            "basic_profile_score": clean_float(row.get("basic_profile_score", 0.5))
        }
        
        # 2. Map to customer_profiles table
        profile_data = {
            "entity_id": entity_id,
            "age": clean_int(row.get("age")),
            "sex": clean_str(row.get("sex")),
            "email": clean_str(row.get("email")),
            "customer_type": clean_str(row.get("customer_type")),
            "household_size": clean_int(row.get("household_size")),
            "phone_number": clean_str(row.get("phone_number")),
            "company_name": clean_str(row.get("company_name")),
            "job_title": clean_str(row.get("job_title")),
            "city": clean_str(row.get("city")),
            "address": clean_str(row.get("address"))
        }
        
        # Check if demographic columns have actual data
        has_profile = any(profile_data[k] is not None for k in profile_data if k != "entity_id")
        
        # 3. Map to digital_twin_snapshots table
        snapshot_data = {
            "entity_id": entity_id,
            "snapshot_date": clean_str(row.get("snapshot_date")),
            "recency_days": clean_float(row.get("recency_days")),
            "visits_30d": clean_float(row.get("visits_30d")),
            "product_views_30d": clean_float(row.get("product_views_30d")),
            "cart_additions_30d": clean_float(row.get("cart_additions_30d")),
            "purchases_90d": clean_float(row.get("purchases_90d")),
            "total_spent_90d_mad": clean_float(row.get("total_spent_90d_mad")),
            "avg_order_value_mad": clean_float(row.get("avg_order_value_mad")),
            "email_open_rate": clean_float(row.get("email_open_rate")),
            "email_click_rate": clean_float(row.get("email_click_rate")),
            "complaint_count_90d": clean_float(row.get("complaint_count_90d")),
            "review_score_avg": clean_float(row.get("review_score_avg")),
            "social_mentions_30d": clean_float(row.get("social_mentions_30d")),
            "social_sentiment_avg": clean_float(row.get("social_sentiment_avg")),
            "conversion_probability": clean_float(row.get("conversion_probability")),
            "churn_risk_score": clean_float(row.get("churn_risk_score")),
            "rfm_score": clean_float(row.get("rfm_score")),
            "behavioral_engagement_score": clean_float(row.get("behavioral_engagement_score")),
            "predictive_value_score": clean_float(row.get("predictive_value_score")),
            "decision_priority_score": clean_float(row.get("decision_priority_score"))
        }
        
        # 4. Map to rfm_es_scores
        rfm_data = {
            "entity_id": entity_id,
            "event_id": None,
            "R_raw": clean_float(row.get("R_raw")),
            "F_raw": clean_float(row.get("F_raw")),
            "M_raw": clean_float(row.get("M_raw")),
            "E_raw": clean_float(row.get("E_raw")),
            "S_raw": clean_float(row.get("S_raw")),
            "rfm_recency_score": clean_int(row.get("rfm_recency_score")),
            "rfm_frequency_score": clean_int(row.get("rfm_frequency_score")),
            "rfm_monetary_score": clean_int(row.get("rfm_monetary_score")),
            "rfm_engagement_score": clean_int(row.get("rfm_engagement_score")),
            "rfm_sentiment_score": clean_int(row.get("rfm_sentiment_score")),
            "rfm_score_raw_1_to_5": clean_float(row.get("rfm_score_raw_1_to_5")),
            "rfm_score": clean_float(row.get("rfm_score")),
            "ahp_weight_R": clean_float(row.get("ahp_weight_R")),
            "ahp_weight_F": clean_float(row.get("ahp_weight_F")),
            "ahp_weight_M": clean_float(row.get("ahp_weight_M")),
            "ahp_weight_E": clean_float(row.get("ahp_weight_E")),
            "ahp_weight_S": clean_float(row.get("ahp_weight_S")),
            "ahp_group_CR": clean_float(row.get("ahp_group_CR")),
            "ahp_group_CI": clean_float(row.get("ahp_group_CI")),
            "ahp_expert_count": clean_int(row.get("ahp_expert_count"))
        }
        has_rfm = rfm_data["rfm_score"] is not None
        
        # 5. Map to classification_predictions
        class_data = {
            "entity_id": entity_id,
            "event_id": None,
            "dynamic_class": clean_str(row.get("dynamic_class")) or "Unknown",
            "confidence": 1.0, # default to 1.0 as it is not in the excel
            "top_3_probs": None,
            "model_name": classification_model_name,
            "model_version": "1.0",
            "model_registry_id": None
        }
        has_class = class_data["dynamic_class"] is not None
        
        # 6. Map to clv_predictions
        clv_data = {
            "entity_id": entity_id,
            "event_id": None,
            "predicted_clv_amount_mad": clean_float(row.get("predicted_clv_amount_mad")),
            "predicted_clv_score": clean_float(row.get("predicted_clv_score")),
            "predicted_clv_segment": clean_str(row.get("predicted_clv_segment")),
            "clv_model_name": clean_str(row.get("clv_model_name")),
            "clv_segment_model_name": clean_str(row.get("clv_segment_model_name")),
            "clv_method_used": clean_str(row.get("clv_method_used")),
            "ml_predicted_clv_amount_mad": clean_float(row.get("ml_predicted_clv_amount_mad")),
            "math_clv_amount_mad": clean_float(row.get("math_clv_amount_mad")),
            "clv_segment_prediction_source": clean_str(row.get("clv_segment_prediction_source")),
            "clv_segment_confidence": clean_float(row.get("clv_segment_confidence")),
            "clv_segment_top_3": parse_json_field(row.get("clv_segment_top_3")),
            "model_registry_id": None
        }
        has_clv = (clv_data["predicted_clv_amount_mad"] is not None) or (clv_data["predicted_clv_segment"] is not None)
        
        # 7. Map to customer_segments
        segment_data = {
            "entity_id": entity_id,
            "event_id": None,
            "customer_segment": clean_str(row.get("customer_segment")),
            "customer_persona": clean_str(row.get("customer_persona")),
            "persona_description": clean_str(row.get("persona_description")),
            "persona_recommended_action": clean_str(row.get("persona_recommended_action")),
            "segmentation_method": clean_str(row.get("segmentation_method")) or "Rule-Based RFM-ES + CLV Segmentation",
            "ml_cluster_id": clean_int(row.get("ml_cluster_id")),
            "ml_cluster_label": clean_str(row.get("ml_cluster_label")),
            "cluster_persona": clean_str(row.get("cluster_persona"))
        }
        has_segment = (segment_data["customer_segment"] is not None) or (segment_data["customer_persona"] is not None)
        
        if not args.dry_run:
            upsert_entity(entity_data)
            counts["entities"] += 1
            
            if has_profile:
                upsert_customer_profile(profile_data)
                counts["profiles"] += 1
                
            upsert_digital_twin_snapshot(snapshot_data)
            counts["snapshots"] += 1
            
            if has_rfm:
                insert_rfm_es_score(rfm_data)
                counts["rfm_scores"] += 1
                
            if has_class:
                insert_classification_prediction(class_data)
                counts["classifications"] += 1
                
            if has_clv:
                insert_clv_prediction(clv_data)
                counts["clvs"] += 1
                
            if has_segment:
                insert_customer_segment(segment_data)
                counts["segments"] += 1
        else:
            counts["entities"] += 1
            if has_profile: counts["profiles"] += 1
            counts["snapshots"] += 1
            if has_rfm: counts["rfm_scores"] += 1
            if has_class: counts["classifications"] += 1
            if has_clv: counts["clvs"] += 1
            if has_segment: counts["segments"] += 1

    # B. Migrate Event History
    # --------------------------------------------------------
    logger.info("Migrating Event History records...")
    skipped_events_count = 0
    for idx, row in hist_df.iterrows():
        event_id = clean_str(row.get("event_id"))
        entity_id = clean_str(row.get("entity_id"))
        if not event_id or not entity_id:
            skipped_events_count += 1
            continue
            
        event_data = {
            "event_id": event_id,
            "entity_id": entity_id,
            "event_type": clean_str(row.get("event_type")),
            "event_date": clean_str(row.get("event_date")),
            "old_class": clean_str(row.get("old_class")),
            "new_class": clean_str(row.get("new_class")),
            "class_changed": clean_bool(row.get("class_changed")),
            "old_entity_type": clean_str(row.get("old_entity_type")),
            "new_entity_type": clean_str(row.get("new_entity_type")),
            "prospect_to_client_conversion": clean_bool(row.get("prospect_to_client_conversion")),
            "completed_client_profile": clean_bool(row.get("completed_client_profile")),
            "changed_variables": parse_json_field(row.get("changed_variables")),
            "before_values": parse_json_field(row.get("before_values")),
            "after_values": parse_json_field(row.get("after_values")),
            "old_clv_amount_mad": clean_float(row.get("old_clv_amount_mad")),
            "new_clv_amount_mad": clean_float(row.get("new_clv_amount_mad")),
            "old_clv_score": clean_float(row.get("old_clv_score")),
            "new_clv_score": clean_float(row.get("new_clv_score")),
            "old_clv_segment": clean_str(row.get("old_clv_segment")),
            "new_clv_segment": clean_str(row.get("new_clv_segment")),
            "clv_changed": clean_bool(row.get("clv_changed"))
        }
        
        if not args.dry_run:
            # We must make sure the entity referenced actually exists (safety fallback)
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM entities WHERE entity_id = %s;", (event_data["entity_id"],))
            exists = cursor.fetchone()
            cursor.close()
            conn.close()
        else:
            exists = event_data["entity_id"] in migrated_entity_ids
            
        if exists:
            if not args.dry_run:
                insert_event_history(event_data)
            counts["events"] += 1
        else:
            skipped_events_count += 1
            if not args.dry_run:
                logger.warning(f"Skipping event {event_id} due to missing parent entity: {event_data['entity_id']}")

    # --------------------------------------------------------
    # C. Print Summary
    # --------------------------------------------------------
    print("\n============================================================")
    print("MIGRATION SUMMARY")
    print("============================================================")
    if args.dry_run:
        print("[DRY-RUN] Analysis complete. No changes were made to PostgreSQL.")
    else:
        print("[SUCCESS] Data successfully written to PostgreSQL.")
        
    print(f"Entities migrated:                     {counts['entities']}")
    print(f"Customer profiles migrated:            {counts['profiles']}")
    print(f"Digital Twin snapshots migrated:       {counts['snapshots']}")
    print(f"RFM scores inserted:                  {counts['rfm_scores']}")
    print(f"Classification predictions inserted:    {counts['classifications']}")
    print(f"CLV predictions inserted:              {counts['clvs']}")
    print(f"Customer segments inserted:            {counts['segments']}")
    print(f"Event history entries migrated:        {counts['events']}")
    print(f"Models registered:                     {counts['models']}")
    
    if model_warnings:
        print("\nWarnings:")
        for warning in model_warnings:
            print(f"  - {warning}")
            
    print("============================================================")

    # Write JSON report
    report_data = {
        "dry_run": args.dry_run,
        "counts": counts,
        "skipped_rows": skipped_rows_count,
        "skipped_events": skipped_events_count,
        "warnings": model_warnings
    }
    
    report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "migration_report.json"))
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"Migration report successfully saved to {report_path}")
    except Exception as e:
        logger.error(f"Failed to write migration report to {report_path}: {e}")

if __name__ == "__main__":
    main()
