"""
Configuration management for OpenMercura application.
Loads and validates environment variables.
Uses ONLY free tools: SQLite, OpenRouter, local ChromaDB.
"""

from pydantic_settings import BaseSettings
from typing import Optional, List, Tuple, Dict, Any
import os
import sys


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "OpenMercura"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "dev-secret-key-change-in-production"
    host: str = "127.0.0.1"
    port: int = int(os.getenv("PORT", "9000"))
    
    # Gemini API
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    
    # OpenRouter (FREE TIER - replaces paid Gemini)
    openrouter_api_key: str = ""
    openrouter_model: str = "deepseek/deepseek-chat:free"
    
    # Direct DeepSeek or Fallback API (OpenAI Compatible)
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    
    # Email Provider (optional - webhooks still work without)
    email_provider: str = "none"  # none, sendgrid, or mailgun
    
    # QuickBooks Integration (optional)
    quickbooks_client_id: str = ""
    quickbooks_client_secret: str = ""
    quickbooks_sandbox: bool = True
    
    # SendGrid (optional)
    sendgrid_webhook_secret: Optional[str] = None
    sendgrid_inbound_domain: Optional[str] = None
    
    # Mailgun (optional)
    mailgun_api_key: Optional[str] = None
    mailgun_webhook_secret: Optional[str] = None
    mailgun_domain: Optional[str] = None
    
    # Export Settings
    max_export_rows: int = 10000
    export_temp_dir: str = "./temp/exports"
    
    # Processing Settings
    max_attachment_size_mb: int = 25
    allowed_attachment_types: str = "pdf,png,jpg,jpeg"
    confidence_threshold: float = 0.7
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/mercura.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from old .env
    
    @property
    def allowed_extensions(self) -> List[str]:
        """Get list of allowed file extensions."""
        return self.allowed_attachment_types.split(",")
    
    @property
    def max_attachment_size_bytes(self) -> int:
        """Get max attachment size in bytes."""
        return self.max_attachment_size_mb * 1024 * 1024
    
    def validate_email_provider(self) -> bool:
        """Validate that required email provider credentials are set."""
        if self.email_provider == "none":
            return True  # Email is optional
        if self.email_provider == "sendgrid":
            return bool(self.sendgrid_webhook_secret and self.sendgrid_inbound_domain)
        elif self.email_provider == "mailgun":
            return bool(self.mailgun_api_key and self.mailgun_webhook_secret)
        return False
    
    def validate_required_settings(self) -> Tuple[bool, List[str]]:
        """Validate that all required settings are present. Returns (is_valid, missing_fields)."""
        missing = []
        
        # OpenRouter is optional - we'll warn but not fail
        # This keeps the app functional even without AI features
        
        return len(missing) == 0, missing
    
    def get_ai_status(self) -> Dict[str, Any]:
        """Get status of AI services."""
        return {
            "openrouter_configured": bool(self.openrouter_api_key),
            "deepseek_configured": bool(self.deepseek_api_key),
            "preferred_model": self.openrouter_model if self.openrouter_api_key else self.deepseek_model,
            "rag_available": None,  # Will be set at runtime
        }


# Global settings instance - initialize with error handling
try:
    settings = Settings()
except Exception as e:
    # If Settings initialization fails completely, create minimal settings
    print(f"Warning: Failed to load settings: {e}", file=sys.stderr)
    settings = Settings()

# Ensure required directories exist (with error handling)
try:
    os.makedirs(settings.export_temp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    os.makedirs("./data", exist_ok=True)  # For SQLite and ChromaDB
except Exception as e:
    print(f"Warning: Failed to create directories: {e}", file=sys.stderr)
