"""API tests for the demo study read endpoint."""

from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_get_study_returns_200() -> None:
    response = client.get("/v1/studies/0001")

    assert response.status_code == 200
    assert response.json()["study_id"] == "0001"


def test_get_study_returns_404_for_unknown() -> None:
    response = client.get("/v1/studies/9999")

    assert response.status_code == 404
