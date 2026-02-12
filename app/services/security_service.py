"""
Security service for encryption and decryption.
Uses Fernet symmetric encryption.
"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.config import settings
from loguru import logger

class SecurityService:
    """Handles encryption and decryption of sensitive data."""
    
    def __init__(self):
        self._fernet = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the Fernet cipher with the encryption key."""
        try:
            key = settings.encryption_key
            if not key:
                logger.warning("ENCRYPTION_KEY not set. Using fallback key (UNSAFE).")
                key = "fallback-key-must-be-32-bytes-long"
                
            # Fernet key must be a base64-encoded 32-byte key
            # If the provided key isn't in that format, we'll derive one from it
            try:
                # Try to use as is if it's already a valid Fernet key
                self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
            except Exception:
                # Derive a valid key from the provided string
                password = key.encode() if isinstance(key, str) else key
                salt = b'mercura-salt' # In production, use a unique salt
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                derived_key = base64.urlsafe_b64encode(kdf.derive(password))
                self._fernet = Fernet(derived_key)
                
        except Exception as e:
            logger.error(f"Failed to initialize SecurityService: {e}")
            raise

    def encrypt(self, data: str) -> str:
        """Encrypt a string."""
        if not data:
            return ""
        try:
            return self._fernet.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return data # Fallback to cleartext (reconsider for production)

    def decrypt(self, token: str) -> str:
        """Decrypt an encrypted string."""
        if not token:
            return ""
        try:
            return self._fernet.decrypt(token.encode()).decode()
        except Exception as e:
            # If decryption fails, it might be cleartext or wrong key
            logger.debug(f"Decryption failed: {e}")
            return token

# Global instance
security_service = SecurityService()
