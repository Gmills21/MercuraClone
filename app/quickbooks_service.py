"""
QuickBooks integration service.
OAuth2 flow, data sync, and real-time updates.
"""

import os
import json
import base64
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import httpx
from loguru import logger
from app.config import settings
from app.services.security_service import security_service
from app import database_sqlite as db  # Using local SQLite for persistence

# QuickBooks OAuth2 settings
QUICKBOOKS_CLIENT_ID = settings.qbo_client_id or os.getenv("QBO_CLIENT_ID", "")
QUICKBOOKS_CLIENT_SECRET = settings.qbo_client_secret or os.getenv("QBO_CLIENT_SECRET", "")
QUICKBOOKS_SANDBOX = settings.quickbooks_sandbox or os.getenv("QUICKBOOKS_SANDBOX", "true").lower() == "true"
QBO_REDIRECT_URI = settings.qbo_redirect_uri or os.getenv("QBO_REDIRECT_URI", "")

# URLs
QB_BASE_URL = "https://sandbox-quickbooks.api.intuit.com" if QUICKBOOKS_SANDBOX else "https://quickbooks.api.intuit.com"
QB_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
QB_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
QB_DISCONNECT_URL = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"

# In-memory token store (use Redis/DB in production)
_qb_tokens: Dict[str, Dict[str, Any]] = {}


class QuickBooksService:
    """QuickBooks API integration service."""
    
    def __init__(self, realm_id: Optional[str] = None, access_token: Optional[str] = None):
        self.realm_id = realm_id
        self.access_token = access_token
        self.base_url = QB_BASE_URL
    
    @staticmethod
    def get_authorization_url(user_id: str, redirect_uri: str) -> str:
        """Generate QuickBooks OAuth authorization URL."""
        # Generate PKCE params
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode('utf-8').rstrip('=')
        
        # Store code_verifier for later
        _qb_tokens[f"{user_id}_verifier"] = {
            "verifier": code_verifier,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Build auth URL
        params = {
            "client_id": QUICKBOOKS_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "com.intuit.quickbooks.accounting",
            "state": user_id,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{QB_AUTH_URL}?{query}"
    
    @staticmethod
    async def exchange_code_for_token(
        code: str,
        user_id: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange OAuth code for access token."""
        # Get code_verifier
        verifier_data = _qb_tokens.get(f"{user_id}_verifier", {})
        code_verifier = verifier_data.get("verifier")
        
        if not code_verifier:
            return {"error": "Code verifier not found. Please restart authentication."}
        
        # Build token request
        auth_string = base64.b64encode(
            f"{QUICKBOOKS_CLIENT_ID}:{QUICKBOOKS_CLIENT_SECRET}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    QB_TOKEN_URL,
                    headers=headers,
                    data=data
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    token_dict = {
                        "access_token": token_data["access_token"],
                        "refresh_token": token_data["refresh_token"],
                        "realm_id": token_data.get("realmId"),
                        "expires_at": (datetime.utcnow() + timedelta(seconds=token_data["expires_in"])).isoformat(),
                        "connected_at": datetime.utcnow().isoformat(),
                    }
                    
                    # Store in-memory
                    _qb_tokens[user_id] = token_dict
                    
                    # Store in DB (Encrypted) - for now using user_id as organization_id 
                    # if we don't have the real organization_id handy
                    encrypted_data = security_service.encrypt(json.dumps(token_dict))
                    db.save_integration_secret(user_id, "quickbooks", encrypted_data)
                    
                    # Clean up verifier
                    del _qb_tokens[f"{user_id}_verifier"]
                    
                    logger.info(f"QuickBooks connected and encrypted for user {user_id}")
                    return {
                        "success": True,
                        "realm_id": token_data.get("realmId"),
                    }
                else:
                    logger.error(f"Token exchange failed: {response.text}")
                    return {"error": f"Authentication failed: {response.text}"}
                    
        except Exception as e:
            logger.error(f"Error exchanging code: {e}")
            return {"error": str(e)}
    
    async def _make_request(self, endpoint: str, method: str = "GET", data: Any = None) -> Dict:
        """Make authenticated request to QuickBooks API."""
        if not self.access_token or not self.realm_id:
            return {"error": "Not authenticated"}
        
        url = f"{self.base_url}/v3/company/{self.realm_id}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                else:
                    return {"error": f"Unsupported method: {method}"}
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"QB API error: {response.status_code} - {response.text}")
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"error": str(e)}
    
    # ========== ITEMS (PRODUCTS) ==========
    
    async def get_items(self, limit: int = 100) -> List[Dict]:
        """Get all items (products) from QuickBooks."""
        query = f"SELECT * FROM Item WHERE Type IN ('Inventory', 'NonInventory', 'Service') MAXRESULTS {limit}"
        result = await self._make_request(f"/query?query={query}")
        
        if "error" in result:
            return []
        
        items = result.get("QueryResponse", {}).get("Item", [])
        return [
            {
                "qb_id": item.get("Id"),
                "name": item.get("Name"),
                "sku": item.get("Sku") or item.get("Name"),
                "description": item.get("Description", ""),
                "price": item.get("UnitPrice", 0),
                "cost": item.get("PurchaseCost", 0),
                "type": item.get("Type"),
                "active": item.get("Active", True),
            }
            for item in items
        ]
    
    async def create_item(self, product: Dict[str, Any]) -> Dict:
        """Create a new item in QuickBooks."""
        item_data = {
            "Name": product["name"],
            "Sku": product.get("sku", ""),
            "Description": product.get("description", ""),
            "UnitPrice": product.get("price", 0),
            "PurchaseCost": product.get("cost", 0),
            "Type": "NonInventory",
            "IncomeAccountRef": {
                "name": "Sales of Product Income"
            },
            "ExpenseAccountRef": {
                "name": "Cost of Goods Sold"
            }
        }
        
        return await self._make_request("/item", "POST", item_data)
    
    # ========== CUSTOMERS ==========
    
    async def get_customers(self, limit: int = 100) -> List[Dict]:
        """Get all customers from QuickBooks."""
        query = f"SELECT * FROM Customer MAXRESULTS {limit}"
        result = await self._make_request(f"/query?query={query}")
        
        if "error" in result:
            return []
        
        customers = result.get("QueryResponse", {}).get("Customer", [])
        return [
            {
                "qb_id": cust.get("Id"),
                "name": cust.get("DisplayName"),
                "email": cust.get("PrimaryEmailAddr", {}).get("Address", ""),
                "phone": cust.get("PrimaryPhone", {}).get("FreeFormNumber", ""),
                "company": cust.get("CompanyName", ""),
                "active": cust.get("Active", True),
            }
            for cust in customers
        ]
    
    async def create_customer(self, customer: Dict[str, Any]) -> Dict:
        """Create a new customer in QuickBooks (with duplicate check)."""
        # Step 1: Check if customer already exists (fuzzy match by name)
        name = customer["name"]
        # Escape single quotes for query
        safe_name = name.replace("'", "\\'")
        query = f"SELECT * FROM Customer WHERE DisplayName LIKE '{safe_name}%'"
        
        search_result = await self._make_request(f"/query?query={query}")
        
        if "QueryResponse" in search_result and "Customer" in search_result["QueryResponse"]:
            # Found a match! Don't create duplicate.
            existing = search_result["QueryResponse"]["Customer"][0]
            logger.info(f"Customer '{name}' already exists in QB (Id: {existing['Id']}). linking.")
            return {"Customer": existing, "status": "linked", "note": "Customer linked to existing record."}

        # Step 2: Create if not found
        customer_data = {
            "DisplayName": customer["name"],
            "PrimaryEmailAddr": {
                "Address": customer.get("email", "")
            },
            "PrimaryPhone": {
                "FreeFormNumber": customer.get("phone", "")
            },
            "CompanyName": customer.get("company", ""),
        }
        
        return await self._make_request("/customer", "POST", customer_data)
    
    # ========== ESTIMATES (QUOTES) ==========
    
    async def create_estimate(self, quote: Dict[str, Any], items: List[Dict]) -> Dict:
        """Create an estimate (quote) in QuickBooks."""
        # Build line items
        line_items = []
        for item in items:
            line_items.append({
                "DetailType": "SalesItemLineDetail",
                "SalesItemLineDetail": {
                    "ItemRef": {
                        "value": item.get("qb_id", ""),
                        "name": item.get("name", "")
                    },
                    "UnitPrice": item.get("unit_price", 0),
                    "Qty": item.get("quantity", 1),
                },
                "Amount": item.get("total_price", 0),
                "Description": item.get("description", "")
            })
        
        estimate_data = {
            "CustomerRef": {
                "value": quote.get("qb_customer_id", "")
            },
            "Line": line_items,
            "TotalAmt": quote.get("total", 0),
            "TxnDate": quote.get("created_at", datetime.now().strftime("%Y-%m-%d")),
            "PrivateNote": quote.get("notes", ""),
        }
        
        return await self._make_request("/estimate", "POST", estimate_data)
    
    # ========== SYNC OPERATIONS ==========
    
    async def sync_products_to_qb(self, products: List[Dict]) -> Dict[str, Any]:
        """Sync local products to QuickBooks."""
        results = {"created": 0, "errors": 0, "items": []}
        
        for product in products:
            result = await self.create_item(product)
            if "error" in result:
                results["errors"] += 1
            else:
                results["created"] += 1
                results["items"].append({
                    "local_id": product.get("id"),
                    "qb_id": result.get("Item", {}).get("Id"),
                    "name": product.get("name"),
                })
        
        return results
    
    async def sync_customers_to_qb(self, customers: List[Dict]) -> Dict[str, Any]:
        """Sync local customers to QuickBooks."""
        results = {"created": 0, "errors": 0, "customers": []}
        
        for customer in customers:
            result = await self.create_customer(customer)
            if "error" in result:
                results["errors"] += 1
            else:
                results["created"] += 1
                results["customers"].append({
                    "local_id": customer.get("id"),
                    "qb_id": result.get("Customer", {}).get("Id"),
                    "name": customer.get("name"),
                })
        
        return results
    
    async def import_from_qb(self) -> Dict[str, Any]:
        """Import products and customers from QuickBooks."""
        items = await self.get_items()
        customers = await self.get_customers()
        
        return {
            "products": items,
            "customers": customers,
            "product_count": len(items),
            "customer_count": len(customers),
        }


# ========== HELPER FUNCTIONS ==========

def get_qb_service(user_id: str) -> Optional[QuickBooksService]:
    """Get QuickBooks service for a user, loading from DB if needed."""
    token_data = _qb_tokens.get(user_id)
    
    if not token_data:
        # Try loading from DB
        encrypted_data = db.get_integration_secret(user_id, "quickbooks")
        if encrypted_data:
            try:
                decrypted_json = security_service.decrypt(encrypted_data)
                token_data = json.loads(decrypted_json)
                _qb_tokens[user_id] = token_data
                logger.info(f"Loaded and decrypted QuickBooks tokens for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to decrypt QB tokens for {user_id}: {e}")
                return None
    
    if not token_data:
        return None
    
    # Check if token is expired (simplified - should refresh in production)
    expires_at_str = token_data.get("expires_at")
    if not expires_at_str:
        return None
        
    expires_at = datetime.fromisoformat(expires_at_str)
    if datetime.utcnow() > expires_at:
        logger.warning(f"QuickBooks token expired for user {user_id}")
        return None
    
    return QuickBooksService(
        realm_id=token_data.get("realm_id"),
        access_token=token_data.get("access_token")
    )


def is_connected(user_id: str) -> bool:
    """Check if user has QuickBooks connected."""
    return user_id in _qb_tokens and "access_token" in _qb_tokens[user_id]


def disconnect(user_id: str) -> bool:
    """Disconnect QuickBooks for a user."""
    if user_id in _qb_tokens:
        del _qb_tokens[user_id]
        logger.info(f"QuickBooks disconnected for user {user_id}")
        return True
    return False


def get_connection_info(user_id: str) -> Optional[Dict]:
    """Get connection info for display."""
    token_data = _qb_tokens.get(user_id)
    if not token_data:
        return None
    
    return {
        "connected": True,
        "connected_at": token_data.get("connected_at"),
        "realm_id": token_data.get("realm_id"),
        "expires_at": token_data.get("expires_at"),
    }
