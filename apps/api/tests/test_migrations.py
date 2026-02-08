"""Tests for Alembic migrations."""

from pathlib import Path
import sqlite3

from alembic import command
from alembic.config import Config


def _table_names(db_path: Path) -> set[str]:
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {row[0] for row in rows}


def test_migrations_create_tables(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "migrated.db"
    db_url = f"sqlite:////{db_path.as_posix().lstrip('/')}"
    monkeypatch.setenv("PAVLONIC_DB_URL", db_url)

    alembic_ini = Path(__file__).resolve().parents[1] / "migrations" / "alembic.ini"
    config = Config(str(alembic_ini))
    command.upgrade(config, "head")

    table_names = _table_names(db_path)
    assert {"studies", "outcomes", "results", "techniques", "users"} <= table_names


def test_migration_downgrade_from_head_removes_users(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "migrated.db"
    db_url = f"sqlite:////{db_path.as_posix().lstrip('/')}"
    monkeypatch.setenv("PAVLONIC_DB_URL", db_url)

    alembic_ini = Path(__file__).resolve().parents[1] / "migrations" / "alembic.ini"
    config = Config(str(alembic_ini))

    command.upgrade(config, "head")
    assert "users" in _table_names(db_path)

    command.downgrade(config, "0002")
    table_names = _table_names(db_path)
    assert "users" not in table_names
    assert {"studies", "outcomes", "results", "techniques"} <= table_names
