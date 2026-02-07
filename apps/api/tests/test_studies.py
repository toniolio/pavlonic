"""API tests for the DB-backed study read endpoint."""

from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_get_study_returns_200(seeded_db) -> None:
    response = client.get("/v1/studies/0001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["study_id"] == "0001"
    assert payload["viewer_entitlement"] == "public"
    assert payload["citation"]["title"]
    assert payload["outcomes"]
    assert len(payload["results"]) == 1


def test_get_study_returns_404_for_unknown(seeded_db) -> None:
    response = client.get("/v1/studies/9999")

    assert response.status_code == 404


def test_get_study_filters_results_by_entitlement(seeded_db) -> None:
    public_response = client.get("/v1/studies/0001")
    paid_response = client.get(
        "/v1/studies/0001",
        headers={"X-Pavlonic-Entitlement": "paid"},
    )

    assert public_response.status_code == 200
    assert paid_response.status_code == 200
    public_results = public_response.json()["results"]
    paid_results = paid_response.json()["results"]
    assert len(public_results) < len(paid_results)
    assert {result["result_id"] for result in public_results} == {"R1"}
    assert {result["result_id"] for result in paid_results} == {"R1", "R2", "R3"}
