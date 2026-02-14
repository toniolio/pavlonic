"""Tests for DB URL configuration helpers."""

from pathlib import Path

import pytest

from apps.api.db import (
    DEFAULT_DB_URL,
    get_db_url,
    init_sqlite_file,
    resolve_sqlite_file_path,
    sqlite_url_for_file_path,
)


def test_get_db_url_defaults_when_missing() -> None:
    assert get_db_url({}) == DEFAULT_DB_URL


def test_get_db_url_uses_env_override() -> None:
    override = "sqlite:///data/private/override.db"
    assert get_db_url({"PAVLONIC_DB_URL": override}) == override


def test_get_db_url_ignores_empty_env_value() -> None:
    assert get_db_url({"PAVLONIC_DB_URL": "   "}) == DEFAULT_DB_URL


def test_resolve_sqlite_file_path_rejects_memory() -> None:
    with pytest.raises(ValueError, match="In-memory"):
        resolve_sqlite_file_path("sqlite:///:memory:")


def test_resolve_sqlite_file_path_rejects_non_sqlite_scheme() -> None:
    with pytest.raises(ValueError, match="sqlite"):
        resolve_sqlite_file_path("postgresql://localhost/db")


def test_resolve_sqlite_file_path_accepts_relative_path() -> None:
    path = resolve_sqlite_file_path("sqlite:///data/private/pavlonic.db")
    assert path == Path("data/private/pavlonic.db")


def test_resolve_sqlite_file_path_accepts_absolute_path() -> None:
    path = resolve_sqlite_file_path("sqlite:////tmp/pavlonic.db")
    assert path == Path("/tmp/pavlonic.db")


def test_sqlite_url_for_file_path_accepts_relative_path() -> None:
    assert sqlite_url_for_file_path("data/private/pavlonic.db") == "sqlite:///data/private/pavlonic.db"


def test_sqlite_url_for_file_path_accepts_absolute_path() -> None:
    assert sqlite_url_for_file_path(Path("/tmp/pavlonic.db")) == "sqlite:////tmp/pavlonic.db"


def test_sqlite_url_for_file_path_rejects_empty_value() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        sqlite_url_for_file_path("   ")


def test_init_sqlite_file_writes_header(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    db_path.write_bytes(b"")
    assert db_path.stat().st_size == 0

    db_url = f"sqlite:////{db_path}"
    initialized = init_sqlite_file(db_url)

    assert initialized == db_path
    assert db_path.stat().st_size > 0
