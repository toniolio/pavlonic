"""Auth service helpers for register/login/me flows.

How it works:
    - Reads auth settings from environment variables.
    - Normalizes emails for case-insensitive uniqueness at rest.
    - Hashes passwords with bcrypt and verifies credentials.
    - Issues and verifies JWT access tokens with identity-only claims.
    - Provides DB-backed helpers to register and authenticate users.

How to run:
    - python -c "from apps.api.auth import normalize_email; print(normalize_email('Foo@Bar.com'))"

Expected output:
    - Prints the normalized email value (e.g., foo@bar.com).
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.db import get_db_url
from apps.api.db_models import User


JWT_SECRET_ENV = "PAVLONIC_AUTH_JWT_SECRET"
JWT_ALGORITHM_ENV = "PAVLONIC_AUTH_JWT_ALGORITHM"
ACCESS_TOKEN_TTL_ENV = "PAVLONIC_AUTH_ACCESS_TOKEN_TTL_SECONDS"
BCRYPT_ROUNDS_ENV = "PAVLONIC_AUTH_BCRYPT_ROUNDS"

DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_TTL_SECONDS = 86400
DEFAULT_BCRYPT_ROUNDS = 12

DEFAULT_TOKEN_TYPE = "bearer"
DEFAULT_PLAN_KEY = "free"
DEFAULT_STATUS = "active"
JWT_TYPE = "JWT"

JWT_HMAC_ALGORITHMS: dict[str, Any] = {
    "HS256": hashlib.sha256,
    "HS384": hashlib.sha384,
    "HS512": hashlib.sha512,
}


class AuthConfigError(ValueError):
    """Raised when auth configuration is missing or invalid."""


class TokenExpiredError(ValueError):
    """Raised when a JWT has expired."""


class TokenValidationError(ValueError):
    """Raised when a JWT is invalid."""


class DuplicateEmailError(ValueError):
    """Raised when attempting to register an existing normalized email."""


@dataclass(frozen=True)
class AuthSettings:
    """Runtime auth settings loaded from environment variables."""

    jwt_secret: str
    jwt_algorithm: str
    access_token_ttl_seconds: int
    bcrypt_rounds: int


@dataclass(frozen=True)
class AuthUser:
    """Public auth user shape used across auth endpoints."""

    user_id: str
    email: str
    plan_key: str


def _parse_positive_int(raw_value: str | None, *, default: int, env_name: str) -> int:
    """Parse an integer environment value and enforce positive bounds."""
    if raw_value is None or not raw_value.strip():
        return default
    try:
        parsed = int(raw_value.strip())
    except ValueError as exc:
        raise AuthConfigError(f"{env_name} must be an integer.") from exc
    if parsed <= 0:
        raise AuthConfigError(f"{env_name} must be > 0.")
    return parsed


def get_auth_settings(env: Mapping[str, str] = os.environ) -> AuthSettings:
    """Load auth settings from environment variables."""
    jwt_secret = env.get(JWT_SECRET_ENV, "").strip()
    if not jwt_secret:
        raise AuthConfigError(f"{JWT_SECRET_ENV} must be set.")

    jwt_algorithm = env.get(JWT_ALGORITHM_ENV, "").strip() or DEFAULT_JWT_ALGORITHM
    if jwt_algorithm not in JWT_HMAC_ALGORITHMS:
        supported = ", ".join(sorted(JWT_HMAC_ALGORITHMS.keys()))
        raise AuthConfigError(f"{JWT_ALGORITHM_ENV} must be one of: {supported}.")

    access_token_ttl_seconds = _parse_positive_int(
        env.get(ACCESS_TOKEN_TTL_ENV),
        default=DEFAULT_ACCESS_TOKEN_TTL_SECONDS,
        env_name=ACCESS_TOKEN_TTL_ENV,
    )
    bcrypt_rounds = _parse_positive_int(
        env.get(BCRYPT_ROUNDS_ENV),
        default=DEFAULT_BCRYPT_ROUNDS,
        env_name=BCRYPT_ROUNDS_ENV,
    )

    return AuthSettings(
        jwt_secret=jwt_secret,
        jwt_algorithm=jwt_algorithm,
        access_token_ttl_seconds=access_token_ttl_seconds,
        bcrypt_rounds=bcrypt_rounds,
    )


def normalize_email(email: str) -> str:
    """Normalize email for case-insensitive identity matching."""
    return email.strip().lower()


def hash_password(password: str, bcrypt_rounds: int) -> str:
    """Hash a plaintext password with bcrypt."""
    if bcrypt_rounds < 4 or bcrypt_rounds > 17:
        raise AuthConfigError(f"{BCRYPT_ROUNDS_ENV} must be between 4 and 17.")

    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=bcrypt_rounds),
    )
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Return True when the plaintext password matches the hash."""
    if not password_hash.strip():
        return False

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.strip().encode("utf-8"),
        )
    except ValueError:
        return False


def _json_encode(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _jwt_sign(signing_input: bytes, settings: AuthSettings) -> bytes:
    digest = JWT_HMAC_ALGORITHMS[settings.jwt_algorithm]
    return hmac.new(settings.jwt_secret.encode("utf-8"), signing_input, digest).digest()


def issue_access_token(user_id: str, settings: AuthSettings, now: datetime | None = None) -> str:
    """Issue a JWT access token containing only identity claims."""
    issued_at = now or datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(seconds=settings.access_token_ttl_seconds)

    header = {
        "alg": settings.jwt_algorithm,
        "typ": JWT_TYPE,
    }
    payload: dict[str, Any] = {
        "sub": user_id,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    header_segment = _base64url_encode(_json_encode(header))
    payload_segment = _base64url_encode(_json_encode(payload))
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    signature_segment = _base64url_encode(_jwt_sign(signing_input, settings))
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def verify_access_token(access_token: str, settings: AuthSettings) -> str:
    """Verify and decode a JWT access token, returning user_id from sub."""
    try:
        header_segment, payload_segment, signature_segment = access_token.split(".")
    except ValueError as exc:
        raise TokenValidationError("Access token invalid.") from exc

    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    expected_signature = _jwt_sign(signing_input, settings)
    try:
        actual_signature = _base64url_decode(signature_segment)
    except (ValueError, binascii.Error) as exc:
        raise TokenValidationError("Access token invalid.") from exc
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise TokenValidationError("Access token invalid.")

    try:
        header = json.loads(_base64url_decode(header_segment).decode("utf-8"))
        payload = json.loads(_base64url_decode(payload_segment).decode("utf-8"))
    except (UnicodeDecodeError, ValueError, binascii.Error) as exc:
        raise TokenValidationError("Access token invalid.") from exc

    if not isinstance(header, dict) or not isinstance(payload, dict):
        raise TokenValidationError("Access token invalid.")
    if header.get("alg") != settings.jwt_algorithm:
        raise TokenValidationError("Access token invalid.")
    if header.get("typ") != JWT_TYPE:
        raise TokenValidationError("Access token invalid.")

    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise TokenValidationError("Access token invalid.")
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if now_ts >= exp:
        raise TokenExpiredError("Access token expired.")

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise TokenValidationError("Access token subject missing.")
    return user_id


def _engine():
    return create_engine(get_db_url(), future=True)


def _utcnow_naive() -> datetime:
    """Return UTC now as a naive datetime for sqlite DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _to_auth_user(user: User) -> AuthUser:
    return AuthUser(
        user_id=str(user.user_id),
        email=str(user.email),
        plan_key=str(user.plan_key),
    )


def register_user(email: str, password: str, settings: AuthSettings) -> AuthUser:
    """Create a user account and return the stored auth-safe user shape."""
    normalized_email = normalize_email(email)
    now = _utcnow_naive()
    user = User(
        user_id=str(uuid.uuid4()),
        email=normalized_email,
        password_hash=hash_password(password, settings.bcrypt_rounds),
        plan_key=DEFAULT_PLAN_KEY,
        status=DEFAULT_STATUS,
        created_at=now,
        updated_at=now,
    )

    with Session(_engine(), expire_on_commit=False) as session:
        try:
            with session.begin():
                session.add(user)
        except IntegrityError as exc:
            raise DuplicateEmailError("Email already registered.") from exc

    return _to_auth_user(user)


def authenticate_user(email: str, password: str) -> AuthUser | None:
    """Validate credentials and return the auth-safe user shape when valid."""
    normalized_email = normalize_email(email)
    now = _utcnow_naive()

    with Session(_engine(), expire_on_commit=False) as session:
        user = session.query(User).filter(User.email == normalized_email).one_or_none()
        if user is None:
            return None
        if not verify_password(password, str(user.password_hash)):
            return None

        user.last_login_at = now
        user.updated_at = now
        session.add(user)
        session.commit()
        return _to_auth_user(user)


def get_user_by_id(user_id: str) -> AuthUser | None:
    """Return an auth-safe user shape for an existing user id."""
    with Session(_engine(), expire_on_commit=False) as session:
        user = session.get(User, user_id)
        if user is None:
            return None
        return _to_auth_user(user)


def build_token_response(user_id: str, settings: AuthSettings) -> dict[str, Any]:
    """Build a consistent auth token response payload."""
    return {
        "access_token": issue_access_token(user_id, settings),
        "token_type": DEFAULT_TOKEN_TYPE,
        "expires_in": settings.access_token_ttl_seconds,
    }


def parse_bearer_token(authorization_header: str | None) -> str | None:
    """Extract a bearer token from an Authorization header."""
    if not authorization_header:
        return None

    parts = authorization_header.strip().split(" ", maxsplit=1)
    if len(parts) != 2:
        return None
    if parts[0].strip().lower() != DEFAULT_TOKEN_TYPE:
        return None

    token = parts[1].strip()
    if not token:
        return None
    return token
