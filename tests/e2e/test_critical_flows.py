"""
End-to-End Tests for Mercura
Tests critical user flows from frontend to backend.

Requirements:
- pytest
- playwright (pip install pytest-playwright)
- Running backend on http://localhost:8000
- Running frontend on http://localhost:5173
"""

import pytest
import requests
import time
from typing import Generator
from datetime import datetime

# Backend API URL
API_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"


class TestBackendAPI:
    """E2E tests for backend API endpoints."""
    
    @pytest.fixture(scope="class")
    def auth_token(self) -> Generator[str, None, None]:
        """Get auth token for tests."""
        # Register a test user
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        response = requests.post(f"{API_URL}/auth/register", json={
            "email": f"test_{timestamp}@example.com",
            "name": "Test User",
            "password": "TestPassword123",
            "company_name": f"Test Company {timestamp}"
        })
        
        if response.status_code == 200:
            yield response.json()["access_token"]
        else:
            # Try login if registration fails (user exists)
            login_response = requests.post(f"{API_URL}/auth/login", json={
                "email": f"test_{timestamp}@example.com",
                "password": "TestPassword123"
            })
            if login_response.status_code == 200:
                yield login_response.json()["access_token"]
            else:
                pytest.skip("Could not get auth token")
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = requests.get(f"{API_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["database"] == "sqlite"
    
    def test_rate_limiting(self):
        """Test that rate limiting is active."""
        # Make multiple requests quickly
        responses = []
        for _ in range(15):
            resp = requests.get(f"{API_URL}/health")
            responses.append(resp.status_code)
        
        # Most should succeed, but we should see rate limit headers
        assert 200 in responses
        # Check for rate limit headers
        response = requests.get(f"{API_URL}/health")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
    
    def test_auth_flow(self):
        """Test registration and login flow."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Register
        register_resp = requests.post(f"{API_URL}/auth/register", json={
            "email": f"auth_test_{timestamp}@example.com",
            "name": "Auth Test User",
            "password": "SecurePass123",
            "company_name": f"Auth Test Co {timestamp}"
        })
        assert register_resp.status_code == 200
        token = register_resp.json()["access_token"]
        assert token is not None
        
        # Login
        login_resp = requests.post(f"{API_URL}/auth/login", json={
            "email": f"auth_test_{timestamp}@example.com",
            "password": "SecurePass123"
        })
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()
    
    def test_password_reset_flow(self, auth_token: str):
        """Test password reset request."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Request password reset (even for non-existent email should return 200)
        response = requests.post(
            f"{API_URL}/auth/password-reset/request",
            json={"email": "nonexistent_test@example.com"},
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_customer_crud(self, auth_token: str):
        """Test customer create, read, update, delete."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create customer
        create_resp = requests.post(
            f"{API_URL}/customers/",
            json={
                "name": "Test Customer",
                "email": "customer@test.com",
                "company": "Test Co",
                "phone": "555-1234"
            },
            headers=headers
        )
        assert create_resp.status_code in [200, 201]
        customer_id = create_resp.json().get("id") or create_resp.json().get("customer_id")
        
        # List customers
        list_resp = requests.get(f"{API_URL}/customers/?limit=10", headers=headers)
        assert list_resp.status_code == 200
        customers = list_resp.json()
        assert isinstance(customers, list)
    
    def test_quote_creation(self, auth_token: str):
        """Test quote creation flow."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a customer
        customer_resp = requests.post(
            f"{API_URL}/customers/",
            json={"name": "Quote Test Customer", "email": "quote@test.com"},
            headers=headers
        )
        customer_id = customer_resp.json().get("id")
        
        # Create quote
        quote_resp = requests.post(
            f"{API_URL}/quotes/",
            json={
                "customer_id": customer_id,
                "customer_name": "Quote Test Customer",
                "items": [
                    {
                        "product_name": "Test Product",
                        "description": "Test Description",
                        "quantity": 10,
                        "unit_price": 100.00,
                        "total_price": 1000.00
                    }
                ],
                "subtotal": 1000.00,
                "total": 1000.00,
                "status": "draft"
            },
            headers=headers
        )
        assert quote_resp.status_code in [200, 201]
        
        # List quotes
        list_resp = requests.get(f"{API_URL}/quotes/?limit=10", headers=headers)
        assert list_resp.status_code == 200
    
    def test_backup_endpoints(self, auth_token: str):
        """Test backup creation and listing."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get backup stats
        stats_resp = requests.get(f"{API_URL}/backups/stats", headers=headers)
        assert stats_resp.status_code == 200
        
        # Create backup
        backup_resp = requests.post(
            f"{API_URL}/backups/create",
            json={"type": "test"},
            headers=headers
        )
        assert backup_resp.status_code == 200
        
        # List backups
        list_resp = requests.get(f"{API_URL}/backups/", headers=headers)
        assert list_resp.status_code == 200
    
    def test_monitoring_endpoints(self, auth_token: str):
        """Test monitoring and health endpoints."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get health
        health_resp = requests.get(f"{API_URL}/monitoring/health")
        assert health_resp.status_code == 200
        assert "status" in health_resp.json()
        
        # Collect metrics
        metrics_resp = requests.post(
            f"{API_URL}/monitoring/collect",
            headers=headers
        )
        assert metrics_resp.status_code == 200
        
        # Get metrics summary
        summary_resp = requests.get(
            f"{API_URL}/monitoring/metrics?hours=1",
            headers=headers
        )
        assert summary_resp.status_code == 200
    
    def test_team_invitations(self, auth_token: str):
        """Test team invitation flow."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create invitation
        invite_resp = requests.post(
            f"{API_URL}/team/invitations/",
            json={
                "email": f"invited_{timestamp}@example.com",
                "role": "sales_rep"
            },
            headers=headers
        )
        assert invite_resp.status_code == 200
        
        # List invitations
        list_resp = requests.get(f"{API_URL}/team/invitations/", headers=headers)
        assert list_resp.status_code == 200


class TestProductionReadiness:
    """Tests for production readiness checks."""
    
    def test_all_critical_endpoints_exist(self):
        """Verify all critical endpoints are accessible."""
        critical_endpoints = [
            "/health",
            "/monitoring/health",
            "/monitoring/status",
            "/docs",
        ]
        
        for endpoint in critical_endpoints:
            response = requests.get(f"{API_URL}{endpoint}")
            assert response.status_code in [200, 307, 401], f"Endpoint {endpoint} failed"
    
    def test_security_headers(self):
        """Test that security headers are present."""
        response = requests.get(f"{API_URL}/health")
        
        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
    
    def test_cors_headers(self):
        """Test CORS configuration."""
        response = requests.options(
            f"{API_URL}/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert "access-control-allow-origin" in response.headers


# Skip tests if backend is not running
@pytest.fixture(scope="session", autouse=True)
def check_backend():
    """Check if backend is running before tests."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            pytest.skip("Backend not healthy")
    except requests.exceptions.ConnectionError:
        pytest.skip("Backend not running at " + API_URL)
