
import sys
import os
import sqlite3
import uuid
from datetime import datetime

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database_sqlite import get_db, init_db, create_customer, list_customers, get_customer_by_id

def verify_schema():
    print("Verifying schema...")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(customers)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'organization_id' in columns:
            print("✅ organizations_id column exists in customers table.")
        else:
            print("❌ organizations_id column MISSING in customers table.")
            return False
    return True

def verify_isolation():
    print("\nVerifying data isolation...")
    org_a = str(uuid.uuid4())
    org_b = str(uuid.uuid4())
    
    # Create customers for Org A
    cust_a = {
        "id": str(uuid.uuid4()),
        "organization_id": org_a,
        "name": "Customer A",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    create_customer(cust_a)
    
    # Create customers for Org B
    cust_b = {
        "id": str(uuid.uuid4()),
        "organization_id": org_b,
        "name": "Customer B",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    create_customer(cust_b)
    
    # List Org A
    list_a = list_customers(organization_id=org_a)
    ids_a = [c['id'] for c in list_a]
    if cust_a['id'] in ids_a and cust_b['id'] not in ids_a:
        print("✅ Org A sees only its customers.")
    else:
        print(f"❌ Org A isolation failed. Got: {ids_a}")

    # List Org B
    list_b = list_customers(organization_id=org_b)
    ids_b = [c['id'] for c in list_b]
    if cust_b['id'] in ids_b and cust_a['id'] not in ids_b:
        print("✅ Org B sees only its customers.")
    else:
        print(f"❌ Org B isolation failed. Got: {ids_b}")

if __name__ == "__main__":
    if verify_schema():
        verify_isolation()
