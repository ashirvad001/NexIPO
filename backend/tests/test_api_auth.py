"""
Tests for Auth API endpoints (/api/v1/auth/*).

Covers:
- User registration (signup)
- Login (form-based and JSON)
- Profile retrieval and update
- Password change
- Logout and account deletion
"""

import pytest


class TestSignup:
    """Tests for POST /api/v1/auth/signup"""

    def test_signup_success(self, client):
        """Register a new user and verify JWT is returned."""
        response = client.post("/api/v1/auth/signup", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "SecurePass123",
            "confirm_password": "SecurePass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["username"] == "newuser"

    def test_signup_duplicate_email(self, client, test_user):
        """Reject signup when email is already registered."""
        response = client.post("/api/v1/auth/signup", json={
            "email": "test@example.com",  # same as test_user
            "username": "different",
            "full_name": "Dup",
            "password": "SecurePass123",
            "confirm_password": "SecurePass123",
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_signup_duplicate_username(self, client, test_user):
        """Reject signup when username is already taken."""
        response = client.post("/api/v1/auth/signup", json={
            "email": "another@example.com",
            "username": "testuser",  # same as test_user
            "full_name": "Dup",
            "password": "SecurePass123",
            "confirm_password": "SecurePass123",
        })
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"].lower()

    def test_signup_password_mismatch(self, client):
        """Reject signup when passwords don't match."""
        response = client.post("/api/v1/auth/signup", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "SecurePass123",
            "confirm_password": "WrongPass456",
        })
        assert response.status_code == 422  # Pydantic validation error

    def test_signup_short_password(self, client):
        """Reject signup when password is too short."""
        response = client.post("/api/v1/auth/signup", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "short",
            "confirm_password": "short",
        })
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login and /api/v1/auth/login/json"""

    def test_login_form_success(self, client, test_user):
        """Login with form data (OAuth2PasswordRequestForm)."""
        response = client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "TestPassword123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_json_success(self, client, test_user):
        """Login with JSON payload."""
        response = client.post("/api/v1/auth/login/json", json={
            "identifier": "test@example.com",
            "password": "TestPassword123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_by_username(self, client, test_user):
        """Login using username instead of email."""
        response = client.post("/api/v1/auth/login", data={
            "username": "testuser",
            "password": "TestPassword123",
        })
        assert response.status_code == 200

    def test_login_invalid_password(self, client, test_user):
        """Reject login with wrong password."""
        response = client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "WrongPassword",
        })
        assert response.status_code == 400

    def test_login_nonexistent_user(self, client):
        """Reject login for user that doesn't exist."""
        response = client.post("/api/v1/auth/login", data={
            "username": "noexist@example.com",
            "password": "SomePass123",
        })
        assert response.status_code == 400


class TestCurrentUser:
    """Tests for GET/PUT /api/v1/auth/me"""

    def test_get_current_user(self, client, auth_headers):
        """Retrieve current user profile with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"

    def test_get_current_user_no_token(self, client):
        """401 when no token is provided."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """401 when token is malformed."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert response.status_code == 401

    def test_update_profile(self, client, auth_headers):
        """Update user profile fields."""
        response = client.put("/api/v1/auth/me", json={
            "full_name": "Updated Name",
            "bio": "I love IPOs",
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"


class TestPasswordChange:
    """Tests for POST /api/v1/auth/change-password"""

    def test_change_password_success(self, client, auth_headers):
        """Successfully change password with correct current password."""
        response = client.post("/api/v1/auth/change-password", json={
            "current_password": "TestPassword123",
            "new_password": "NewSecurePass456",
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_change_password_wrong_current(self, client, auth_headers):
        """Reject password change with wrong current password."""
        response = client.post("/api/v1/auth/change-password", json={
            "current_password": "WrongPassword",
            "new_password": "NewSecurePass456",
        }, headers=auth_headers)
        assert response.status_code == 400


class TestLogoutAndDelete:
    """Tests for POST /api/v1/auth/logout and DELETE /api/v1/auth/me"""

    def test_logout(self, client, auth_headers):
        """Logout returns success (JWT is stateless, client discards token)."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200

    def test_delete_account(self, client, auth_headers):
        """Soft-delete account (set inactive)."""
        response = client.delete("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert "deactivated" in response.json()["detail"].lower()
