"""Tests for local user plan assignment CLI workflow."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.set_user_plan import InvalidPlanError, main, run


def _create_users_table(db_path: Path, *, unique_email: bool = True) -> None:
    unique_constraint = " UNIQUE" if unique_email else ""
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            f"""
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                email TEXT NOT NULL{unique_constraint},
                password_hash TEXT NOT NULL,
                plan_key TEXT NOT NULL DEFAULT 'free',
                status TEXT NOT NULL DEFAULT 'active',
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                last_login_at DATETIME
            )
            """
        )
        conn.commit()


def _insert_user(
    db_path: Path,
    *,
    user_id: str,
    email: str,
    plan_key: str = "free",
) -> None:
    timestamp = "2026-02-14T00:00:00"
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO users (
                user_id,
                email,
                password_hash,
                plan_key,
                status,
                created_at,
                updated_at,
                last_login_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                email,
                "bcrypt$placeholder",
                plan_key,
                "active",
                timestamp,
                timestamp,
                None,
            ),
        )
        conn.commit()


def _plan_keys_for_email(db_path: Path, email: str) -> list[str]:
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(
            "SELECT plan_key FROM users WHERE email = ? ORDER BY user_id",
            (email,),
        ).fetchall()
    return [str(row[0]) for row in rows]


def test_set_user_plan_main_updates_plan_with_path_override(tmp_path: Path, capsys) -> None:
    db_path = tmp_path / "users.db"
    _create_users_table(db_path, unique_email=True)
    _insert_user(db_path, user_id="u-1", email="demo@example.com", plan_key="free")

    exit_code = main(
        [
            "--email",
            " Demo@Example.com ",
            "--plan",
            "basic_paid",
            "--db",
            str(db_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert "Updated plan_key for demo@example.com: free -> basic_paid" in captured.out
    assert _plan_keys_for_email(db_path, "demo@example.com") == ["basic_paid"]


def test_set_user_plan_run_accepts_full_sqlalchemy_url_override(tmp_path: Path) -> None:
    db_path = tmp_path / "users.db"
    _create_users_table(db_path, unique_email=True)
    _insert_user(db_path, user_id="u-1", email="url@example.com", plan_key="free")

    db_url = f"sqlite:////{db_path.as_posix().lstrip('/')}"
    result = run(
        email="url@example.com",
        plan_key="basic_paid",
        db_override=db_url,
    )

    assert result.email == "url@example.com"
    assert result.old_plan_key == "free"
    assert result.new_plan_key == "basic_paid"
    assert _plan_keys_for_email(db_path, "url@example.com") == ["basic_paid"]


def test_set_user_plan_run_rejects_invalid_plan_key(tmp_path: Path) -> None:
    db_path = tmp_path / "users.db"
    _create_users_table(db_path, unique_email=True)
    _insert_user(db_path, user_id="u-1", email="invalid-plan@example.com", plan_key="free")

    with pytest.raises(InvalidPlanError, match="Allowed values: free, basic_paid"):
        run(
            email="invalid-plan@example.com",
            plan_key="pro",
            db_override=str(db_path),
        )


def test_set_user_plan_main_fails_when_email_missing_and_leaves_data_unchanged(
    tmp_path: Path,
    capsys,
) -> None:
    db_path = tmp_path / "users.db"
    _create_users_table(db_path, unique_email=True)
    _insert_user(db_path, user_id="u-1", email="existing@example.com", plan_key="free")

    exit_code = main(
        [
            "--email",
            "missing@example.com",
            "--plan",
            "basic_paid",
            "--db",
            str(db_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "No user found for email: missing@example.com" in captured.err
    assert captured.out == ""
    assert _plan_keys_for_email(db_path, "existing@example.com") == ["free"]


def test_set_user_plan_main_fails_on_duplicate_email_and_makes_no_partial_update(
    tmp_path: Path,
    capsys,
) -> None:
    db_path = tmp_path / "users.db"
    _create_users_table(db_path, unique_email=False)
    _insert_user(db_path, user_id="u-1", email="dupe@example.com", plan_key="free")
    _insert_user(db_path, user_id="u-2", email="dupe@example.com", plan_key="free")

    exit_code = main(
        [
            "--email",
            "DUPE@example.com",
            "--plan",
            "basic_paid",
            "--db",
            str(db_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Multiple users found for email: dupe@example.com" in captured.err
    assert captured.out == ""
    assert _plan_keys_for_email(db_path, "dupe@example.com") == ["free", "free"]
