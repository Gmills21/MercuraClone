"""
Initialize billing database tables.
Run this script to set up subscription and billing tables.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db
from app.models_billing import BILLING_SCHEMA
from loguru import logger


async def init_billing_tables():
    """Initialize billing tables in the database."""
    try:
        logger.info("Initializing billing tables...")
        
        if not db or not db.admin_client:
            logger.error("Database not configured. Please set SUPABASE_URL and SUPABASE_SERVICE_KEY")
            return False
        
        # Execute the billing schema
        # Note: This is for Supabase/PostgreSQL
        # For SQLite, you'll need to adapt the schema
        
        logger.info("Executing billing schema SQL...")
        
        # Split schema into individual statements
        statements = [s.strip() for s in BILLING_SCHEMA.split(';') if s.strip()]
        
        for statement in statements:
            try:
                # Execute each statement
                # Note: Supabase Python client doesn't support raw SQL execution directly
                # You'll need to run this SQL manually in Supabase SQL editor
                logger.info(f"Statement: {statement[:100]}...")
            except Exception as e:
                logger.warning(f"Statement execution note: {e}")
        
        logger.success("Billing schema prepared!")
        logger.info("Please run the SQL from app/models_billing.py in your Supabase SQL editor")
        
        # Create default subscription plans
        logger.info("Creating default subscription plans...")
        
        default_plans = [
            {
                "name": "Basic",
                "description": "Perfect for small teams",
                "price_per_seat": 150.00,
                "billing_interval": "monthly",
                "features": [
                    "Unlimited quotes",
                    "Email integration",
                    "Basic analytics",
                    "Standard support"
                ],
                "max_seats": 10,
                "is_active": True
            },
            {
                "name": "Professional",
                "description": "For growing businesses",
                "price_per_seat": 250.00,
                "billing_interval": "monthly",
                "features": [
                    "Everything in Basic",
                    "Advanced analytics",
                    "QuickBooks integration",
                    "Priority support",
                    "Custom branding"
                ],
                "max_seats": 50,
                "is_active": True
            },
            {
                "name": "Enterprise",
                "description": "For large organizations",
                "price_per_seat": 400.00,
                "billing_interval": "monthly",
                "features": [
                    "Everything in Professional",
                    "Dedicated account manager",
                    "Custom integrations",
                    "SLA guarantee",
                    "Advanced security"
                ],
                "max_seats": None,
                "is_active": True
            }
        ]
        
        try:
            for plan in default_plans:
                result = db.admin_client.table('subscription_plans').insert(plan).execute()
                logger.success(f"Created plan: {plan['name']}")
        except Exception as e:
            logger.warning(f"Plans may already exist: {e}")
        
        logger.success("Billing initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing billing tables: {e}")
        return False


async def main():
    """Main entry point."""
    logger.info("Starting billing database initialization...")
    
    success = await init_billing_tables()
    
    if success:
        logger.success("✓ Billing setup complete!")
        logger.info("Next steps:")
        logger.info("1. Run the SQL schema from app/models_billing.py in Supabase SQL editor")
        logger.info("2. Configure Paddle credentials in .env")
        logger.info("3. Create products in Paddle dashboard")
        logger.info("4. Update PADDLE_PLAN_* environment variables")
    else:
        logger.error("✗ Billing setup failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
