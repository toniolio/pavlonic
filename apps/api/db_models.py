"""SQLAlchemy ORM models for the v0 data layer cut line.

How it works:
    - Defines ORM models for studies, outcomes, results, and techniques only.
    - Captures the minimal v0 fields needed for read-only study/technique pages.

How to run:
    - python -c "from apps.api.db_models import Study, Outcome, Result, Technique; print(Study.__tablename__)"

Expected output:
    - Prints the table name for the Study model.
"""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Study(Base):
    """ORM model for the studies table (v0 cut line)."""

    __tablename__ = "studies"

    study_id = Column(String, primary_key=True)
    is_synthetic = Column(Boolean, nullable=False)
    title = Column(Text, nullable=False)
    authors = Column(Text, nullable=False)
    year = Column(Integer, nullable=False)
    venue = Column(Text, nullable=False)
    study_type = Column(String, nullable=False)


class Outcome(Base):
    """ORM model for the outcomes table (v0 cut line)."""

    __tablename__ = "outcomes"

    study_id = Column(String, ForeignKey("studies.study_id"), primary_key=True)
    outcome_id = Column(String, primary_key=True)
    label = Column(Text, nullable=False)
    kind = Column(String, nullable=False)


class Result(Base):
    """ORM model for the results table (v0 cut line)."""

    __tablename__ = "results"

    study_id = Column(String, ForeignKey("studies.study_id"), primary_key=True)
    result_id = Column(String, primary_key=True)
    outcome_id = Column(String, nullable=False)
    result_label = Column(Text, nullable=False)
    result_description = Column(Text)

    effect_type = Column(String, nullable=False)
    effect_value = Column(Float, nullable=False)
    effect_direction = Column(String, nullable=False)
    effect_provenance = Column(String, nullable=False)

    significance_type = Column(String, nullable=False)
    significance_value = Column(Float, nullable=False)
    significance_provenance = Column(String, nullable=False)

    reliability_rating = Column(String, nullable=False)
    reliability_provenance = Column(String, nullable=False)

    visibility = Column(String, nullable=False)


class Technique(Base):
    """ORM model for the techniques table (v0 cut line)."""

    __tablename__ = "techniques"

    technique_id = Column(String, primary_key=True)
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    visibility = Column(String, nullable=False)
    mapping_json = Column(JSON)
