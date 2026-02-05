"""Database configuration helpers for local SQLite usage.

How it works:
    - get_db_url reads PAVLONIC_DB_URL with a default fallback.
    - resolve_sqlite_file_path validates sqlite file URLs and returns a Path.
    - init_sqlite_file creates parent directories and touches the sqlite file.

How to run:
    - python -c "from apps.api.db import get_db_url, init_sqlite_file; print(init_sqlite_file(get_db_url()))"

Expected output:
    - Prints the resolved sqlite file path when initialization succeeds.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Mapping
from pathlib import Path


DEFAULT_DB_URL = "sqlite:///data/private/pavlonic.db"


def get_db_url(env: Mapping[str, str] = os.environ) -> str:
    """Return the configured DB URL, defaulting to the local sqlite file."""
    value = env.get("PAVLONIC_DB_URL", "").strip()
    return value if value else DEFAULT_DB_URL


def resolve_sqlite_file_path(db_url: str) -> Path:
    """Resolve a sqlite file URL to a filesystem path."""
    if not isinstance(db_url, str) or not db_url.strip():
        raise ValueError("DB URL must be a non-empty sqlite file URL.")

    if "?" in db_url or "#" in db_url:
        raise ValueError("SQLite URLs must not include query parameters or fragments.")

    if not db_url.startswith("sqlite://"):
        raise ValueError("Unsupported DB URL scheme. Only sqlite file URLs are supported.")

    if db_url.startswith("sqlite:////"):
        path_part = db_url[len("sqlite:////") :]
        if not path_part:
            raise ValueError("SQLite URL must include a file path.")
        if path_part == ":memory:":
            raise ValueError("In-memory sqlite URLs are not supported. Use a file path.")
        return Path("/") / path_part

    if db_url.startswith("sqlite:///"):
        path_part = db_url[len("sqlite:///") :]
        if not path_part:
            raise ValueError("SQLite URL must include a file path.")
        if path_part == ":memory:":
            raise ValueError("In-memory sqlite URLs are not supported. Use a file path.")
        if path_part.startswith("/"):
            raise ValueError("Absolute sqlite paths must use sqlite:////absolute/path.db.")
        return Path(path_part)

    raise ValueError(
        "Unsupported sqlite URL format. Use sqlite:///relative/path.db or sqlite:////absolute/path.db."
    )


def init_sqlite_file(db_url: str) -> Path:
    """Create the sqlite file if missing and return its path."""
    db_path = resolve_sqlite_file_path(db_url)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(db_path)):
        pass

    return db_path
