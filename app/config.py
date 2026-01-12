"""
Configuration management for Mercura application.
Loads and validates environment variables.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Mercura"
    app_env: str = "development"
    debug: bool = True
    secret_key: str
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", "8000"))  # Use PORT from Render, fallback to 8000
    
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    
    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-flash"
    
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
    
    @property
    def allowed_extensions(self) -> list[str]:
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


# Global settings instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.export_temp_dir, exist_ok=True)
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
