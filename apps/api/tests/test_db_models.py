"""Tests for SQLAlchemy model imports."""


def test_db_models_importable() -> None:
    from apps.api import db_models

    assert db_models.Study.__tablename__ == "studies"
