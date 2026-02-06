"""API tests for the DB-backed technique read endpoint."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def _result_ids(payload: dict) -> set[str]:
    return {item["result"]["result_id"] for item in payload["results"]}


def _mapping_ids(payload: dict) -> set[tuple[str, str]]:
    return {
        (item["study_id"], item["result_id"])
        for item in payload["mapping_json"]
    }


def _update_mapping(db_path: Path, mapping: list[dict[str, str]]) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            "UPDATE techniques SET mapping_json = ? WHERE technique_id = ?",
            (json.dumps(mapping), "spaced-practice"),
        )
        conn.commit()


def test_get_technique_returns_200(seeded_db) -> None:
    response = client.get("/v1/techniques/spaced-practice")

    assert response.status_code == 200
    payload = response.json()
    assert payload["technique_id"] == "spaced-practice"
    assert payload["viewer_entitlement"] == "public"
    assert payload["title"]
    assert payload["summary"]
    assert payload["mapping_json"]
    assert payload["results"]


def test_get_technique_returns_404_for_unknown(seeded_db) -> None:
    response = client.get("/v1/techniques/missing-technique")

    assert response.status_code == 404


def test_get_technique_filters_results_by_entitlement(seeded_db) -> None:
    mapping = [
        {"study_id": "0001", "result_id": "R1"},
        {"study_id": "0001", "result_id": "R2"},
    ]
    _update_mapping(seeded_db, mapping)

    public_response = client.get("/v1/techniques/spaced-practice")
    paid_response = client.get(
        "/v1/techniques/spaced-practice",
        headers={"X-Pavlonic-Entitlement": "paid"},
    )

    assert public_response.status_code == 200
    assert paid_response.status_code == 200

    public_payload = public_response.json()
    paid_payload = paid_response.json()

    assert len(public_payload["results"]) < len(paid_payload["results"])
    assert _result_ids(public_payload) == {"R1"}
    assert _result_ids(paid_payload) == {"R1", "R2"}

    assert _mapping_ids(public_payload) == {("0001", "R1")}
    assert _mapping_ids(paid_payload) == {("0001", "R1"), ("0001", "R2")}
