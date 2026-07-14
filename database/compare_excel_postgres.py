import sys
import os
import json
import pandas as pd
import numpy as np

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import storage managers
os.environ["OSMOS_STORAGE_BACKEND"] = "postgres"
from storage.postgres_storage import load_postgres_data
from storage.excel_storage import load_excel_data

def compare_data():
    print("============================================================")
    print("OSMOS Excel vs PostgreSQL Parity Diagnostic")
    print("============================================================")
    
    # 1. Load Excel Data
    excel_df, excel_hist = load_excel_data()
    print(f"Loaded Excel Digital Twins: {excel_df.shape[0]} rows, {excel_df.shape[1]} columns.")
    
    # 2. Load PostgreSQL Data
    pg_df, pg_hist = load_postgres_data()
    print(f"Loaded PostgreSQL Digital Twins: {pg_df.shape[0]} rows, {pg_df.shape[1]} columns.")
    
    # Compare columns
    excel_cols = set(excel_df.columns)
    pg_cols = set(pg_df.columns)
    
    missing_in_pg = list(excel_cols - pg_cols)
    extra_in_pg = list(pg_cols - excel_cols)
    
    print(f"Columns missing in PostgreSQL ({len(missing_in_pg)}): {missing_in_pg}")
    print(f"Columns extra in PostgreSQL ({len(extra_in_pg)}): {extra_in_pg}")
    
    # Compare entities
    excel_ids = set(excel_df["entity_id"].dropna().astype(str).tolist())
    pg_ids = set(pg_df["entity_id"].dropna().astype(str).tolist()) if "entity_id" in pg_df.columns else set()
    
    missing_ids = list(excel_ids - pg_ids)
    extra_ids = list(pg_ids - excel_ids)
    
    print(f"Entity IDs missing in PostgreSQL ({len(missing_ids)}): {missing_ids[:20]}")
    print(f"Entity IDs extra in PostgreSQL ({len(extra_ids)}): {extra_ids[:20]}")
    
    # Compare null rates
    important_cols = [
        "entity_id", "entity_type", "original_entity_type", "dynamic_class",
        "rfm_score", "predicted_clv_amount_mad", "predicted_clv_score", "predicted_clv_segment",
        "customer_segment", "customer_persona"
    ]
    
    null_comparison = {}
    for col in important_cols:
        excel_null = float(excel_df[col].isna().mean()) if col in excel_df.columns else 1.0
        pg_null = float(pg_df[col].isna().mean()) if col in pg_df.columns else 1.0
        null_comparison[col] = {
            "excel_null_rate": excel_null,
            "postgres_null_rate": pg_null
        }
        
    # Value differences
    sample_diffs = []
    if not pg_df.empty and "entity_id" in pg_df.columns:
        # Align on index entity_id
        excel_aligned = excel_df.set_index("entity_id")
        pg_aligned = pg_df.set_index("entity_id")
        
        common_ids = list(excel_ids & pg_ids)
        if common_ids:
            for col in important_cols:
                if col == "entity_id":
                    continue
                if col in excel_aligned.columns and col in pg_aligned.columns:
                    e_vals = excel_aligned.loc[common_ids, col]
                    p_vals = pg_aligned.loc[common_ids, col]
                    
                    # Compute mismatched indices
                    mismatches = []
                    for cid in common_ids:
                        ev = e_vals.loc[cid]
                        pv = p_vals.loc[cid]
                        if pd.isna(ev) and pd.isna(pv):
                            continue
                        elif pd.isna(ev) or pd.isna(pv):
                            mismatches.append((cid, ev, pv))
                        else:
                            try:
                                if abs(float(ev) - float(pv)) > 0.05:
                                    mismatches.append((cid, float(ev), float(pv)))
                            except Exception:
                                if str(ev) != str(pv):
                                    mismatches.append((cid, str(ev), str(pv)))
                                    
                    if mismatches:
                        sample_diffs.append({
                            "column": col,
                            "mismatch_count": len(mismatches),
                            "samples": [{"entity_id": m[0], "excel": m[1], "postgres": m[2]} for m in mismatches[:5]]
                        })
                        
    # Final verdict
    verdict = "PASS"
    if missing_in_pg or missing_ids or sample_diffs:
        verdict = "FAIL"
        
    report = {
        "excel_row_count": int(excel_df.shape[0]),
        "postgres_row_count": int(pg_df.shape[0]),
        "missing_columns_in_postgres": missing_in_pg,
        "extra_columns_in_postgres": extra_in_pg,
        "missing_entity_ids_in_postgres": missing_ids,
        "extra_entity_ids_in_postgres": extra_ids,
        "null_rate_comparison": null_comparison,
        "sample_value_differences": sample_diffs,
        "verdict": verdict
    }
    
    report_path = os.path.join(os.path.dirname(__file__), "parity_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    print(f"\nDiagnostic finished. Verdict: {verdict}. Report written to {report_path}")
    print("============================================================")

if __name__ == "__main__":
    compare_data()
