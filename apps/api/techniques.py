"""DB-backed technique fetch helpers for the API.

How it works:
    - Load the technique and curated mapping_json from the SQLite DB.
    - Resolve mapping_json references into result payloads.
    - Filter mapped results server-side based on viewer entitlements.

How to run:
    - python -c "from apps.api.techniques import load_technique_payload; print(load_technique_payload('spaced-practice', 'public'))"

Expected output:
    - A technique payload dict matching the API shape, or None if missing.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

from sqlalchemy import create_engine, tuple_
from sqlalchemy.orm import Session

from apps.api.db import get_db_url
from apps.api.db_models import Outcome as OutcomeModel
from apps.api.db_models import Result as ResultModel
from apps.api.db_models import Study as StudyModel
from apps.api.db_models import Technique as TechniqueModel
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


def _normalize_mapping(mapping: Iterable[dict[str, Any]] | None) -> list[dict[str, str]]:
    """Normalize and deterministically order mapping entries."""
    if not mapping:
        return []

    normalized: list[dict[str, str]] = []
    for item in mapping:
        if not isinstance(item, dict):
            continue
        study_id = str(item.get("study_id", "")).strip()
        result_id = str(item.get("result_id", "")).strip()
        if not study_id or not result_id:
            continue
        normalized.append({"study_id": study_id, "result_id": result_id})

    return sorted(normalized, key=lambda entry: (entry["study_id"], entry["result_id"]))


def _study_reference_payload(study: StudyModel) -> dict[str, Any]:
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
    }


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


def load_technique_payload(
    technique_id_or_slug: str,
    viewer_entitlement: str,
) -> dict[str, Any] | None:
    """Load a technique payload from the DB or return None if missing."""
    db_url = get_db_url()
    engine = create_engine(db_url, future=True)

    with Session(engine) as session:
        technique = session.get(TechniqueModel, technique_id_or_slug)
        if technique is None:
            return None

        allowed_visibilities = _allowed_result_visibilities(viewer_entitlement)
        if technique.visibility not in allowed_visibilities:
            return None

        mapping = _normalize_mapping(technique.mapping_json)
        mapped_results: list[dict[str, Any]] = []
        filtered_mapping: list[dict[str, str]] = []

        if mapping and allowed_visibilities:
            pairs = [(item["study_id"], item["result_id"]) for item in mapping]
            results = (
                session.query(ResultModel)
                .filter(
                    tuple_(ResultModel.study_id, ResultModel.result_id).in_(pairs),
                    ResultModel.visibility.in_(allowed_visibilities),
                )
                .all()
            )

            results_by_key = {(result.study_id, result.result_id): result for result in results}
            study_ids = {result.study_id for result in results}
            studies = (
                session.query(StudyModel)
                .filter(StudyModel.study_id.in_(study_ids))
                .all()
                if study_ids
                else []
            )
            studies_by_id = {study.study_id: study for study in studies}

            outcome_pairs = {(result.study_id, result.outcome_id) for result in results}
            outcomes = (
                session.query(OutcomeModel)
                .filter(tuple_(OutcomeModel.study_id, OutcomeModel.outcome_id).in_(outcome_pairs))
                .all()
                if outcome_pairs
                else []
            )
            outcomes_by_key = {
                (outcome.study_id, outcome.outcome_id): outcome for outcome in outcomes
            }

            for item in mapping:
                key = (item["study_id"], item["result_id"])
                result = results_by_key.get(key)
                if result is None:
                    continue
                study = studies_by_id.get(result.study_id)
                outcome = outcomes_by_key.get((result.study_id, result.outcome_id))
                mapped_results.append(
                    {
                        "study": _study_reference_payload(study) if study else None,
                        "outcome": _outcome_payload(outcome) if outcome else None,
                        "result": _result_payload(result),
                    }
                )
                filtered_mapping.append(item)

    return {
        "technique_id": technique.technique_id,
        "title": technique.title,
        "summary": technique.summary,
        "visibility": technique.visibility,
        "viewer_entitlement": viewer_entitlement,
        "mapping_json": filtered_mapping,
        "results": mapped_results,
    }
