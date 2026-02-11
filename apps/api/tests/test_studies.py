"""API tests for auth-backed study read gating and anti-leak behavior."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from apps.api.auth import get_auth_settings, issue_access_token
from apps.api.main import app
from apps.api.tests.helpers import bearer_headers, login_user, register_user, set_user_plan_key


client = TestClient(app)


def _result_ids(payload: dict) -> set[str]:
    return {item["result_id"] for item in payload["results"]}


def _has_vary_authorization(response) -> bool:
    vary = response.headers.get("Vary", "")
    return any(part.strip().lower() == "authorization" for part in vary.split(","))


def test_get_study_returns_200_preview_for_unauthenticated(seeded_db) -> None:
    response = client.get("/v1/studies/0001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["study_id"] == "0001"
    assert payload["viewer_entitlement"] == "public"
    assert payload["citation"]["title"]
    assert payload["outcomes"]
    assert _result_ids(payload) == {"R1"}
    assert response.headers.get("Cache-Control") != "no-store"
    assert _has_vary_authorization(response) is False


def test_get_study_returns_404_for_unknown(seeded_db) -> None:
    response = client.get("/v1/studies/9999")

    assert response.status_code == 404


def test_get_study_unauthenticated_free_and_paid_matrix(seeded_db) -> None:
    register_user(
        client,
        email="study-free@example.com",
        password="correct-password",
    )
    free_login = login_user(
        client,
        email="study-free@example.com",
        password="correct-password",
    )

    register_user(
        client,
        email="study-paid@example.com",
        password="correct-password",
    )
    set_user_plan_key(
        seeded_db,
        email="study-paid@example.com",
        plan_key="basic_paid",
    )
    paid_login = login_user(
        client,
        email="study-paid@example.com",
        password="correct-password",
    )

    unauth_response = client.get("/v1/studies/0001")
    free_response = client.get(
        "/v1/studies/0001",
        headers=bearer_headers(free_login["access_token"]),
    )
    paid_response = client.get(
        "/v1/studies/0001",
        headers=bearer_headers(paid_login["access_token"]),
    )

    assert unauth_response.status_code == 200
    assert free_response.status_code == 200
    assert paid_response.status_code == 200

    unauth_payload = unauth_response.json()
    free_payload = free_response.json()
    paid_payload = paid_response.json()

    assert unauth_payload["viewer_entitlement"] == "public"
    assert free_payload["viewer_entitlement"] == "public"
    assert paid_payload["viewer_entitlement"] == "paid"

    assert _result_ids(unauth_payload) == {"R1"}
    assert _result_ids(free_payload) == {"R1"}
    assert _result_ids(paid_payload) == {"R1", "R2", "R3"}

    assert free_response.headers.get("Cache-Control") == "no-store"
    assert paid_response.headers.get("Cache-Control") == "no-store"
    assert _has_vary_authorization(free_response) is True
    assert _has_vary_authorization(paid_response) is True


def test_get_study_dev_entitlement_header_does_not_elevate(seeded_db) -> None:
    response = client.get(
        "/v1/studies/0001",
        headers={"X-Pavlonic-Entitlement": "paid"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["viewer_entitlement"] == "public"
    assert _result_ids(payload) == {"R1"}


def test_get_study_invalid_and_expired_tokens_fall_back_to_preview(seeded_db) -> None:
    invalid_response = client.get(
        "/v1/studies/0001",
        headers={"Authorization": "Bearer this-is-not-a-valid-token"},
    )

    settings = get_auth_settings()
    expired_token = issue_access_token(
        "any-user-id",
        settings,
        now=datetime.now(timezone.utc) - timedelta(seconds=settings.access_token_ttl_seconds + 1),
    )
    expired_response = client.get(
        "/v1/studies/0001",
        headers=bearer_headers(expired_token),
    )

    assert invalid_response.status_code == 200
    assert expired_response.status_code == 200
    assert _result_ids(invalid_response.json()) == {"R1"}
    assert _result_ids(expired_response.json()) == {"R1"}
    assert invalid_response.json()["viewer_entitlement"] == "public"
    assert expired_response.json()["viewer_entitlement"] == "public"
    assert invalid_response.headers.get("Cache-Control") != "no-store"
    assert expired_response.headers.get("Cache-Control") != "no-store"
