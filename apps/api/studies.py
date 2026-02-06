"""DB-backed study fetch helpers for the API.

How it works:
    - Load study, outcomes, and results from the SQLite DB via SQLAlchemy.
    - Filter result rows server-side based on viewer entitlements.
    - Serialize ORM rows into a deterministic, public-safe JSON payload.

How to run:
    - python -c "from apps.api.studies import load_study_payload; print(load_study_payload('0001', 'public'))"

Expected output:
    - A study payload dict matching the demo JSON shape, or None if missing.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from apps.api.db import get_db_url
from apps.api.db_models import Outcome as OutcomeModel
from apps.api.db_models import Result as ResultModel
from apps.api.db_models import Study as StudyModel
from packages.core.entitlements import can_view


RESULT_VISIBILITY_OVERALL = "overall"
RESULT_VISIBILITY_EXPANDED = "expanded"


def _deserialize_authors(authors_text: str) -> list[str]:
    """Deserialize stored authors JSON (or comma-delimited fallback)."""
    try:
        parsed = json.loads(authors_text)
    except json.JSONDecodeError:
        return [part.strip() for part in authors_text.split(",") if part.strip()]
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return [str(parsed)]


def _allowed_result_visibilities(viewer_entitlement: str) -> tuple[str, ...]:
    """Return the result visibility values allowed for the viewer."""
    allowed: list[str] = []
    if can_view("study.results.overall", viewer_entitlement):
        allowed.append(RESULT_VISIBILITY_OVERALL)
    if can_view("study.results.expanded", viewer_entitlement):
        allowed.append(RESULT_VISIBILITY_EXPANDED)
    return tuple(allowed)


def _outcome_payload(outcome: OutcomeModel) -> dict[str, Any]:
    return {
        "outcome_id": outcome.outcome_id,
        "label": outcome.label,
        "kind": outcome.kind,
    }


def _result_payload(result: ResultModel) -> dict[str, Any]:
    return {
        "result_id": result.result_id,
        "result_label": result.result_label,
        "result_description": result.result_description,
        "outcome_id": result.outcome_id,
        "visibility": result.visibility,
        "effect": {
            "type": result.effect_type,
            "value": float(result.effect_value),
            "direction": result.effect_direction,
            "provenance": result.effect_provenance,
        },
        "significance": {
            "type": result.significance_type,
            "value": float(result.significance_value),
            "provenance": result.significance_provenance,
        },
        "reliability": {
            "rating": result.reliability_rating,
            "provenance": result.reliability_provenance,
        },
        "notes": None,
    }


def _study_payload(
    study: StudyModel,
    outcomes: Iterable[OutcomeModel],
    results: Iterable[ResultModel],
    viewer_entitlement: str,
) -> dict[str, Any]:
    return {
        "study_id": study.study_id,
        "is_synthetic": bool(study.is_synthetic),
        "citation": {
            "title": study.title,
            "authors": _deserialize_authors(study.authors),
            "year": int(study.year),
            "venue": study.venue,
        },
        "study_type": study.study_type,
        "viewer_entitlement": viewer_entitlement,
        "groups": [],
        "outcomes": [_outcome_payload(outcome) for outcome in outcomes],
        "results": [_result_payload(result) for result in results],
    }


def load_study_payload(study_id: str, viewer_entitlement: str) -> dict[str, Any] | None:
    """Load a study payload from the DB or return None if missing."""
    db_url = get_db_url()
    engine = create_engine(db_url, future=True)

    with Session(engine) as session:
        study = session.get(StudyModel, study_id)
        if study is None:
            return None

        outcomes = (
            session.query(OutcomeModel)
            .filter(OutcomeModel.study_id == study_id)
            .order_by(OutcomeModel.outcome_id)
            .all()
        )

        allowed = _allowed_result_visibilities(viewer_entitlement)
        if allowed:
            results = (
                session.query(ResultModel)
                .filter(ResultModel.study_id == study_id, ResultModel.visibility.in_(allowed))
                .order_by(ResultModel.result_id)
                .all()
            )
        else:
            results = []

    return _study_payload(study, outcomes, results, viewer_entitlement)
