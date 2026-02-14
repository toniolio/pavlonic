#!/usr/bin/env python
"""Set a user's plan key in the local database.

How it works:
    - Normalizes the requested email using the same auth normalization logic.
    - Validates plan keys against canonical E004 values (`free`, `basic_paid`).
    - Resolves DB URL with API defaults, with optional `--db` override.
    - Updates exactly one user row and fails closed for missing/duplicate matches.

How to run:
    - python scripts/set_user_plan.py --email demo@example.com --plan basic_paid
    - python scripts/set_user_plan.py --email demo@example.com --plan free --db /tmp/pavlonic.db
    - python scripts/set_user_plan.py --email demo@example.com --plan free --db sqlite:////tmp/pavlonic.db

Expected output:
    - Updated plan_key for demo@example.com: free -> basic_paid
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from apps.api.auth import normalize_email
from apps.api.db import get_db_url, resolve_sqlite_file_path, sqlite_url_for_file_path
from apps.api.db_models import User
from packages.core.entitlements import PLAN_KEY_BASIC_PAID, PLAN_KEY_FREE


ALLOWED_PLAN_KEYS = (PLAN_KEY_FREE, PLAN_KEY_BASIC_PAID)


class SetUserPlanError(ValueError):
    """Base error for set_user_plan workflow failures."""


class InvalidPlanError(SetUserPlanError):
    """Raised when an unsupported plan key is provided."""


class UserNotFoundError(SetUserPlanError):
    """Raised when no user exists for the requested email."""


class DuplicateUsersError(SetUserPlanError):
    """Raised when multiple rows match a normalized email."""


@dataclass(frozen=True)
class PlanUpdateResult:
    """Result shape for a successful plan update."""

    email: str
    old_plan_key: str
    new_plan_key: str


def _utcnow_naive() -> datetime:
    """Return UTC now as a naive datetime for sqlite DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _resolve_db_url(db_override: str | None) -> str:
    """Resolve DB URL using default API logic or a caller override."""
    if db_override is None or not db_override.strip():
        db_url = get_db_url()
    else:
        override = db_override.strip()
        if "://" in override:
            db_url = override
        else:
            db_url = sqlite_url_for_file_path(Path(override))

    # Enforce the same sqlite URL rules used by the API.
    resolve_sqlite_file_path(db_url)
    return db_url


def _validate_plan_key(plan_key: str) -> str:
    value = plan_key.strip()
    if value not in ALLOWED_PLAN_KEYS:
        allowed = ", ".join(ALLOWED_PLAN_KEYS)
        raise InvalidPlanError(f"Invalid plan key '{value}'. Allowed values: {allowed}.")
    return value


def run(*, email: str, plan_key: str, db_override: str | None = None) -> PlanUpdateResult:
    """Update exactly one user by normalized email."""
    normalized_email = normalize_email(email)
    if not normalized_email:
        raise SetUserPlanError("Email must be non-empty.")

    target_plan_key = _validate_plan_key(plan_key)
    db_url = _resolve_db_url(db_override)
    engine = create_engine(db_url, future=True)

    try:
        with Session(engine, expire_on_commit=False) as session:
            with session.begin():
                users = session.query(User).filter(User.email == normalized_email).all()
                if not users:
                    raise UserNotFoundError(f"No user found for email: {normalized_email}")
                if len(users) > 1:
                    raise DuplicateUsersError(
                        f"Multiple users found for email: {normalized_email}. No updates applied."
                    )

                user = users[0]
                old_plan_key = str(user.plan_key)
                user.plan_key = target_plan_key
                user.updated_at = _utcnow_naive()
                session.add(user)
    except SQLAlchemyError as exc:
        raise SetUserPlanError(f"Database update failed: {exc}") from exc
    finally:
        engine.dispose()

    return PlanUpdateResult(
        email=normalized_email,
        old_plan_key=old_plan_key,
        new_plan_key=target_plan_key,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for local plan assignment."""
    parser = argparse.ArgumentParser(
        description="Set a user's plan key by email (local/dev workflow).",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="User email (normalized to lowercase).",
    )
    parser.add_argument(
        "--plan",
        required=True,
        help="Canonical plan key: free or basic_paid.",
    )
    parser.add_argument(
        "--db",
        required=False,
        help="Optional sqlite file path or full SQLAlchemy sqlite URL override.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for set-user-plan workflow."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = run(email=args.email, plan_key=args.plan, db_override=args.db)
    except SetUserPlanError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Updated plan_key for {result.email}: {result.old_plan_key} -> {result.new_plan_key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
