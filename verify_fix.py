import sys
import unittest
from unittest.mock import MagicMock, patch
# Mock imports to avoid needing actual DB or complex dependencies
sys.modules['app.database_sqlite'] = MagicMock()
sys.modules['app.auth'] = MagicMock()

# Now import services
from app.services.team_invitation_service import TeamInvitationService
from app.services.password_reset_service import PasswordResetService
from app.utils.transactions import TransactionOptions, IsolationLevel

class TestFixes(unittest.TestCase):
    @patch('app.services.team_invitation_service.transaction')
    @patch('app.services.team_invitation_service.get_db')
    def test_accept_invitation_transaction(self, mock_get_db, mock_transaction):
        print("Testing accept_invitation transaction usage...")
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        mock_transaction.return_value.__enter__.return_value = mock_conn

        # Setup validate to pass
        with patch.object(TeamInvitationService, 'validate_invitation') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "invite_id": "invite-123",
                "organization_id": "org-123",
                "org_name": "Test Org",
                "email": "invited@example.com",
                "role": "sales_rep"
            }
            mock_cursor.fetchone.return_value = None # No existing user

            TeamInvitationService.accept_invitation("token", "Name", "Pass1234")

            # Verify transaction called
            assert mock_transaction.called
            print("Transaction wrapper called successfully.")

    @patch('app.services.password_reset_service.transaction')
    @patch('app.services.password_reset_service.get_db') 
    def test_reset_password_transaction(self, mock_get_db, mock_transaction):
        print("Testing reset_password transaction usage...")
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        mock_transaction.return_value.__enter__.return_value = mock_conn

        with patch.object(PasswordResetService, 'validate_token') as mock_validate:
             with patch('app.auth._hash_password') as mock_hash:
                mock_validate.return_value = {"valid": True, "user_id": "u1", "email": "e@e.com"}
                mock_hash.return_value = "hash"
                
                PasswordResetService.reset_password("token", "Pass1234")
                
                assert mock_transaction.called
                print("Transaction wrapper called successfully.")

    @patch('app.services.team_invitation_service.atomic')
    @patch('app.services.team_invitation_service.get_db')
    def test_create_invitation_atomic(self, mock_get_db, mock_atomic):
        print("Testing create_invitation atomic usage...")
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        mock_atomic.return_value.__enter__.return_value = mock_conn
        
        # User not exists, seats OK, no existing, count OK
        mock_cursor.fetchone.side_effect = [
            None, 
            {"seats_total": 10, "seats_used": 0},
            None,
            {"count": 0},
            {"name": "Org"},
            {"name": "User"}
        ]

        TeamInvitationService.create_invitation("org", "email@e.com", "viewer", "u1")
        
        assert mock_atomic.called
        print("Atomic wrapper called successfully.")

if __name__ == '__main__':
    unittest.main()
