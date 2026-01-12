"""
Database initialization script for Supabase.
"""

from supabase import create_client
from app.models import SUPABASE_SCHEMA
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

def init_database():
    """Initialize Supabase database with schema."""
    try:
        # Get credentials from environment
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_service_key:
            print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")
            sys.exit(1)
        
        print("Connecting to Supabase...")
        client = create_client(supabase_url, supabase_service_key)
        
        print("Executing schema SQL...")
        
        # Split schema into individual statements
        statements = SUPABASE_SCHEMA.split(';')
        
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if statement:
                try:
                    print(f"Executing statement {i+1}/{len(statements)}...")
                    # Note: Supabase Python client doesn't directly support raw SQL execution
                    # You'll need to run this SQL manually in the Supabase SQL Editor
                    # or use a PostgreSQL client
                    print(f"Statement: {statement[:100]}...")
                except Exception as e:
                    print(f"Warning: Error executing statement {i+1}: {e}")
        
        print("\n" + "="*80)
        print("IMPORTANT: Database Schema Setup")
        print("="*80)
        print("\nThe Supabase Python client doesn't support direct SQL execution.")
        print("Please follow these steps to initialize your database:\n")
        print("1. Go to your Supabase Dashboard")
        print("2. Navigate to the SQL Editor")
        print("3. Copy the SQL schema from app/models.py (SUPABASE_SCHEMA)")
        print("4. Paste and execute it in the SQL Editor\n")
        print("Alternatively, you can use a PostgreSQL client with your database connection string.")
        print("="*80)
        
        # Save schema to file for easy access
        schema_file = "database_schema.sql"
        with open(schema_file, 'w') as f:
            f.write(SUPABASE_SCHEMA)
        
        print(f"\nSchema has been saved to: {schema_file}")
        print("You can execute this file in the Supabase SQL Editor.\n")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    print("Mercura Database Initialization")
    print("="*80)
    
    success = init_database()
    
    if success:
        print("\nDatabase initialization completed!")
        print("Please execute the schema SQL in Supabase Dashboard.")
    else:
        print("\nDatabase initialization failed!")
        sys.exit(1)
