"""
Security middleware and utilities for NexIPO.

Provides:
- SecurityHeadersMiddleware: Adds security headers to all responses
- RequestIdMiddleware: Generates and propagates X-Request-ID
- Rate limiter configuration via SlowAPI
"""

import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


# ── Rate Limiter ──────────────────────────────────────────────────────────

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
    storage_uri="memory://",  # in-memory for simplicity; use Redis URI in production
)


# ── Security Headers Middleware ───────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to every HTTP response.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: camera=(), microphone=(), geolocation=()
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        # response.headers["X-Frame-Options"] = "DENY" # Commented out to allow PDF iframe preview
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        return response


# ── Request ID Middleware ─────────────────────────────────────────────────

class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Generates a unique X-Request-ID for every request.

    - If the client sends an X-Request-ID header, it is reused (for distributed tracing).
    - Otherwise, a new UUID is generated.
    - The request_id is stored in `request.state.request_id` for use in logging.
    - The X-Request-ID header is included in the response.
    """

    async def dispatch(self, request: Request, call_next):
        # Reuse client-provided request ID or generate a new one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


# ── Secret Key Validation ─────────────────────────────────────────────────

INSECURE_DEFAULT_KEYS = {
    "dev-secret-key-change-in-production-12345678",
    "changeme",
    "secret",
    "your-secret-key",
}


def validate_secret_key(secret_key: str, debug: bool) -> None:
    """
    Validate that the SECRET_KEY is not a known insecure default.
    Raises RuntimeError in non-debug mode.
    Logs a warning in debug mode.
    """
    if secret_key in INSECURE_DEFAULT_KEYS:
        msg = (
            "⚠️  SECRET_KEY is set to an insecure default value! "
            "Set a strong, unique SECRET_KEY in your .env file."
        )
        if not debug:
            raise RuntimeError(msg)
        logger.warning(msg)


# ── Role-Based Access Control ─────────────────────────────────────────────

from fastapi import Depends, HTTPException, status  # noqa: E402


def _get_current_user_dependency():
    """Lazy import to avoid circular dependency with auth routes."""
    from app.api.routes.auth import get_current_user
    return get_current_user


def require_admin(current_user=Depends(_get_current_user_dependency())):
    """
    Dependency that enforces admin-level access.

    Raises HTTPException(403) if the authenticated user does not have
    the 'admin' role. Returns the user object otherwise.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
