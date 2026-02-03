"""API tests for the demo study read endpoint."""

from dataclasses import replace

from fastapi.testclient import TestClient

from apps.api.main import app
from packages.core.loader import load_demo_study


client = TestClient(app)


def test_get_study_returns_200() -> None:
    response = client.get("/v1/studies/0001")

    assert response.status_code == 200
    assert response.json()["study_id"] == "0001"


def test_get_study_returns_404_for_unknown() -> None:
    response = client.get("/v1/studies/9999")

    assert response.status_code == 404


def test_get_study_filters_results_by_entitlement(monkeypatch) -> None:
    demo = load_demo_study("0001")

    def _public_loader(_: str):
        return replace(demo, viewer_entitlement="public")

    def _paid_loader(_: str):
        return replace(demo, viewer_entitlement="paid")

    monkeypatch.setattr("apps.api.main.load_demo_study", _public_loader)
    public_response = client.get("/v1/studies/0001")

    monkeypatch.setattr("apps.api.main.load_demo_study", _paid_loader)
    paid_response = client.get("/v1/studies/0001")

    assert public_response.status_code == 200
    assert paid_response.status_code == 200
    assert len(public_response.json()["results"]) < len(paid_response.json()["results"])
