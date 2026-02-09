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

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
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


def get_auth_settings(env: dict[str, str] | os._Environ[str] = os.environ) -> AuthSettings:
    """Load auth settings from environment variables."""
    jwt_secret = env.get(JWT_SECRET_ENV, "").strip()
    if not jwt_secret:
        raise AuthConfigError(f"{JWT_SECRET_ENV} must be set.")

    jwt_algorithm = env.get(JWT_ALGORITHM_ENV, "").strip() or DEFAULT_JWT_ALGORITHM
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
    encoded_password = password.encode("utf-8")
    hashed = bcrypt.hashpw(encoded_password, bcrypt.gensalt(rounds=bcrypt_rounds))
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Return True when the plaintext password matches the hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def issue_access_token(user_id: str, settings: AuthSettings, now: datetime | None = None) -> str:
    """Issue a JWT access token containing only identity claims."""
    issued_at = now or datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(seconds=settings.access_token_ttl_seconds)
    payload: dict[str, Any] = {
        "sub": user_id,
        "iat": issued_at,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return str(token)


def verify_access_token(access_token: str, settings: AuthSettings) -> str:
    """Verify and decode a JWT access token, returning user_id from sub."""
    try:
        payload = jwt.decode(
            access_token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp"]},
        )
    except ExpiredSignatureError as exc:
        raise TokenExpiredError("Access token expired.") from exc
    except InvalidTokenError as exc:
        raise TokenValidationError("Access token invalid.") from exc

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise TokenValidationError("Access token subject missing.")
    return user_id


def _engine():
    return create_engine(get_db_url(), future=True)


def _to_auth_user(user: User) -> AuthUser:
    return AuthUser(
        user_id=str(user.user_id),
        email=str(user.email),
        plan_key=str(user.plan_key),
    )


def register_user(email: str, password: str, settings: AuthSettings) -> AuthUser:
    """Create a user account and return the stored auth-safe user shape."""
    normalized_email = normalize_email(email)
    now = datetime.utcnow()
    user = User(
        user_id=str(uuid.uuid4()),
        email=normalized_email,
        password_hash=hash_password(password, settings.bcrypt_rounds),
        plan_key=DEFAULT_PLAN_KEY,
        status=DEFAULT_STATUS,
        created_at=now,
        updated_at=now,
    )

    with Session(_engine()) as session:
        try:
            with session.begin():
                session.add(user)
        except IntegrityError as exc:
            raise DuplicateEmailError("Email already registered.") from exc

    return _to_auth_user(user)


def authenticate_user(email: str, password: str) -> AuthUser | None:
    """Validate credentials and return the auth-safe user shape when valid."""
    normalized_email = normalize_email(email)
    now = datetime.utcnow()

    with Session(_engine()) as session:
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
    with Session(_engine()) as session:
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
