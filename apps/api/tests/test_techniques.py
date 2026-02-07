"""API tests for the DB-backed technique read endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app


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


def test_get_technique_returns_200(seeded_db) -> None:
    response = client.get("/v1/techniques/spaced-practice")

    assert response.status_code == 200
    payload = response.json()
    assert payload["technique_id"] == "spaced-practice"
    assert payload["viewer_entitlement"] == "public"
    assert payload["title"]
    assert payload["summary"]
    assert payload["mapping_json"]
    assert payload["tables"]

    overall_row = _find_overall_row(payload["tables"])
    assert overall_row is not None
    assert "performance" in overall_row
    assert "learning" in overall_row
    assert "refs" in overall_row["performance"]
    assert "refs" in overall_row["learning"]

    refs = _collect_refs(payload["tables"])
    assert refs
    assert _resolved_keys(payload) == refs
    for entry in payload["resolved_results"].values():
        assert entry["study_id"]
        assert entry["result_id"]


def test_get_technique_returns_404_for_unknown(seeded_db) -> None:
    response = client.get("/v1/techniques/missing-technique")

    assert response.status_code == 404


def test_get_technique_filters_rows_and_refs_by_entitlement(seeded_db) -> None:
    public_response = client.get("/v1/techniques/spaced-practice")
    paid_response = client.get(
        "/v1/techniques/spaced-practice",
        headers={"X-Pavlonic-Entitlement": "paid"},
    )

    assert public_response.status_code == 200
    assert paid_response.status_code == 200

    public_payload = public_response.json()
    paid_payload = paid_response.json()

    public_rows = _collect_rows(public_payload["tables"])
    paid_rows = _collect_rows(paid_payload["tables"])

    assert len(public_rows) < len(paid_rows)
    assert len(public_rows) == 1
    assert _find_overall_row(public_payload["tables"]) is not None

    public_refs = _collect_refs(public_payload["tables"])
    paid_refs = _collect_refs(paid_payload["tables"])

    assert public_refs < paid_refs
    assert _resolved_keys(public_payload) == public_refs
    assert _resolved_keys(paid_payload) == paid_refs
