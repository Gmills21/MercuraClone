import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db
from app.models import User, Customer, Quote, QuoteItem, Catalog, QuoteStatus
from app.config import settings

async def seed():
    print("Seeding data...")
    if not db:
        print("Database not initialized. Check credentials.")
        return

    # 1. Create User
    user = User(
        email="demo@mercura.ai",
        company_name="Mercura Demo",
        api_key="demo-key-123",
        email_quota_per_day=1000
    )
    # Check if user exists first to avoid duplicate email error
    existing_user = await db.get_user_by_email(user.email)
    if existing_user:
        user_id = existing_user['id']
        print(f"User exists: {user_id}")
    else:
        user_id = await db.create_user(user)
        print(f"Created user: {user_id}")

    # 2. Create Customers
    customer_ids = []
    customers = [
        Customer(user_id=user_id, name="Acme Corp", email="contact@acme.com", company="Acme Corp", address="123 Acme Way"),
        Customer(user_id=user_id, name="Globex Inc", email="info@globex.com", company="Globex Inc", address="456 Globex St"),
        Customer(user_id=user_id, name="Soylent Corp", email="people@soylent.com", company="Soylent Corp", address="789 People Rd"),
    ]
    
    # Simple check if customers exist (by listing)
    existing_customers = await db.get_customers(user_id)
    if not existing_customers:
        for c in customers:
            cid = await db.create_customer(c)
            customer_ids.append(cid)
        print(f"Created {len(customers)} customers")
    else:
        customer_ids = [c['id'] for c in existing_customers]
        print(f"Using {len(customer_ids)} existing customers")

    # 3. Create Products (Catalogs)
    products = [
        {"sku": "HAM-001", "name": "Industrial Hammer", "price": 25.50},
        {"sku": "DRL-900", "name": "Power Drill 9000", "price": 199.99},
        {"sku": "SCR-100", "name": "Screw Set (100pc)", "price": 12.99},
        {"sku": "SAW-500", "name": "Circular Saw", "price": 149.50},
        {"sku": "GLV-MED", "name": "Safety Gloves (M)", "price": 5.00},
        {"sku": "HLM-YEL", "name": "Hard Hat (Yellow)", "price": 29.99},
    ]
    
    product_ids = []
    for p in products:
        # Check if exists
        existing = await db.get_catalog_item(user_id, p['sku'])
        if existing:
            product_ids.append(existing['id'])
        else:
            cat = Catalog(
                user_id=user_id,
                sku=p['sku'],
                item_name=p['name'],
                expected_price=p['price'],
                category="Tools",
                supplier="ToolCo"
            )
            pid = await db.upsert_catalog_item(cat)
            product_ids.append(pid)
    print(f"Seeded {len(products)} products")

    # 4. Create Quotes
    # Only create if none exist to avoid cluttering on multiple runs
    existing_quotes = await db.list_quotes(user_id)
    if not existing_quotes:
        for _ in range(5):
            cid = random.choice(customer_ids)
            q_items = []
            total = 0
            
            # Select 1-3 random products
            selected_prods = random.sample(products, k=random.randint(1, 3))
            
            for sp in selected_prods:
                qty = random.randint(1, 10)
                subtotal = sp['price'] * qty
                total += subtotal
                
                # Find the product ID (we need to map sku back to ID or just search)
                # Ideally we stored the IDs properly. Let's look them up or use the list we made.
                # Simplification: we need the product ID for the QuoteItem.
                # Re-fetch or rely on the fact we upserted.
                prod_data = await db.get_catalog_item(user_id, sp['sku'])
                
                q_items.append(QuoteItem(
                    quote_id="placeholder", # Filled by create_quote
                    product_id=prod_data['id'],
                    sku=sp['sku'],
                    description=sp['name'],
                    quantity=qty,
                    unit_price=sp['price'],
                    total_price=subtotal
                ))

            quote = Quote(
                user_id=user_id,
                customer_id=cid,
                quote_number=f"QT-{random.randint(10000, 99999)}",
                status=random.choice(list(QuoteStatus)),
                total_amount=total,
                items=q_items,
                valid_until=datetime.utcnow() + timedelta(days=30)
            )
            
            qid = await db.create_quote(quote)
            print(f"Created quote {qid}")

    print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed())
