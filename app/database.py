"""
Database connection and operations for Supabase.
"""

from supabase import create_client, Client
from app.config import settings
from app.models import InboundEmail, LineItem, User, Catalog
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class Database:
    """Supabase database client wrapper."""
    
    def __init__(self):
        """Initialize Supabase client."""
        try:
            self.client: Client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            self.admin_client: Client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase client: {e}")
            logger.warning("Database operations will not be available. Please check your SUPABASE_URL and keys.")
            # Set to None so we can check if database is available
            self.client = None
            self.admin_client = None
    
    # ==================== INBOUND EMAILS ====================
    
    async def create_inbound_email(self, email: InboundEmail) -> str:
        """Create a new inbound email record."""
        try:
            data = email.model_dump(exclude={'id'}, exclude_none=True)
            result = self.admin_client.table('inbound_emails').insert(data).execute()
            return result.data[0]['id']
        except Exception as e:
            logger.error(f"Error creating inbound email: {e}")
            raise
    
    async def update_email_status(
        self, 
        email_id: str, 
        status: str, 
        error_message: Optional[str] = None
    ) -> None:
        """Update email processing status."""
        try:
            update_data = {'status': status}
            if error_message:
                update_data['error_message'] = error_message
            
            self.admin_client.table('inbound_emails')\
                .update(update_data)\
                .eq('id', email_id)\
                .execute()
        except Exception as e:
            logger.error(f"Error updating email status: {e}")
            raise
    
    async def get_email_by_id(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get email by ID."""
        try:
            result = self.admin_client.table('inbound_emails')\
                .select('*')\
                .eq('id', email_id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching email: {e}")
            return None
    
    async def get_emails_by_status(
        self, 
        status: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get emails by status."""
        try:
            result = self.admin_client.table('inbound_emails')\
                .select('*')\
                .eq('status', status)\
                .limit(limit)\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching emails by status: {e}")
            return []
    
    # ==================== LINE ITEMS ====================
    
    async def create_line_items(
        self, 
        email_id: str, 
        items: List[Dict[str, Any]]
    ) -> List[str]:
        """Create multiple line items for an email."""
        try:
            # Add email_id to each item
            items_data = [
                {**item, 'email_id': email_id} 
                for item in items
            ]
            
            result = self.admin_client.table('line_items')\
                .insert(items_data)\
                .execute()
            
            return [item['id'] for item in result.data]
        except Exception as e:
            logger.error(f"Error creating line items: {e}")
            raise
    
    async def get_line_items_by_email(
        self, 
        email_id: str
    ) -> List[Dict[str, Any]]:
        """Get all line items for an email."""
        try:
            result = self.admin_client.table('line_items')\
                .select('*')\
                .eq('email_id', email_id)\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching line items: {e}")
            return []
    
    async def get_line_items_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get line items within a date range."""
        try:
            query = self.admin_client.table('line_items')\
                .select('*, inbound_emails!inner(user_id, received_at)')\
                .gte('inbound_emails.received_at', start_date.isoformat())\
                .lte('inbound_emails.received_at', end_date.isoformat())
            
            if user_id:
                query = query.eq('inbound_emails.user_id', user_id)
            
            result = query.execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching line items by date range: {e}")
            return []
    
    # ==================== USERS ====================
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        try:
            result = self.admin_client.table('users')\
                .select('*')\
                .eq('email', email)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return None
    
    async def create_user(self, user: User) -> str:
        """Create a new user."""
        try:
            data = user.model_dump(exclude={'id'}, exclude_none=True)
            result = self.admin_client.table('users').insert(data).execute()
            return result.data[0]['id']
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def increment_user_email_count(self, user_id: str) -> None:
        """Increment user's daily email count."""
        try:
            # Get current count
            user = self.admin_client.table('users')\
                .select('emails_processed_today')\
                .eq('id', user_id)\
                .execute()
            
            if user.data:
                new_count = user.data[0]['emails_processed_today'] + 1
                self.admin_client.table('users')\
                    .update({'emails_processed_today': new_count})\
                    .eq('id', user_id)\
                    .execute()
        except Exception as e:
            logger.error(f"Error incrementing email count: {e}")
    
    # ==================== CATALOGS ====================
    
    async def get_catalog_item(
        self, 
        user_id: str, 
        sku: str
    ) -> Optional[Dict[str, Any]]:
        """Get catalog item by SKU."""
        try:
            result = self.admin_client.table('catalogs')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('sku', sku)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching catalog item: {e}")
            return None
    
    async def upsert_catalog_item(
        self, 
        catalog: Catalog
    ) -> str:
        """Insert or update catalog item."""
        try:
            data = catalog.model_dump(exclude={'id'}, exclude_none=True)
            result = self.admin_client.table('catalogs')\
                .upsert(data, on_conflict='user_id,sku')\
                .execute()
            return result.data[0]['id']
        except Exception as e:
            logger.error(f"Error upserting catalog item: {e}")
            raise


# Global database instance
# Initialize immediately but handle errors gracefully
try:
    db = Database()
except Exception as e:
    logger.error(f"Failed to create database instance: {e}")
    # Create a dummy instance that will fail on use
    db = None
