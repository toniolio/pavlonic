"""Shared fixtures for API tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from apps.api.seed import seed_db


def _db_url_for_path(db_path: Path) -> str:
    return f"sqlite:////{db_path.as_posix().lstrip('/')}"


def _run_migrations() -> None:
    alembic_ini = Path(__file__).resolve().parents[1] / "migrations" / "alembic.ini"
    config = Config(str(alembic_ini))
    command.upgrade(config, "head")


@pytest.fixture()
def seeded_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "api.db"
    monkeypatch.setenv("PAVLONIC_DB_URL", _db_url_for_path(db_path))
    _run_migrations()
    seed_db()
    return db_path
