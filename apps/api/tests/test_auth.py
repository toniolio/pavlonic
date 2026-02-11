"""API tests for auth register/login/me flows."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from apps.api.auth import get_auth_settings, issue_access_token
from apps.api.main import app


client = TestClient(app)

LOGIN_FAILURE_DETAIL = {"detail": "Invalid email or password"}
UNAUTHORIZED_DETAIL = {"detail": "Invalid or expired token"}


def _register(email: str, password: str) -> dict:
    response = client.post("/v1/auth/register", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()


def _token_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_success(seeded_db) -> None:
    response = client.post(
        "/v1/auth/register",
        json={"email": "user@example.com", "password": "correct horse battery staple"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"access_token", "token_type", "expires_in"}
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] == 86400
    assert "password_hash" not in payload


def test_register_duplicate_email_rejected_case_insensitive(seeded_db) -> None:
    first_response = client.post(
        "/v1/auth/register",
        json={"email": "Foo@Bar.com", "password": "strong-password-1"},
    )
    second_response = client.post(
        "/v1/auth/register",
        json={"email": "foo@bar.com", "password": "strong-password-2"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409


def test_login_success_updates_last_login(seeded_db) -> None:
    _register("login-success@example.com", "swordfish")

    response = client.post(
        "/v1/auth/login",
        json={"email": "login-success@example.com", "password": "swordfish"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"access_token", "token_type", "expires_in"}
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] == 86400

    with sqlite3.connect(str(seeded_db)) as conn:
        row = conn.execute(
            "SELECT last_login_at FROM users WHERE email = ?",
            ("login-success@example.com",),
        ).fetchone()
    assert row is not None
    assert row[0] is not None


def test_login_wrong_password_returns_generic_failure(seeded_db) -> None:
    _register("wrong-password@example.com", "correct-password")

    response = client.post(
        "/v1/auth/login",
        json={"email": "wrong-password@example.com", "password": "not-correct"},
    )

    assert response.status_code == 401
    assert response.json() == LOGIN_FAILURE_DETAIL


def test_login_unknown_email_returns_same_generic_failure(seeded_db) -> None:
    response = client.post(
        "/v1/auth/login",
        json={"email": "does-not-exist@example.com", "password": "any-password"},
    )

    assert response.status_code == 401
    assert response.json() == LOGIN_FAILURE_DETAIL


def test_me_with_valid_token_returns_contract_fields(seeded_db) -> None:
    register_payload = _register("me-valid@example.com", "correct-password")
    token = register_payload["access_token"]

    response = client.get("/v1/auth/me", headers=_token_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {
        "user_id",
        "email",
        "plan_key",
        "entitlements",
        "expires_at",
    }
    assert payload["user_id"]
    assert payload["email"] == "me-valid@example.com"
    assert payload["plan_key"] == "free"
    assert payload["expires_at"] is None
    assert payload["entitlements"] == {
        "content_access_rules_version": 1,
        "is_paid": False,
        "features": [],
    }


def test_me_with_invalid_token_returns_401(seeded_db) -> None:
    response = client.get(
        "/v1/auth/me",
        headers=_token_headers("this-is-not-a-valid-token"),
    )

    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED_DETAIL


def test_me_with_token_for_missing_user_returns_401(seeded_db) -> None:
    settings = get_auth_settings()
    token = issue_access_token("missing-user-id", settings)

    response = client.get("/v1/auth/me", headers=_token_headers(token))

    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED_DETAIL


def test_me_with_expired_token_returns_401(seeded_db) -> None:
    _register("me-expired@example.com", "correct-password")

    settings = get_auth_settings()
    expired_token = issue_access_token(
        "any-user-id",
        settings,
        now=datetime.now(timezone.utc) - timedelta(seconds=settings.access_token_ttl_seconds + 1),
    )

    response = client.get("/v1/auth/me", headers=_token_headers(expired_token))

    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED_DETAIL
