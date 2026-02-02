"""Minimal read-only API for demo study data.

How it works:
    - Exposes GET /v1/studies/{study_id}.
    - Loads demo JSON via packages.core.loader.load_demo_study.
    - Returns 404 when the demo file for the requested ID is missing.

How to run:
    - uvicorn apps.api.main:app --reload

Expected output:
    - 200 JSON response for /v1/studies/0001.
    - 404 JSON response for unknown study IDs.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from packages.core.loader import load_demo_study

app = FastAPI(title="Pavlonic API", version="0.1.0")


@app.get("/v1/studies/{study_id}")
def get_study(study_id: str) -> dict:
    """Return the demo Study payload by ID."""
    try:
        study = load_demo_study(study_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Study not found") from exc

    return study.to_dict()
