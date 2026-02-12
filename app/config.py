"""
Configuration management for Mercura application.
Loads and validates environment variables.
"""

from pydantic_settings import BaseSettings
from typing import Optional, List, Tuple
import os
import sys


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Mercura"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = ""  # Allow empty for startup, validate later
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", "8000"))  # Use PORT from Render, fallback to 8000
    
    # Database
    database_url: str = "sqlite:///mercura.db"
    
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""
    
    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-flash-preview"
    byok_mode: bool = False  # Bring Your Own Key mode for bootstrapper phase
    
    # OpenRouter (multi-key support)
    openrouter_api_key: Optional[str] = None
    openrouter_api_key_1: Optional[str] = None
    openrouter_api_key_2: Optional[str] = None
    openrouter_api_key_3: Optional[str] = None
    openrouter_api_key_4: Optional[str] = None
    openrouter_api_key_5: Optional[str] = None
    openrouter_api_key_6: Optional[str] = None
    openrouter_api_key_7: Optional[str] = None
    openrouter_api_key_8: Optional[str] = None
    openrouter_api_key_9: Optional[str] = None
    
    # DeepSeek
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: Optional[str] = None
    deepseek_model: Optional[str] = None
    
    # Knowledge Base
    knowledge_base_enabled: bool = False
    
    # Paddle Billing
    paddle_api_key: Optional[str] = None
    paddle_vendor_id: Optional[str] = None
    paddle_webhook_secret: Optional[str] = None
    paddle_sandbox: bool = True
    
    # QuickBooks
    qbo_client_id: Optional[str] = None
    qbo_client_secret: Optional[str] = None
    qbo_redirect_uri: Optional[str] = None
    quickbooks_sandbox: bool = True
    
    # Security
    encryption_key: Optional[str] = None
    
    # Email Provider
    email_provider: str = "sendgrid"  # sendgrid or mailgun
    
    # SendGrid
    sendgrid_webhook_secret: Optional[str] = None
    sendgrid_inbound_domain: Optional[str] = None
    
    # Mailgun
    mailgun_api_key: Optional[str] = None
    mailgun_webhook_secret: Optional[str] = None
    mailgun_domain: Optional[str] = None
    
    # Google Sheets
    google_sheets_credentials_path: Optional[str] = None
    
    # PostHog Analytics
    posthog_api_key: Optional[str] = None
    posthog_host: str = "https://app.posthog.com"
    
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

    # n8n Integration
    n8n_enabled: bool = False
    n8n_webhook_url: Optional[str] = None
    n8n_api_key: Optional[str] = None
        
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/mercura.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
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
        if self.email_provider == "sendgrid":
            return bool(self.sendgrid_webhook_secret and self.sendgrid_inbound_domain)
        elif self.email_provider == "mailgun":
            return bool(self.mailgun_api_key and self.mailgun_webhook_secret)
        return False
    
    def validate_required_settings(self) -> Tuple[bool, List[str]]:
        """Validate that all required settings are present. Returns (is_valid, missing_fields)."""
        missing = []
        
        if not self.secret_key:
            missing.append("SECRET_KEY")
        if not self.supabase_url:
            missing.append("SUPABASE_URL")
        if not self.supabase_key:
            missing.append("SUPABASE_KEY")
        if not self.supabase_service_key:
            missing.append("SUPABASE_SERVICE_KEY")
        if not self.gemini_api_key:
            missing.append("GEMINI_API_KEY")
        
        return len(missing) == 0, missing


# Global settings instance - initialize with error handling
try:
    settings = Settings()
except Exception as e:
    # If Settings initialization fails completely, create minimal settings for health check
    print(f"Warning: Failed to load settings: {e}", file=sys.stderr)
    # Create a minimal settings object with defaults
    settings = Settings(
        secret_key=os.getenv("SECRET_KEY", ""),
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_key=os.getenv("SUPABASE_KEY", ""),
        supabase_service_key=os.getenv("SUPABASE_SERVICE_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
    )

# Ensure required directories exist (with error handling)
try:
    os.makedirs(settings.export_temp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
except Exception as e:
    print(f"Warning: Failed to create directories: {e}", file=sys.stderr)
