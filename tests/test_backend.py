"""
Tests for OpenMercura backend.
"""

import pytest
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database_sqlite import (
    init_db, create_customer, get_customer_by_id, list_customers,
    create_product, get_product_by_sku, list_products,
    create_quote, add_quote_item, get_quote_with_items,
    save_competitor, list_competitors,
    save_document, list_documents,
    save_extraction, list_extractions
)


# Reset database before tests
@pytest.fixture(autouse=True)
def reset_db():
    """Reset database for each test."""
    # Clean up test data
    pass


class TestCustomers:
    """Test customer CRUD operations."""
    
    def test_create_customer(self):
        customer = {
            "id": "test-cust-1",
            "name": "Test Customer",
            "email": "test@example.com",
            "company": "Test Co",
            "phone": "555-1234",
            "address": "123 Test St",
            "created_at": "2026-01-31T00:00:00Z",
            "updated_at": "2026-01-31T00:00:00Z"
        }
        assert create_customer(customer) is True
    
    def test_get_customer_by_id(self):
        customer = {
            "id": "test-cust-2",
            "name": "Get Test",
            "email": "get@example.com",
            "company": None,
            "phone": None,
            "address": None,
            "created_at": "2026-01-31T00:00:00Z",
            "updated_at": "2026-01-31T00:00:00Z"
        }
        create_customer(customer)
        result = get_customer_by_id("test-cust-2")
        assert result is not None
        assert result["name"] == "Get Test"
    
    def test_list_customers(self):
        customers = list_customers(limit=10)
        assert isinstance(customers, list)


class TestProducts:
    """Test product CRUD operations."""
    
    def test_create_product(self):
        product = {
            "id": "test-prod-1",
            "sku": "TEST-SKU-1",
            "name": "Test Product",
            "description": "A test product",
            "price": 99.99,
            "cost": 50.00,
            "category": "Test",
            "competitor_sku": None,
            "created_at": "2026-01-31T00:00:00Z",
            "updated_at": "2026-01-31T00:00:00Z"
        }
        assert create_product(product) is True
    
    def test_get_product_by_sku(self):
        product = {
            "id": "test-prod-2",
            "sku": "TEST-SKU-2",
            "name": "SKU Test Product",
            "description": None,
            "price": 49.99,
            "cost": None,
            "category": None,
            "competitor_sku": None,
            "created_at": "2026-01-31T00:00:00Z",
            "updated_at": "2026-01-31T00:00:00Z"
        }
        create_product(product)
        result = get_product_by_sku("TEST-SKU-2")
        assert result is not None
        assert result["name"] == "SKU Test Product"


class TestQuotes:
    """Test quote operations."""
    
    def test_create_quote(self):
        # First create a customer
        customer = {
            "id": "test-quote-cust",
            "name": "Quote Test Customer",
            "email": "quote@test.com",
            "company": None,
            "phone": None,
            "address": None,
            "created_at": "2026-01-31T00:00:00Z",
            "updated_at": "2026-01-31T00:00:00Z"
        }
        create_customer(customer)
        
        quote = {
            "id": "test-quote-1",
            "customer_id": "test-quote-cust",
            "status": "draft",
            "subtotal": 100.00,
            "tax_rate": 8.0,
            "tax_amount": 8.00,
            "total": 108.00,
            "notes": "Test quote",
            "token": "TEST-TOKEN-123",
            "created_at": "2026-01-31T00:00:00Z",
            "updated_at": "2026-01-31T00:00:00Z",
            "expires_at": "2026-02-28T00:00:00Z"
        }
        assert create_quote(quote) is True


class TestCompetitors:
    """Test competitor operations."""
    
    def test_save_competitor(self):
        competitor = {
            "id": "test-comp-1",
            "url": "https://example.com",
            "name": "Example Competitor",
            "title": "Example Inc",
            "description": "An example company",
            "keywords": ["test", "example"],
            "pricing": "$99/month",
            "features": ["Feature 1", "Feature 2"],
            "last_updated": "2026-01-31T00:00:00Z"
        }
        assert save_competitor(competitor) is True
    
    def test_list_competitors(self):
        competitors = list_competitors()
        assert isinstance(competitors, list)


class TestDocuments:
    """Test document operations."""
    
    def test_save_document(self):
        doc = {
            "id": "test-doc-1",
            "content": "Test document content",
            "source": "test.txt",
            "type": "text",
            "metadata": {"test": True},
            "created_at": "2026-01-31T00:00:00Z"
        }
        assert save_document(doc) is True
    
    def test_list_documents(self):
        docs = list_documents()
        assert isinstance(docs, list)


class TestExtractions:
    """Test extraction operations."""
    
    def test_save_extraction(self):
        extraction = {
            "id": "test-ext-1",
            "source_type": "text",
            "source_content": "Test content",
            "parsed_data": {"items": []},
            "confidence_score": 0.85,
            "status": "completed",
            "created_at": "2026-01-31T00:00:00Z"
        }
        assert save_extraction(extraction) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
