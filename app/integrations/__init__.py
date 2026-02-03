"""
ERP Integration Abstraction Layer
Supports multiple ERP systems through common interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class ERPProvider(ABC):
    """
    Abstract base class for ERP integrations.
    
    All ERP providers (QuickBooks, SAP, Oracle, etc.) implement this interface.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'quickbooks', 'sap')"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name (e.g., 'QuickBooks Online')"""
        pass
    
    @abstractmethod
    async def get_auth_url(self, user_id: str, redirect_uri: str) -> str:
        """Get OAuth authorization URL"""
        pass
    
    @abstractmethod
    async def connect(self, code: str, user_id: str, redirect_uri: str) -> Dict[str, Any]:
        """Complete OAuth flow and store tokens"""
        pass
    
    @abstractmethod
    async def is_connected(self, user_id: str) -> bool:
        """Check if user has active connection"""
        pass
    
    @abstractmethod
    async def disconnect(self, user_id: str) -> bool:
        """Disconnect and remove tokens"""
        pass
    
    @abstractmethod
    async def import_customers(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Import customers from ERP"""
        pass
    
    @abstractmethod
    async def import_products(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Import products/items from ERP"""
        pass
    
    @abstractmethod
    async def export_quote(self, user_id: str, quote_data: Dict) -> Dict[str, Any]:
        """Export quote as estimate/invoice to ERP"""
        pass


class ERPRegistry:
    """Registry of available ERP providers."""
    
    _providers: Dict[str, ERPProvider] = {}
    
    @classmethod
    def register(cls, provider: ERPProvider):
        """Register an ERP provider."""
        cls._providers[provider.name] = provider
    
    @classmethod
    def get(cls, name: str) -> Optional[ERPProvider]:
        """Get provider by name."""
        return cls._providers.get(name)
    
    @classmethod
    def list_available(cls) -> List[Dict[str, str]]:
        """List all available providers."""
        return [
            {"name": p.name, "display_name": p.display_name}
            for p in cls._providers.values()
        ]
    
    @classmethod
    def get_user_connections(cls, user_id: str) -> Dict[str, bool]:
        """Get connection status for all providers."""
        # This would check database in production
        return {name: False for name in cls._providers.keys()}


class ERPService:
    """
    Unified ERP service that works with any registered provider.
    
    Usage:
        service = ERPService("quickbooks")
        customers = await service.import_customers(user_id)
    """
    
    def __init__(self, provider_name: str):
        self.provider = ERPRegistry.get(provider_name)
        if not self.provider:
            raise ValueError(f"Unknown ERP provider: {provider_name}")
    
    async def get_auth_url(self, user_id: str, redirect_uri: str) -> str:
        return await self.provider.get_auth_url(user_id, redirect_uri)
    
    async def connect(self, code: str, user_id: str, redirect_uri: str) -> Dict[str, Any]:
        return await self.provider.connect(code, user_id, redirect_uri)
    
    async def is_connected(self, user_id: str) -> bool:
        return await self.provider.is_connected(user_id)
    
    async def disconnect(self, user_id: str) -> bool:
        return await self.provider.disconnect(user_id)
    
    async def import_customers(self, user_id: str, limit: int = 100) -> List[Dict]:
        return await self.provider.import_customers(user_id, limit)
    
    async def import_products(self, user_id: str, limit: int = 100) -> List[Dict]:
        return await self.provider.import_products(user_id, limit)
    
    async def export_quote(self, user_id: str, quote_data: Dict) -> Dict[str, Any]:
        return await self.provider.export_quote(user_id, quote_data)
