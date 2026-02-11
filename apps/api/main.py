"""Minimal read-only API for DB-backed study and technique data.

How it works:
    - Exposes POST /v1/auth/register.
    - Exposes POST /v1/auth/login.
    - Exposes GET /v1/auth/me.
    - Exposes GET /v1/studies/{study_id}.
    - Exposes GET /v1/techniques/{technique_id_or_slug}.
    - Loads study data from the SQLite DB via SQLAlchemy.
    - Filters results server-side based on viewer entitlements.
    - Returns 404 when the study or technique is missing.

How to run:
    - uvicorn apps.api.main:app --reload

Expected output:
    - 200 JSON response for /v1/studies/0001.
    - 200 JSON response for /v1/techniques/spaced-practice.
    - 404 JSON response for unknown study or technique IDs.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from apps.api.auth import (
    AuthConfigError,
    DuplicateEmailError,
    authenticate_user,
    build_token_response,
    get_auth_settings,
    register_user,
)
from apps.api.request_context import (
    RequestAuthenticationError,
    get_viewer_entitlement,
    require_authenticated_request_context,
)
from apps.api.studies import load_study_payload
from apps.api.techniques import load_technique_payload

app = FastAPI(title="Pavlonic API", version="0.1.0")

AUTH_LOGIN_FAILURE_DETAIL = "Invalid email or password"
AUTH_UNAUTHORIZED_DETAIL = "Invalid or expired token"
AUTH_CONFIGURATION_DETAIL = "Auth is not configured."
AUTH_BEARER_HEADER = {"WWW-Authenticate": "Bearer"}


class AuthCredentialsRequest(BaseModel):
    """Request payload for auth credential endpoints."""

    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


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


@app.post("/v1/auth/register")
def register(credentials: AuthCredentialsRequest) -> dict:
    """Register a user and return a bearer access token."""
    try:
        settings = get_auth_settings()
        user = register_user(credentials.email, credentials.password, settings)
    except AuthConfigError as exc:
        raise HTTPException(status_code=500, detail=AUTH_CONFIGURATION_DETAIL) from exc
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=409, detail="Email already registered.") from exc

    return build_token_response(user.user_id, settings)


@app.post("/v1/auth/login")
def login(credentials: AuthCredentialsRequest) -> dict:
    """Authenticate a user and return a bearer access token."""
    try:
        settings = get_auth_settings()
    except AuthConfigError as exc:
        raise HTTPException(status_code=500, detail=AUTH_CONFIGURATION_DETAIL) from exc

    user = authenticate_user(credentials.email, credentials.password)
    if user is None:
        raise HTTPException(status_code=401, detail=AUTH_LOGIN_FAILURE_DETAIL)

    return build_token_response(user.user_id, settings)


@app.get("/v1/auth/me")
def get_me(request: Request) -> dict:
    """Return the authenticated user's identity and entitlements shape."""
    try:
        context = require_authenticated_request_context(request)
    except AuthConfigError as exc:
        raise HTTPException(status_code=500, detail=AUTH_CONFIGURATION_DETAIL) from exc
    except RequestAuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail=AUTH_UNAUTHORIZED_DETAIL,
            headers=AUTH_BEARER_HEADER,
        ) from exc

    return {
        "user_id": context.user_id,
        "email": context.email,
        "plan_key": context.plan_key,
        "entitlements": {
            "content_access_rules_version": 1,
            "is_paid": context.plan_key == "basic_paid",
            "features": [],
        },
        "expires_at": None,
    }


@app.get("/v1/studies/{study_id}")
def get_study(study_id: str, request: Request) -> dict:
    """Return the study payload by ID."""
    viewer_entitlement = get_viewer_entitlement(request)
    study = load_study_payload(study_id, viewer_entitlement)
    if study is None:
        raise HTTPException(status_code=404, detail="Study not found")

    return study


@app.get("/v1/techniques/{technique_id_or_slug}")
def get_technique(technique_id_or_slug: str, request: Request) -> dict:
    """Return the technique payload by ID or slug."""
    viewer_entitlement = get_viewer_entitlement(request)
    technique = load_technique_payload(technique_id_or_slug, viewer_entitlement)
    if technique is None:
        raise HTTPException(status_code=404, detail="Technique not found")

    return technique
