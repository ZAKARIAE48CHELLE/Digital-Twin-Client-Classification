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

def main():
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
