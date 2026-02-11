"""Tests for request auth context identity + plan resolution."""

from __future__ import annotations

from fastapi import Request

from apps.api.auth import get_auth_settings, issue_access_token, register_user
from apps.api.request_context import (
    AUTH_STATE_AUTHENTICATED,
    AUTH_STATE_UNAUTHENTICATED,
    resolve_request_auth_context,
)


def _request_with_headers(headers: dict[str, str] | None = None) -> Request:
    raw_headers = []
    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))
    return Request({"type": "http", "headers": raw_headers})


def test_resolve_request_auth_context_without_authorization_header_is_unauthenticated(
    seeded_db,
) -> None:
    context = resolve_request_auth_context(_request_with_headers())

    assert context.auth_state == AUTH_STATE_UNAUTHENTICATED
    assert context.user_id is None
    assert context.email is None
    assert context.plan_key is None
    assert context.is_authenticated is False


def test_resolve_request_auth_context_with_valid_free_user_token(seeded_db) -> None:
    settings = get_auth_settings()
    user = register_user("request-context-free@example.com", "correct-password", settings)
    token = issue_access_token(user.user_id, settings)

    context = resolve_request_auth_context(
        _request_with_headers({"Authorization": f"Bearer {token}"})
    )

    assert context.auth_state == AUTH_STATE_AUTHENTICATED
    assert context.user_id == user.user_id
    assert context.email == "request-context-free@example.com"
    assert context.plan_key == "free"
    assert context.is_authenticated is True


def test_resolve_request_auth_context_with_invalid_token_is_unauthenticated(seeded_db) -> None:
    context = resolve_request_auth_context(
        _request_with_headers({"Authorization": "Bearer this-is-not-a-valid-token"})
    )

    assert context.auth_state == AUTH_STATE_UNAUTHENTICATED
    assert context.user_id is None
    assert context.email is None
    assert context.plan_key is None


def test_resolve_request_auth_context_with_missing_user_token_is_unauthenticated(seeded_db) -> None:
    settings = get_auth_settings()
    token = issue_access_token("missing-user-id", settings)

    context = resolve_request_auth_context(
        _request_with_headers({"Authorization": f"Bearer {token}"})
    )

    assert context.auth_state == AUTH_STATE_UNAUTHENTICATED
    assert context.user_id is None
    assert context.email is None
    assert context.plan_key is None


def test_resolve_request_auth_context_ignores_dev_entitlement_header(seeded_db) -> None:
    context = resolve_request_auth_context(
        _request_with_headers({"X-Pavlonic-Entitlement": "paid"})
    )

    assert context.auth_state == AUTH_STATE_UNAUTHENTICATED
    assert context.user_id is None
    assert context.email is None
    assert context.plan_key is None


def test_resolve_request_auth_context_ignores_dev_header_with_valid_token(seeded_db) -> None:
    settings = get_auth_settings()
    user = register_user("request-context-header@example.com", "correct-password", settings)
    token = issue_access_token(user.user_id, settings)

    context = resolve_request_auth_context(
        _request_with_headers(
            {
                "Authorization": f"Bearer {token}",
                "X-Pavlonic-Entitlement": "paid",
            }
        )
    )

    assert context.auth_state == AUTH_STATE_AUTHENTICATED
    assert context.user_id == user.user_id
    assert context.email == "request-context-header@example.com"
    assert context.plan_key == "free"
