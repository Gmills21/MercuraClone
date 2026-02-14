"""
Tests for Team Invitation Service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json

from app.services.team_invitation_service import TeamInvitationService


class TestTeamInvitationService:
    """Test cases for team invitation functionality."""
    
    def test_generate_token_unique(self):
        """Test that generated tokens are unique."""
        tokens = [TeamInvitationService._generate_token() for _ in range(10)]
        assert len(set(tokens)) == 10
        assert all(len(t) > 20 for t in tokens)
    
    @patch('app.services.team_invitation_service.atomic')
    @patch('app.services.team_invitation_service.get_db')
    def test_create_invitation_success(self, mock_get_db, mock_atomic):
        """Test creating a new invitation successfully."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        mock_atomic.return_value.__enter__.return_value = mock_conn
        
        # Mock: user doesn't exist, has seats available, no existing invite
        mock_cursor.fetchone.side_effect = [
            None,  # User doesn't exist
            {"seats_total": 5, "seats_used": 2},  # 3 seats available
            None,  # No existing invite
            {"count": 1},  # 1 pending invite
            {"name": "Test Org"},  # Org name
            {"name": "Inviter Name"}  # Inviter name
        ]
        
        result = TeamInvitationService.create_invitation(
            organization_id="org-123",
            email="newuser@example.com",
            role="sales_rep",
            invited_by="user-456"
        )
        
        assert result["success"] is True
        assert result["token"] is not None
        assert result["invite_id"] is not None
        assert result["email"] == "newuser@example.com"
        assert result["role"] == "sales_rep"
        assert result["is_resend"] is False
    
    @patch('app.services.team_invitation_service.get_db')
    def test_create_invitation_user_already_exists(self, mock_get_db):
        """Test creating invitation when user already exists."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        # Mock: user already exists
        mock_cursor.fetchone.return_value = {
            "id": "existing-user",
            "email": "existing@example.com"
        }
        
        result = TeamInvitationService.create_invitation(
            organization_id="org-123",
            email="existing@example.com",
            role="sales_rep",
            invited_by="user-456"
        )
        
        assert result["success"] is False
        assert "already exists" in result["error"]
    
    @patch('app.services.team_invitation_service.get_db')
    def test_create_invitation_seat_limit_reached(self, mock_get_db):
        """Test creating invitation when seat limit is reached."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        # Mock: user doesn't exist, but no seats available
        mock_cursor.fetchone.side_effect = [
            None,  # User doesn't exist
            {"seats_total": 5, "seats_used": 5},  # No seats available
            {"count": 0}  # No pending invites
        ]
        
        result = TeamInvitationService.create_invitation(
            organization_id="org-123",
            email="newuser@example.com",
            role="sales_rep",
            invited_by="user-456"
        )
        
        assert result["success"] is False
        assert "Seat limit reached" in result["error"]
    
    @patch('app.services.team_invitation_service.get_db')
    def test_create_invitation_resend_existing(self, mock_get_db):
        """Test resending an existing pending invitation."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        # Mock: existing pending invite found
        future_time = (datetime.utcnow() + timedelta(days=6)).isoformat()
        mock_cursor.fetchone.side_effect = [
            None,  # User doesn't exist
            {"seats_total": 5, "seats_used": 2},  # Seats available
            {"id": "invite-123", "token": "existing-token", "expires_at": future_time},  # Existing invite
        ]
        
        result = TeamInvitationService.create_invitation(
            organization_id="org-123",
            email="invited@example.com",
            role="sales_rep",
            invited_by="user-456"
        )
        
        assert result["success"] is True
        assert result["is_resend"] is True
        assert result["token"] == "existing-token"
    
    @patch('app.services.team_invitation_service.get_db')
    def test_validate_valid_invitation(self, mock_get_db):
        """Test validating a valid invitation token."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        future_time = (datetime.utcnow() + timedelta(days=6)).isoformat()
        mock_cursor.fetchone.return_value = {
            "id": "invite-123",
            "organization_id": "org-123",
            "email": "invited@example.com",
            "role": "sales_rep",
            "expires_at": future_time,
            "status": "pending",
            "metadata": "{}",
            "org_name": "Test Org",
            "inviter_name": "John Doe"
        }
        
        result = TeamInvitationService.validate_invitation("valid-token")
        
        assert result["valid"] is True
        assert result["email"] == "invited@example.com"
        assert result["org_name"] == "Test Org"
        assert result["role"] == "sales_rep"
    
    @patch('app.services.team_invitation_service.get_db')
    def test_validate_already_accepted_invitation(self, mock_get_db):
        """Test validating an already accepted invitation."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = {
            "id": "invite-123",
            "organization_id": "org-123",
            "email": "invited@example.com",
            "role": "sales_rep",
            "expires_at": (datetime.utcnow() + timedelta(days=6)).isoformat(),
            "status": "accepted",  # Already accepted
            "metadata": "{}",
            "org_name": "Test Org",
            "inviter_name": "John Doe"
        }
        
        result = TeamInvitationService.validate_invitation("accepted-token")
        
        assert result["valid"] is False
        assert "already been accepted" in result["error"]
    
    @patch('app.services.team_invitation_service.transaction')
    @patch('app.services.team_invitation_service.get_db')
    def test_accept_invitation_success(self, mock_get_db, mock_transaction):
        """Test successfully accepting an invitation."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        mock_transaction.return_value.__enter__.return_value = mock_conn
        
        # Mock validation to return valid
        future_time = (datetime.utcnow() + timedelta(days=6)).isoformat()
        
        with patch.object(TeamInvitationService, 'validate_invitation') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "invite_id": "invite-123",
                "organization_id": "org-123",
                "org_name": "Test Org",
                "email": "invited@example.com",
                "role": "sales_rep"
            }
            
            # Mock: user doesn't exist yet
            mock_cursor.fetchone.return_value = None
            
            result = TeamInvitationService.accept_invitation(
                token="valid-token",
                name="New User",
                password="SecurePass123"
            )
            
            assert result["success"] is True
            assert result["token"] is not None  # Auth token
            assert result["email"] == "invited@example.com"
            assert result["organization_id"] == "org-123"
    
    def test_accept_invitation_weak_password(self):
        """Test accepting with weak password fails."""
        with patch.object(TeamInvitationService, 'validate_invitation') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "invite_id": "invite-123",
                "organization_id": "org-123",
                "org_name": "Test Org",
                "email": "invited@example.com",
                "role": "sales_rep"
            }
            
            # Too short
            result = TeamInvitationService.accept_invitation(
                token="valid-token",
                name="New User",
                password="short"
            )
            assert result["success"] is False
            assert "8 characters" in result["error"]
            
            # No uppercase
            result = TeamInvitationService.accept_invitation(
                token="valid-token",
                name="New User",
                password="lowercase123"
            )
            assert result["success"] is False
            assert "uppercase" in result["error"]
    
    @patch('app.services.team_invitation_service.atomic')
    def test_cancel_invitation_success(self, mock_atomic):
        """Test canceling a pending invitation."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_atomic.return_value.__enter__.return_value = mock_conn
        
        # Mock: invite exists and user is owner
        mock_cursor.fetchone.side_effect = [
            {"id": "invite-123", "organization_id": "org-123", "status": "pending", "owner_user_id": "user-456"},
            {"role": "admin"}  # User is admin
        ]
        
        result = TeamInvitationService.cancel_invitation("invite-123", "user-456")
        
        assert result["success"] is True
        assert "canceled" in result["message"]
    
    @patch('app.services.team_invitation_service.atomic')
    def test_cancel_invitation_unauthorized(self, mock_atomic):
        """Test canceling without permission fails."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_atomic.return_value.__enter__.return_value = mock_conn
        
        # Mock: invite exists but user is not owner or admin
        mock_cursor.fetchone.side_effect = [
            {"id": "invite-123", "organization_id": "org-123", "status": "pending", "owner_user_id": "owner-789"},
            {"role": "sales_rep"}  # User is not admin
        ]
        
        result = TeamInvitationService.cancel_invitation("invite-123", "user-456")
        
        assert result["success"] is False
        assert "permission" in result["error"]
    
    @patch('app.services.team_invitation_service.get_db')
    def test_list_invitations(self, mock_get_db):
        """Test listing invitations for an organization."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        future_time = (datetime.utcnow() + timedelta(days=6)).isoformat()
        mock_cursor.fetchall.return_value = [
            {
                "id": "invite-1",
                "email": "user1@example.com",
                "role": "sales_rep",
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": future_time,
                "accepted_at": None,
                "invited_by_name": "Admin User"
            },
            {
                "id": "invite-2",
                "email": "user2@example.com",
                "role": "viewer",
                "status": "accepted",
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": future_time,
                "accepted_at": datetime.utcnow().isoformat(),
                "invited_by_name": "Admin User"
            }
        ]
        
        invitations = TeamInvitationService.list_invitations("org-123")
        
        assert len(invitations) == 2
        assert invitations[0]["email"] == "user1@example.com"
        assert invitations[0]["status"] == "pending"
        assert invitations[1]["status"] == "accepted"
    
    @patch('app.services.team_invitation_service.atomic')
    def test_cleanup_expired_invitations(self, mock_atomic):
        """Test cleaning up expired invitations."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_atomic.return_value.__enter__.return_value = mock_conn
        
        mock_cursor.rowcount = 5  # 5 invitations expired
        
        result = TeamInvitationService.cleanup_expired_invitations()
        
        assert result == 5
