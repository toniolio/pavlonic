"""Minimal read-only API for DB-backed study data.

How it works:
    - Exposes GET /v1/studies/{study_id}.
    - Loads study data from the SQLite DB via SQLAlchemy.
    - Filters results server-side based on viewer entitlements.
    - Returns 404 when the study ID is missing.

How to run:
    - uvicorn apps.api.main:app --reload

Expected output:
    - 200 JSON response for /v1/studies/0001.
    - 404 JSON response for unknown study IDs.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from apps.api.request_context import get_viewer_entitlement
from apps.api.studies import load_study_payload

app = FastAPI(title="Pavlonic API", version="0.1.0")

# Local dev-only CORS for the static web viewer.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8001",
        "http://localhost:8001",
        "http://127.0.0.1:8000",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/v1/studies/{study_id}")
def get_study(study_id: str, request: Request) -> dict:
    """Return the study payload by ID."""
    viewer_entitlement = get_viewer_entitlement(request)
    study = load_study_payload(study_id, viewer_entitlement)
    if study is None:
        raise HTTPException(status_code=404, detail="Study not found")

    return study
