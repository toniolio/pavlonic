"""API tests for auth-backed technique read gating and anti-leak behavior."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from apps.api.auth import get_auth_settings, issue_access_token
from apps.api.main import app
from apps.api.tests.helpers import bearer_headers, login_user, register_user, set_user_plan_key


client = TestClient(app)


def _collect_rows(tables: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for table in tables:
        rows.extend(table.get("rows", []))
    return rows


def _collect_refs(tables: list[dict]) -> set[str]:
    refs: set[str] = set()
    for table in tables:
        for row in table.get("rows", []):
            for channel_name in ("performance", "learning"):
                channel = row.get(channel_name, {})
                for ref in channel.get("refs", []):
                    if ref:
                        refs.add(ref)
    return refs


def _find_overall_row(tables: list[dict]) -> dict | None:
    for row in _collect_rows(tables):
        row_id = str(row.get("row_id", "")).strip().lower()
        row_label = str(row.get("row_label", "")).strip().lower()
        if row_id == "overall" or row_label == "overall":
            return row
    return None


def _resolved_keys(payload: dict) -> set[str]:
    return set(payload["resolved_results"].keys())


def _mapping_result_ids(payload: dict) -> set[str]:
    return {entry["result_id"] for entry in payload["mapping_json"]}


def _has_vary_authorization(response) -> bool:
    vary = response.headers.get("Vary", "")
    return any(part.strip().lower() == "authorization" for part in vary.split(","))


def test_get_technique_returns_200_preview_for_unauthenticated(seeded_db) -> None:
    response = client.get("/v1/techniques/spaced-practice")

    assert response.status_code == 200
    payload = response.json()
    assert payload["technique_id"] == "spaced-practice"
    assert payload["viewer_entitlement"] == "public"
    assert payload["title"]
    assert payload["summary"]
    assert payload["tables"]
    assert len(_collect_rows(payload["tables"])) == 1
    assert _find_overall_row(payload["tables"]) is not None

    # Preview must not leak expanded references/results.
    assert _mapping_result_ids(payload) == {"R1"}
    assert _collect_refs(payload["tables"]) == {"0001:R1"}
    assert _resolved_keys(payload) == {"0001:R1"}
    assert response.headers.get("Cache-Control") != "no-store"
    assert _has_vary_authorization(response) is False


def test_get_technique_returns_404_for_unknown(seeded_db) -> None:
    response = client.get("/v1/techniques/missing-technique")

    assert response.status_code == 404


def test_get_technique_unauthenticated_free_and_paid_matrix(seeded_db) -> None:
    register_user(
        client,
        email="technique-free@example.com",
        password="correct-password",
    )
    free_login = login_user(
        client,
        email="technique-free@example.com",
        password="correct-password",
    )

    register_user(
        client,
        email="technique-paid@example.com",
        password="correct-password",
    )
    set_user_plan_key(
        seeded_db,
        email="technique-paid@example.com",
        plan_key="basic_paid",
    )
    paid_login = login_user(
        client,
        email="technique-paid@example.com",
        password="correct-password",
    )

    unauth_response = client.get("/v1/techniques/spaced-practice")
    free_response = client.get(
        "/v1/techniques/spaced-practice",
        headers=bearer_headers(free_login["access_token"]),
    )
    paid_response = client.get(
        "/v1/techniques/spaced-practice",
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

    assert len(_collect_rows(unauth_payload["tables"])) == 1
    assert len(_collect_rows(free_payload["tables"])) == 1
    assert len(_collect_rows(paid_payload["tables"])) > 1

    assert _mapping_result_ids(unauth_payload) == {"R1"}
    assert _mapping_result_ids(free_payload) == {"R1"}
    assert _mapping_result_ids(paid_payload) == {"R1", "R2", "R3"}

    assert _collect_refs(unauth_payload["tables"]) == {"0001:R1"}
    assert _collect_refs(free_payload["tables"]) == {"0001:R1"}
    assert _collect_refs(paid_payload["tables"]) == {"0001:R1", "0001:R2", "0001:R3"}

    assert _resolved_keys(unauth_payload) == {"0001:R1"}
    assert _resolved_keys(free_payload) == {"0001:R1"}
    assert _resolved_keys(paid_payload) == {"0001:R1", "0001:R2", "0001:R3"}

    assert free_response.headers.get("Cache-Control") == "no-store"
    assert paid_response.headers.get("Cache-Control") == "no-store"
    assert _has_vary_authorization(free_response) is True
    assert _has_vary_authorization(paid_response) is True


def test_get_technique_dev_entitlement_header_does_not_elevate(seeded_db) -> None:
    response = client.get(
        "/v1/techniques/spaced-practice",
        headers={"X-Pavlonic-Entitlement": "paid"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["viewer_entitlement"] == "public"
    assert len(_collect_rows(payload["tables"])) == 1
    assert _mapping_result_ids(payload) == {"R1"}
    assert _collect_refs(payload["tables"]) == {"0001:R1"}
    assert _resolved_keys(payload) == {"0001:R1"}


def test_get_technique_invalid_and_expired_tokens_fall_back_to_preview(seeded_db) -> None:
    invalid_response = client.get(
        "/v1/techniques/spaced-practice",
        headers={"Authorization": "Bearer this-is-not-a-valid-token"},
    )

    settings = get_auth_settings()
    expired_token = issue_access_token(
        "any-user-id",
        settings,
        now=datetime.now(timezone.utc) - timedelta(seconds=settings.access_token_ttl_seconds + 1),
    )
    expired_response = client.get(
        "/v1/techniques/spaced-practice",
        headers=bearer_headers(expired_token),
    )

    assert invalid_response.status_code == 200
    assert expired_response.status_code == 200

    invalid_payload = invalid_response.json()
    expired_payload = expired_response.json()
    assert invalid_payload["viewer_entitlement"] == "public"
    assert expired_payload["viewer_entitlement"] == "public"
    assert len(_collect_rows(invalid_payload["tables"])) == 1
    assert len(_collect_rows(expired_payload["tables"])) == 1
    assert _mapping_result_ids(invalid_payload) == {"R1"}
    assert _mapping_result_ids(expired_payload) == {"R1"}
    assert _collect_refs(invalid_payload["tables"]) == {"0001:R1"}
    assert _collect_refs(expired_payload["tables"]) == {"0001:R1"}
    assert _resolved_keys(invalid_payload) == {"0001:R1"}
    assert _resolved_keys(expired_payload) == {"0001:R1"}
    assert invalid_response.headers.get("Cache-Control") != "no-store"
    assert expired_response.headers.get("Cache-Control") != "no-store"
