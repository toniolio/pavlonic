"""Shared test helpers for auth-backed API integration tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient


def bearer_headers(access_token: str) -> dict[str, str]:
    """Build Authorization headers for a bearer token."""
    return {"Authorization": f"Bearer {access_token}"}


def register_user(client: TestClient, *, email: str, password: str) -> dict:
    """Register a user and return the token payload."""
    response = client.post("/v1/auth/register", json={"email": email, "password": password})
    assert response.status_code == 200
    payload = response.json()
    assert "access_token" in payload
    return payload


def login_user(client: TestClient, *, email: str, password: str) -> dict:
    """Log in a user and return the token payload."""
    response = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    payload = response.json()
    assert "access_token" in payload
    return payload


def set_user_plan_key(db_path: Path, *, email: str, plan_key: str) -> None:
    """Update a user's plan_key directly in sqlite for integration tests."""
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.execute(
            "UPDATE users SET plan_key = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
            (plan_key, email.lower()),
        )
        conn.commit()
    assert cursor.rowcount == 1

