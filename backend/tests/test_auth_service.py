"""
Unit tests for the AuthService (service layer, not API).

Tests password hashing, JWT creation/decoding, and user CRUD operations.
"""

import pytest
from datetime import timedelta
from fastapi import HTTPException

from app.services.auth_service import AuthService


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_password(self):
        """Password hash should not match the original."""
        hashed = AuthService.get_password_hash("MySecurePass123")
        assert hashed != "MySecurePass123"
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        hashed = AuthService.get_password_hash("MySecurePass123")
        assert AuthService.verify_password("MySecurePass123", hashed) is True

    def test_verify_password_incorrect(self):
        """Wrong password should fail verification."""
        hashed = AuthService.get_password_hash("MySecurePass123")
        assert AuthService.verify_password("WrongPassword", hashed) is False


class TestJWT:
    """Tests for JWT token creation and decoding."""

    def test_create_access_token(self):
        """Token should be a non-empty string."""
        token = AuthService.create_access_token(
            {"sub": "1", "email": "test@example.com"}
        )
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Decoding a valid token should return the original payload."""
        token = AuthService.create_access_token(
            {"sub": "42", "email": "test@example.com"}
        )
        payload = AuthService.decode_token(token)
        assert payload["sub"] == "42"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload  # expiry claim present

    def test_decode_invalid_token(self):
        """Decoding a garbage token should raise 401."""
        with pytest.raises(HTTPException) as exc_info:
            AuthService.decode_token("not-a-real-token")
        assert exc_info.value.status_code == 401

    def test_create_token_with_custom_expiry(self):
        """Token with custom expiry should decode correctly."""
        token = AuthService.create_access_token(
            {"sub": "1"},
            expires_delta=timedelta(hours=1),
        )
        payload = AuthService.decode_token(token)
        assert payload["sub"] == "1"


class TestUserCRUD:
    """Tests for user creation, lookup, and authentication at the service layer."""

    def test_create_user(self, db_session):
        """Create a user and verify fields."""
        from app.schemas.user import UserCreate

        user_data = UserCreate(
            email="new@example.com",
            username="newuser",
            full_name="New User",
            password="SecurePass123",
            confirm_password="SecurePass123",
        )
        user = AuthService.create_user(db_session, user_data)
        assert user.email == "new@example.com"
        assert user.username == "newuser"
        assert user.hashed_password != "SecurePass123"

    def test_create_duplicate_email(self, db_session, test_user):
        """Creating user with duplicate email raises 400."""
        from app.schemas.user import UserCreate

        with pytest.raises(HTTPException) as exc_info:
            AuthService.create_user(db_session, UserCreate(
                email="test@example.com",  # same as test_user
                username="different",
                full_name="Dup",
                password="SecurePass123",
                confirm_password="SecurePass123",
            ))
        assert exc_info.value.status_code == 400

    def test_authenticate_by_email(self, db_session, test_user):
        """Authenticate user using email."""
        user = AuthService.authenticate_user(
            db_session, "test@example.com", "TestPassword123"
        )
        assert user is not None
        assert user.id == test_user.id

    def test_authenticate_by_username(self, db_session, test_user):
        """Authenticate user using username."""
        user = AuthService.authenticate_user(
            db_session, "testuser", "TestPassword123"
        )
        assert user is not None
        assert user.id == test_user.id

    def test_authenticate_wrong_password(self, db_session, test_user):
        """Authentication fails with wrong password."""
        user = AuthService.authenticate_user(
            db_session, "test@example.com", "WrongPassword"
        )
        assert user is None

    def test_authenticate_nonexistent_user(self, db_session):
        """Authentication fails for non-existent user."""
        user = AuthService.authenticate_user(
            db_session, "noone@example.com", "SomePass"
        )
        assert user is None

    def test_get_user_by_id(self, db_session, test_user):
        """Look up user by ID."""
        user = AuthService.get_user_by_id(db_session, test_user.id)
        assert user is not None
        assert user.email == "test@example.com"

    def test_get_user_by_id_not_found(self, db_session):
        """Return None for non-existent user ID."""
        user = AuthService.get_user_by_id(db_session, 99999)
        assert user is None

    def test_change_password(self, db_session, test_user):
        """Successfully change password."""
        result = AuthService.change_password(
            db_session, test_user.id, "TestPassword123", "NewPass456"
        )
        assert result is True

        # Verify new password works
        user = AuthService.authenticate_user(
            db_session, "test@example.com", "NewPass456"
        )
        assert user is not None

    def test_change_password_wrong_current(self, db_session, test_user):
        """Reject password change with incorrect current password."""
        with pytest.raises(HTTPException) as exc_info:
            AuthService.change_password(
                db_session, test_user.id, "WrongCurrent", "NewPass456"
            )
        assert exc_info.value.status_code == 400

    def test_delete_user_soft(self, db_session, test_user):
        """Soft-delete sets user inactive."""
        AuthService.delete_user(db_session, test_user.id)
        user = AuthService.get_user_by_id(db_session, test_user.id)
        assert user.is_active is False
