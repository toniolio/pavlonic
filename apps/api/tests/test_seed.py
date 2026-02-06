"""Tests for deterministic seeding and golden fixture export."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config

from apps.api.seed import GOLDEN_PATH, export_seed_data, seed_db


def _db_url_for_path(db_path: Path) -> str:
    return f"sqlite:////{db_path.as_posix().lstrip('/')}"


def _run_migrations() -> None:
    alembic_ini = Path(__file__).resolve().parents[1] / "migrations" / "alembic.ini"
    config = Config(str(alembic_ini))
    command.upgrade(config, "head")


def test_seed_db_inserts_expected_rows(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "seed.db"
    monkeypatch.setenv("PAVLONIC_DB_URL", _db_url_for_path(db_path))

    _run_migrations()
    seed_db()

    with sqlite3.connect(str(db_path)) as conn:
        studies = conn.execute("SELECT COUNT(*) FROM studies").fetchone()[0]
        outcomes = conn.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0]
        results = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
        techniques = conn.execute("SELECT COUNT(*) FROM techniques").fetchone()[0]

    assert studies == 1
    assert techniques == 1
    assert outcomes >= 1
    assert results >= 1


def test_seed_export_matches_golden_fixture(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "golden.db"
    monkeypatch.setenv("PAVLONIC_DB_URL", _db_url_for_path(db_path))

    _run_migrations()
    seed_db()

    exported = export_seed_data()
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))

    assert exported == golden
