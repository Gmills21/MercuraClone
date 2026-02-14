"""
QuickBooks Online Integration
Implements ERPProvider interface with production-grade resilience.

Features:
- Circuit breaker pattern for API failures
- Retry logic with exponential backoff
- Token refresh handling
- Graceful degradation when QB is unavailable
"""

import os
import base64
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import httpx
from loguru import logger

from app.config import settings
from app.integrations import ERPProvider, ERPRegistry
from app.errors import AppError, ErrorCategory, ErrorSeverity
from app.utils.resilience import (
    CircuitBreaker, with_retry, RetryConfig, with_timeout, TimeoutError
)

# QuickBooks OAuth2 settings
QUICKBOOKS_CLIENT_ID = settings.qbo_client_id or os.getenv("QBO_CLIENT_ID", "")
QUICKBOOKS_CLIENT_SECRET = settings.qbo_client_secret or os.getenv("QBO_CLIENT_SECRET", "")
QUICKBOOKS_SANDBOX = settings.quickbooks_sandbox or os.getenv("QUICKBOOKS_SANDBOX", "true").lower() == "true"
QBO_REDIRECT_URI = settings.qbo_redirect_uri or os.getenv("QBO_REDIRECT_URI", "")

# URLs
QB_BASE_URL = "https://sandbox-quickbooks.api.intuit.com" if QUICKBOOKS_SANDBOX else "https://quickbooks.api.intuit.com"
QB_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
QB_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

# In-memory token store (use Redis/DB in production)
_qb_tokens: Dict[str, Dict[str, Any]] = {}

# Custom exception for QB service unavailability
class QBServiceUnavailableError(Exception):
    """QuickBooks service temporarily unavailable."""
    pass


# Retry configuration for QB API calls
QB_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=60.0,
    retryable_exceptions=[
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.NetworkError,
        QBServiceUnavailableError
    ]
)


class QBAuthError(Exception):
    """QuickBooks authentication error."""
    pass


class QuickBooksProvider(ERPProvider):
    """QuickBooks Online ERP integration with resilience patterns."""
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker("quickbooks")
        self.timeout_seconds = 30.0
    
    @property
    def name(self) -> str:
        return "quickbooks"
    
    @property
    def display_name(self) -> str:
        return "QuickBooks Online"
    
    def _create_error(
        self,
        message: str,
        code: str = "QB_ERROR",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        retryable: bool = True
    ) -> AppError:
        """Create a user-friendly error for QuickBooks issues."""
        return AppError(
            category=ErrorCategory.ERP_ERROR,
            code=code,
            message=message,
            severity=severity,
            http_status=503,
            retryable=retryable,
            retry_after_seconds=300 if retryable else None,
            suggested_action="Your data has been saved locally. Try syncing again from Settings > Integrations."
        )
    
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
        """Complete OAuth flow with error handling."""
        verifier_data = _qb_tokens.get(f"{user_id}_verifier", {})
        code_verifier = verifier_data.get("verifier")
        
        if not code_verifier:
            return {
                "success": False,
                "error": "Code verifier not found. Please restart the connection process.",
                "retryable": True
            }
        
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
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
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
                    
                    return {
                        "success": True,
                        "realm_id": token_data.get("realmId"),
                        "message": "Successfully connected to QuickBooks"
                    }
                elif response.status_code == 401:
                    return {
                        "success": False,
                        "error": "Authentication failed. Please check your QuickBooks credentials.",
                        "error_code": "QB_AUTH_FAILED",
                        "retryable": False
                    }
                else:
                    return {
                        "success": False,
                        "error": f"QuickBooks authentication failed: {response.status_code}",
                        "error_code": f"QB_ERROR_{response.status_code}",
                        "retryable": True
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Connection to QuickBooks timed out. Please try again.",
                "error_code": "QB_TIMEOUT",
                "retryable": True
            }
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            return {
                "success": False,
                "error": "Could not connect to QuickBooks. Please try again.",
                "error_code": "QB_CONNECTION_ERROR",
                "retryable": True
            }
    
    async def _refresh_token(self, user_id: str) -> bool:
        """Refresh the access token if expired."""
        token_data = _qb_tokens.get(user_id, {})
        refresh_token = token_data.get("refresh_token")
        
        if not refresh_token:
            return False
        
        auth_string = base64.b64encode(
            f"{QUICKBOOKS_CLIENT_ID}:{QUICKBOOKS_CLIENT_SECRET}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(QB_TOKEN_URL, headers=headers, data=data)
                
                if response.status_code == 200:
                    new_tokens = response.json()
                    _qb_tokens[user_id].update({
                        "access_token": new_tokens["access_token"],
                        "refresh_token": new_tokens.get("refresh_token", refresh_token),
                        "expires_at": (datetime.utcnow() + timedelta(seconds=new_tokens["expires_in"])).isoformat(),
                    })
                    logger.info(f"Token refreshed for user {user_id}")
                    return True
                else:
                    logger.error(f"Token refresh failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False
    
    async def _api_call_with_retry(
        self,
        user_id: str,
        method: str,
        url: str,
        headers: Dict = None,
        params: Dict = None,
        json_data: Dict = None
    ) -> Dict[str, Any]:
        """
        Make API call with retry logic and circuit breaker.
        
        Handles token refresh automatically.
        """
        if self.circuit_breaker.is_open:
            return {
                "success": False,
                "error": "QuickBooks is temporarily unavailable due to recent errors.",
                "error_code": "CIRCUIT_OPEN",
                "retryable": True,
                "retry_after": 300
            }
        
        token_data = _qb_tokens.get(user_id, {})
        access_token = token_data.get("access_token")
        
        if not access_token:
            return {
                "success": False,
                "error": "Not connected to QuickBooks. Please connect in Settings > Integrations.",
                "error_code": "QB_NOT_CONNECTED",
                "retryable": False
            }
        
        # Check if token needs refresh
        expires_at = token_data.get("expires_at")
        if expires_at:
            try:
                expiry = datetime.fromisoformat(expires_at)
                if datetime.utcnow() > expiry - timedelta(minutes=5):
                    refreshed = await self._refresh_token(user_id)
                    if refreshed:
                        access_token = _qb_tokens[user_id]["access_token"]
            except Exception as e:
                logger.warning(f"Token expiry check failed: {e}")
        
        request_headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        if headers:
            request_headers.update(headers)
        
        last_error = None
        
        for attempt in range(QB_RETRY_CONFIG.max_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    if method == "GET":
                        response = await client.get(url, headers=request_headers, params=params)
                    elif method == "POST":
                        response = await client.post(url, headers=request_headers, json=json_data)
                    else:
                        raise ValueError(f"Unsupported method: {method}")
                    
                    # Handle token expiration (401)
                    if response.status_code == 401:
                        refreshed = await self._refresh_token(user_id)
                        if refreshed and attempt < QB_RETRY_CONFIG.max_attempts - 1:
                            # Retry with new token
                            access_token = _qb_tokens[user_id]["access_token"]
                            request_headers["Authorization"] = f"Bearer {access_token}"
                            continue
                        else:
                            return {
                                "success": False,
                                "error": "QuickBooks authentication expired. Please reconnect.",
                                "error_code": "QB_AUTH_EXPIRED",
                                "retryable": False
                            }
                    
                    # Handle rate limiting (429)
                    if response.status_code == 429:
                        if attempt < QB_RETRY_CONFIG.max_attempts - 1:
                            delay = QB_RETRY_CONFIG.calculate_delay(attempt)
                            logger.warning(f"QB rate limited, waiting {delay:.1f}s")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            return {
                                "success": False,
                                "error": "QuickBooks rate limit exceeded. Please try again in a few minutes.",
                                "error_code": "QB_RATE_LIMITED",
                                "retryable": True,
                                "retry_after": 60
                            }
                    
                    # Handle service errors (5xx)
                    if response.status_code >= 500:
                        raise QBServiceUnavailableError(f"QB returned {response.status_code}")
                    
                    # Handle other errors
                    if response.status_code >= 400:
                        return {
                            "success": False,
                            "error": f"QuickBooks API error: {response.status_code}",
                            "error_code": f"QB_ERROR_{response.status_code}",
                            "details": response.text[:500],
                            "retryable": response.status_code >= 500
                        }
                    
                    # Success
                    self.circuit_breaker.record_success()
                    return {
                        "success": True,
                        "data": response.json()
                    }
                    
            except (httpx.TimeoutException, TimeoutError):
                last_error = "timeout"
                if attempt < QB_RETRY_CONFIG.max_attempts - 1:
                    delay = QB_RETRY_CONFIG.calculate_delay(attempt)
                    logger.warning(f"QB request timed out, retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    self.circuit_breaker.record_failure()
                    return {
                        "success": False,
                        "error": "QuickBooks is not responding. Please try again later.",
                        "error_code": "QB_TIMEOUT",
                        "retryable": True,
                        "retry_after": 300
                    }
                    
            except QBServiceUnavailableError:
                last_error = "service_unavailable"
                if attempt < QB_RETRY_CONFIG.max_attempts - 1:
                    delay = QB_RETRY_CONFIG.calculate_delay(attempt)
                    logger.warning(f"QB service unavailable, retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    self.circuit_breaker.record_failure()
                    return {
                        "success": False,
                        "error": "QuickBooks is experiencing issues. Please try again later.",
                        "error_code": "QB_SERVICE_UNAVAILABLE",
                        "retryable": True,
                        "retry_after": 300
                    }
                    
            except Exception as e:
                logger.error(f"Unexpected QB API error: {e}")
                self.circuit_breaker.record_failure()
                return {
                    "success": False,
                    "error": "An unexpected error occurred while connecting to QuickBooks.",
                    "error_code": "QB_UNEXPECTED_ERROR",
                    "retryable": False
                }
        
        # All retries exhausted
        self.circuit_breaker.record_failure()
        return {
            "success": False,
            "error": "Could not complete QuickBooks operation after multiple attempts.",
            "error_code": "QB_RETRY_EXHAUSTED",
            "retryable": True,
            "retry_after": 300
        }
    
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
        """Import customers from QuickBooks with error handling."""
        token_data = _qb_tokens.get(user_id, {})
        realm_id = token_data.get("realm_id")
        
        if not realm_id:
            logger.warning("No realm_id for QuickBooks import")
            return []
        
        url = f"{QB_BASE_URL}/v3/company/{realm_id}/query"
        query = f"SELECT * FROM Customer MAXRESULTS {limit}"
        
        result = await self._api_call_with_retry(
            user_id=user_id,
            method="GET",
            url=url,
            params={"query": query}
        )
        
        if not result.get("success"):
            logger.error(f"Failed to import customers: {result.get('error')}")
            return []
        
        try:
            data = result["data"]
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
        except Exception as e:
            logger.error(f"Error parsing QB customers: {e}")
            return []
    
    async def import_products(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Import items/products from QuickBooks."""
        token_data = _qb_tokens.get(user_id, {})
        realm_id = token_data.get("realm_id")
        
        if not realm_id:
            return []
        
        url = f"{QB_BASE_URL}/v3/company/{realm_id}/query"
        query = f"SELECT * FROM Item WHERE Type IN ('Inventory', 'NonInventory', 'Service') MAXRESULTS {limit}"
        
        result = await self._api_call_with_retry(
            user_id=user_id,
            method="GET",
            url=url,
            params={"query": query}
        )
        
        if not result.get("success"):
            logger.error(f"Failed to import products: {result.get('error')}")
            return []
        
        try:
            data = result["data"]
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
        except Exception as e:
            logger.error(f"Error parsing QB products: {e}")
            return []
    
    async def create_item(self, user_id: str, item: Dict) -> Dict:
        """Create a new item in QuickBooks."""
        qb_item = {
            "Name": item.get("name"),
            "Sku": item.get("sku"),
            "Description": item.get("description", ""),
            "UnitPrice": item.get("price", 0),
            "PurchaseCost": item.get("cost", 0),
            "Type": "NonInventory" if not item.get("track_inventory") else "Inventory",
            "IncomeAccountRef": {"value": "1"},  # Should be configured
            "ExpenseAccountRef": {"value": "2"},  # Should be configured
        }
        
        token_data = _qb_tokens.get(user_id, {})
        realm_id = token_data.get("realm_id")
        if not realm_id:
            return {"error": "Not connected"}
            
        url = f"{QB_BASE_URL}/v3/company/{realm_id}/item"
        return await self._api_call_with_retry(user_id, "POST", url, json_data=qb_item)

    async def create_customer(self, user_id: str, customer: Dict) -> Dict:
        """Create a new customer in QuickBooks."""
        qb_customer = {
            "DisplayName": customer.get("name"),
            "CompanyName": customer.get("company", ""),
            "PrimaryEmailAddr": {"Address": customer.get("email", "")},
            "PrimaryPhone": {"FreeFormNumber": customer.get("phone", "")},
        }
        
        token_data = _qb_tokens.get(user_id, {})
        realm_id = token_data.get("realm_id")
        if not realm_id:
            return {"error": "Not connected"}
            
        url = f"{QB_BASE_URL}/v3/company/{realm_id}/customer"
        return await self._api_call_with_retry(user_id, "POST", url, json_data=qb_customer)

    async def sync_products_to_qb(self, products: List[Dict], user_id: str) -> Dict:
        """Sync local products to QuickBooks."""
        results = {
            "created": 0,
            "errors": 0,
            "products": [],
        }
        
        for product in products:
            result = await self.create_item(user_id, product)
            if not result.get("success"):
                results["errors"] += 1
            else:
                data = result.get("data", {})
                results["created"] += 1
                results["products"].append({
                    "local_id": product.get("id"),
                    "qb_id": data.get("Item", {}).get("Id"),
                    "name": product.get("name"),
                })
        
        return results

    async def sync_customers_to_qb(self, customers: List[Dict], user_id: str) -> Dict:
        """Sync local customers to QuickBooks."""
        results = {
            "created": 0,
            "errors": 0,
            "customers": [],
        }
        
        for customer in customers:
            result = await self.create_customer(user_id, customer)
            if not result.get("success"):
                results["errors"] += 1
            else:
                data = result.get("data", {})
                results["created"] += 1
                results["customers"].append({
                    "local_id": customer.get("id"),
                    "qb_id": data.get("Customer", {}).get("Id"),
                    "name": customer.get("name"),
                })
        
        return results

    async def get_items(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get raw items from QuickBooks for preview."""
        # Re-use import logic but return raw-ish structure matching old service if needed
        # Or just use import_products which returns standardized format.
        # old service returned: {qb_id, name, sku, description, price, cost, type, active}
        # import_products returns: {erp_id, name, sku, description, price, cost, type, source}
        # We can map erp_id to qb_id for compatibility
        items = await self.import_products(user_id, limit)
        for item in items:
            item["qb_id"] = item.pop("erp_id")
            item["active"] = True # import_products doesn't return active status, assume true?
        return items

    async def get_customers(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get raw customers for preview."""
        customers = await self.import_customers(user_id, limit)
        for c in customers:
            c["qb_id"] = c.pop("erp_id")
            c["active"] = True
        return customers

    async def import_from_qb(self, user_id: str) -> Dict[str, Any]:
        """Import products and customers from QuickBooks."""
        # This wrapper matches the old service's convenience method
        items = await self.get_items(user_id)
        customers = await self.get_customers(user_id)
        
        return {
            "products": items,
            "customers": customers,
            "product_count": len(items),
            "customer_count": len(customers),
        }

    async def export_quote(self, user_id: str, quote_data: Dict) -> Dict[str, Any]:
        """Export quote as Estimate to QuickBooks."""
        token_data = _qb_tokens.get(user_id, {})
        realm_id = token_data.get("realm_id")
        
        if not realm_id:
            return {
                "success": False,
                "error": "Not connected to QuickBooks. Please connect in Settings > Integrations.",
                "error_code": "QB_NOT_CONNECTED",
                "retryable": False
            }
        
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
        
        result = await self._api_call_with_retry(
            user_id=user_id,
            method="POST",
            url=url,
            json_data=estimate_data
        )
        
        if result.get("success"):
            data = result["data"]
            return {
                "success": True,
                "estimate_id": data.get("Estimate", {}).get("Id"),
                "provider": "quickbooks",
                "message": "Quote successfully exported to QuickBooks"
            }
        else:
            # Return error with context
            return {
                "success": False,
                "error": result.get("error", "Failed to export quote"),
                "error_code": result.get("error_code", "QB_EXPORT_FAILED"),
                "retryable": result.get("retryable", True),
                "retry_after": result.get("retry_after")
            }
    
    async def get_connection_details(self, user_id: str) -> Optional[Dict]:
        """Get detailed connection info for UI."""
        token_data = _qb_tokens.get(user_id, {})
        if not token_data or not token_data.get("access_token"):
            return None
            
        return {
            "realm_id": token_data.get("realm_id"),
            "connected_at": token_data.get("connected_at"), # Note: connected_at might not be in _qb_tokens in this new file?
            "expires_at": token_data.get("expires_at")
        }

    def get_status(self) -> Dict[str, Any]:
        """Get integration status."""
        return {
            "provider": "quickbooks",
            "configured": bool(QUICKBOOKS_CLIENT_ID and QUICKBOOKS_CLIENT_SECRET),
            "sandbox": QUICKBOOKS_SANDBOX,
            "circuit_breaker": self.circuit_breaker.get_status()
        }


# Register the provider
ERPRegistry.register(QuickBooksProvider())
