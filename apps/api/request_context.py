"""Request context helpers for API endpoints.

How it works:
    - Resolve auth identity + plan from Authorization bearer token.

How to run:
    - Import resolve_request_auth_context inside a FastAPI handler.

Expected output:
    - Returns an authenticated or unauthenticated request auth context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fastapi import Request

from apps.api.auth import (
    TokenExpiredError,
    TokenValidationError,
    get_auth_settings,
    get_user_by_id,
    parse_bearer_token,
    verify_access_token,
)
AUTH_STATE_UNAUTHENTICATED = "unauthenticated"
AUTH_STATE_AUTHENTICATED = "authenticated"


@dataclass(frozen=True)
class RequestAuthContext:
    """Per-request identity + plan resolution result."""

    auth_state: Literal["unauthenticated", "authenticated"]
    user_id: str | None
    email: str | None
    plan_key: str | None

    @property
    def is_authenticated(self) -> bool:
        """Return True when context represents an authenticated user."""
        return self.auth_state == AUTH_STATE_AUTHENTICATED


class RequestAuthenticationError(ValueError):
    """Raised when an endpoint requires authentication but context is unauthenticated."""


def _unauthenticated_auth_context() -> RequestAuthContext:
    return RequestAuthContext(
        auth_state=AUTH_STATE_UNAUTHENTICATED,
        user_id=None,
        email=None,
        plan_key=None,
    )


def resolve_request_auth_context(request: Request) -> RequestAuthContext:
    """Resolve identity + plan for this request.

    Behavior is fail-closed: missing/invalid/expired tokens and missing users
    resolve to an unauthenticated context.
    """
    token = parse_bearer_token(request.headers.get("Authorization"))
    if token is None:
        return _unauthenticated_auth_context()

    settings = get_auth_settings()
    try:
        user_id = verify_access_token(token, settings)
    except (TokenExpiredError, TokenValidationError):
        return _unauthenticated_auth_context()

    user = get_user_by_id(user_id)
    if user is None:
        return _unauthenticated_auth_context()

    return RequestAuthContext(
        auth_state=AUTH_STATE_AUTHENTICATED,
        user_id=user.user_id,
        email=user.email,
        plan_key=user.plan_key,
    )


def require_authenticated_request_context(request: Request) -> RequestAuthContext:
    """Resolve auth context and require an authenticated user."""
    context = resolve_request_auth_context(request)
    if not context.is_authenticated:
        raise RequestAuthenticationError("Authenticated request required.")
    return context
