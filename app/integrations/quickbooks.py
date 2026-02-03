"""
QuickBooks Online Integration
Implements ERPProvider interface
"""

import os
import base64
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import httpx
from loguru import logger

from app.integrations import ERPProvider, ERPRegistry

# QuickBooks OAuth2 settings
QUICKBOOKS_CLIENT_ID = os.getenv("QUICKBOOKS_CLIENT_ID", "")
QUICKBOOKS_CLIENT_SECRET = os.getenv("QUICKBOOKS_CLIENT_SECRET", "")
QUICKBOOKS_SANDBOX = os.getenv("QUICKBOOKS_SANDBOX", "true").lower() == "true"

# URLs
QB_BASE_URL = "https://sandbox-quickbooks.api.intuit.com" if QUICKBOOKS_SANDBOX else "https://quickbooks.api.intuit.com"
QB_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
QB_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

# In-memory token store (use Redis/DB in production)
_qb_tokens: Dict[str, Dict[str, Any]] = {}


class QuickBooksProvider(ERPProvider):
    """QuickBooks Online ERP integration."""
    
    @property
    def name(self) -> str:
        return "quickbooks"
    
    @property
    def display_name(self) -> str:
        return "QuickBooks Online"
    
    async def get_auth_url(self, user_id: str, redirect_uri: str) -> str:
        """Generate QuickBooks OAuth authorization URL."""
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode('utf-8').rstrip('=')
        
        _qb_tokens[f"{user_id}_verifier"] = {
            "verifier": code_verifier,
            "created_at": datetime.utcnow().isoformat()
        }
        
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
    
    async def connect(self, code: str, user_id: str, redirect_uri: str) -> Dict[str, Any]:
        """Complete OAuth flow."""
        verifier_data = _qb_tokens.get(f"{user_id}_verifier", {})
        code_verifier = verifier_data.get("verifier")
        
        if not code_verifier:
            return {"error": "Code verifier not found"}
        
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
                response = await client.post(QB_TOKEN_URL, headers=headers, data=data)
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    _qb_tokens[user_id] = {
                        "access_token": token_data["access_token"],
                        "refresh_token": token_data["refresh_token"],
                        "realm_id": token_data.get("realmId"),
                        "expires_at": (datetime.utcnow() + timedelta(seconds=token_data["expires_in"])).isoformat(),
                    }
                    
                    del _qb_tokens[f"{user_id}_verifier"]
                    
                    return {"success": True, "realm_id": token_data.get("realmId")}
                else:
                    return {"error": f"Authentication failed: {response.text}"}
                    
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            return {"error": str(e)}
    
    async def is_connected(self, user_id: str) -> bool:
        """Check if user has active connection."""
        return user_id in _qb_tokens and "access_token" in _qb_tokens[user_id]
    
    async def disconnect(self, user_id: str) -> bool:
        """Disconnect QuickBooks."""
        if user_id in _qb_tokens:
            del _qb_tokens[user_id]
            return True
        return False
    
    async def import_customers(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Import customers from QuickBooks."""
        token_data = _qb_tokens.get(user_id, {})
        realm_id = token_data.get("realm_id")
        access_token = token_data.get("access_token")
        
        if not realm_id or not access_token:
            return []
        
        url = f"{QB_BASE_URL}/v3/company/{realm_id}/query"
        query = f"SELECT * FROM Customer MAXRESULTS {limit}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params={"query": query})
                
                if response.status_code == 200:
                    data = response.json()
                    customers = data.get("QueryResponse", {}).get("Customer", [])
                    
                    return [
                        {
                            "erp_id": c.get("Id"),
                            "name": c.get("DisplayName"),
                            "email": c.get("PrimaryEmailAddr", {}).get("Address", ""),
                            "phone": c.get("PrimaryPhone", {}).get("FreeFormNumber", ""),
                            "company": c.get("CompanyName", ""),
                            "source": "quickbooks"
                        }
                        for c in customers
                    ]
                else:
                    logger.error(f"QB API error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Import customers failed: {e}")
            return []
    
    async def import_products(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Import items/products from QuickBooks."""
        token_data = _qb_tokens.get(user_id, {})
        realm_id = token_data.get("realm_id")
        access_token = token_data.get("access_token")
        
        if not realm_id or not access_token:
            return []
        
        url = f"{QB_BASE_URL}/v3/company/{realm_id}/query"
        query = f"SELECT * FROM Item WHERE Type IN ('Inventory', 'NonInventory', 'Service') MAXRESULTS {limit}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params={"query": query})
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("QueryResponse", {}).get("Item", [])
                    
                    return [
                        {
                            "erp_id": item.get("Id"),
                            "name": item.get("Name"),
                            "sku": item.get("Sku") or item.get("Name"),
                            "description": item.get("Description", ""),
                            "price": item.get("UnitPrice", 0),
                            "cost": item.get("PurchaseCost", 0),
                            "type": item.get("Type"),
                            "source": "quickbooks"
                        }
                        for item in items
                    ]
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Import products failed: {e}")
            return []
    
    async def export_quote(self, user_id: str, quote_data: Dict) -> Dict[str, Any]:
        """Export quote as Estimate to QuickBooks."""
        token_data = _qb_tokens.get(user_id, {})
        realm_id = token_data.get("realm_id")
        access_token = token_data.get("access_token")
        
        if not realm_id or not access_token:
            return {"error": "Not connected to QuickBooks"}
        
        url = f"{QB_BASE_URL}/v3/company/{realm_id}/estimate"
        
        # Build line items
        line_items = []
        for item in quote_data.get("items", []):
            line_items.append({
                "DetailType": "SalesItemLineDetail",
                "SalesItemLineDetail": {
                    "ItemRef": {
                        "value": item.get("product_id", ""),
                        "name": item.get("product_name", "")
                    },
                    "UnitPrice": item.get("unit_price", 0),
                    "Qty": item.get("quantity", 1),
                },
                "Amount": item.get("total_price", 0),
                "Description": item.get("description", "")
            })
        
        estimate_data = {
            "CustomerRef": {
                "value": quote_data.get("customer_id", "")
            },
            "Line": line_items,
            "TotalAmt": quote_data.get("total", 0),
            "TxnDate": quote_data.get("created_at", datetime.now().strftime("%Y-%m-%d")),
            "PrivateNote": quote_data.get("notes", ""),
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=estimate_data)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "success": True,
                        "estimate_id": data.get("Estimate", {}).get("Id"),
                        "provider": "quickbooks"
                    }
                else:
                    return {"error": f"Export failed: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Export quote failed: {e}")
            return {"error": str(e)}


# Register the provider
ERPRegistry.register(QuickBooksProvider())
