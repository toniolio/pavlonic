"""Tests for Alembic migrations."""

from pathlib import Path
import sqlite3

from alembic import command
from alembic.config import Config


def test_migrations_create_tables(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "migrated.db"
    db_url = f"sqlite:////{db_path.as_posix().lstrip('/')}"
    monkeypatch.setenv("PAVLONIC_DB_URL", db_url)

    alembic_ini = Path(__file__).resolve().parents[1] / "migrations" / "alembic.ini"
    config = Config(str(alembic_ini))
    command.upgrade(config, "head")

    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

    table_names = {row[0] for row in rows}
    assert {"studies", "outcomes", "results", "techniques"} <= table_names
