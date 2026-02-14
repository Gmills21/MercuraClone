"""
Tests for Password Reset Service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.services.password_reset_service import PasswordResetService


class TestPasswordResetService:
    """Test cases for password reset functionality."""
    
    def test_hash_token_consistency(self):
        """Test that token hashing is consistent."""
        token = "test_token_123"
        hash1 = PasswordResetService._hash_token(token)
        hash2 = PasswordResetService._hash_token(token)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex is 64 chars
    
    def test_generate_token_unique(self):
        """Test that generated tokens are unique."""
        tokens = [PasswordResetService._generate_token() for _ in range(10)]
        assert len(set(tokens)) == 10  # All unique
        assert all(len(t) > 20 for t in tokens)  # Reasonably long
    
    @patch('app.services.password_reset_service.atomic')
    @patch('app.services.password_reset_service.get_db')
    def test_create_reset_token_for_existing_user(self, mock_get_db, mock_atomic):
        """Test creating reset token for existing user."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        mock_atomic.return_value.__enter__.return_value = mock_conn
        
        # Mock user lookup
        mock_cursor.fetchone.side_effect = [
            {"id": "user-123", "email": "test@example.com", "name": "Test User", "is_active": 1, "org_name": "Test Org"},
            {"count": 0}  # No recent attempts
        ]
        
        result = PasswordResetService.create_reset_token("test@example.com")
        
        assert result["success"] is True
        assert result["token"] is not None
        assert result["user"] is not None
        assert result["user"]["email"] == "test@example.com"
    
    @patch('app.services.password_reset_service.get_db')
    def test_create_reset_token_for_nonexistent_user(self, mock_get_db):
        """Test creating reset token for non-existent user (should still return success)."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        # Mock user lookup - no user found
        mock_cursor.fetchone.return_value = None
        
        result = PasswordResetService.create_reset_token("nonexistent@example.com")
        
        # Should return success to prevent email enumeration
        assert result["success"] is True
        assert result["token"] is None
        assert result["user"] is None
    
    @patch('app.services.password_reset_service.get_db')
    def test_create_reset_token_rate_limit(self, mock_get_db):
        """Test rate limiting for password reset."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        # Mock user lookup
        mock_cursor.fetchone.side_effect = [
            {"id": "user-123", "email": "test@example.com", "name": "Test User", "is_active": 1, "org_name": "Test Org"},
            {"count": 5}  # 5 recent attempts (at limit)
        ]
        
        result = PasswordResetService.create_reset_token("test@example.com")
        
        assert result["success"] is False
        assert "Too many reset attempts" in result["error"]
    
    @patch('app.services.password_reset_service.get_db')
    def test_validate_valid_token(self, mock_get_db):
        """Test validating a valid token."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        # Mock token lookup - valid token
        future_time = (datetime.utcnow() + timedelta(hours=23)).isoformat()
        mock_cursor.fetchone.return_value = {
            "id": "token-123",
            "user_id": "user-123",
            "expires_at": future_time,
            "is_used": 0,
            "email": "test@example.com",
            "name": "Test User",
            "is_active": 1
        }
        
        # Generate a token and hash it for lookup
        token = PasswordResetService._generate_token()
        
        result = PasswordResetService.validate_token(token)
        
        assert result["valid"] is True
        assert result["user_id"] == "user-123"
        assert result["email"] == "test@example.com"
    
    @patch('app.services.password_reset_service.get_db')
    def test_validate_used_token(self, mock_get_db):
        """Test validating an already used token."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        # Mock token lookup - used token
        mock_cursor.fetchone.return_value = {
            "id": "token-123",
            "user_id": "user-123",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "is_used": 1,  # Already used
            "email": "test@example.com",
            "name": "Test User",
            "is_active": 1
        }
        
        token = PasswordResetService._generate_token()
        result = PasswordResetService.validate_token(token)
        
        assert result["valid"] is False
        assert "already been used" in result["error"]
    
    @patch('app.services.password_reset_service.get_db')
    def test_validate_expired_token(self, mock_get_db):
        """Test validating an expired token."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        # Mock token lookup - expired token
        mock_cursor.fetchone.return_value = {
            "id": "token-123",
            "user_id": "user-123",
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),  # Expired
            "is_used": 0,
            "email": "test@example.com",
            "name": "Test User",
            "is_active": 1
        }
        
        token = PasswordResetService._generate_token()
        result = PasswordResetService.validate_token(token)
        
        assert result["valid"] is False
        assert "expired" in result["error"]
    
    @patch('app.services.password_reset_service.get_db')
    @patch('app.services.password_reset_service.transaction')
    @patch('app.services.password_reset_service.PasswordResetService.validate_token')
    @patch('app.auth._hash_password')
    def test_reset_password_success(self, mock_hash_pw, mock_validate, mock_transaction, mock_get_db):
        """Test successful password reset."""
        # Setup mocks
        mock_validate.return_value = {
            "valid": True,
            "user_id": "user-123",
            "email": "test@example.com"
        }
        mock_hash_pw.return_value = "new_hashed_password"
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        mock_transaction.return_value.__enter__.return_value = mock_conn
        
        token = PasswordResetService._generate_token()
        result = PasswordResetService.reset_password(token, "NewPassword123")
        
        assert result["success"] is True
        assert "reset successfully" in result["message"]
        mock_cursor.execute.assert_any_call(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            ("new_hashed_password", mock_cursor.execute.call_args[0][0][1], "user-123")
        )
    
    def test_reset_password_weak_password(self):
        """Test password reset with weak password."""
        token = PasswordResetService._generate_token()
        
        # Too short
        result = PasswordResetService.reset_password(token, "short")
        assert result["success"] is False
        assert "8 characters" in result["error"]
        
        # No uppercase
        result = PasswordResetService.reset_password(token, "lowercase123")
        assert result["success"] is False
        assert "uppercase" in result["error"]
        
        # No lowercase
        result = PasswordResetService.reset_password(token, "UPPERCASE123")
        assert result["success"] is False
        assert "lowercase" in result["error"]
        
        # No number
        result = PasswordResetService.reset_password(token, "NoNumbersHere")
        assert result["success"] is False
        assert "number" in result["error"]
