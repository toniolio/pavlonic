"""DB-backed technique fetch helpers for the API.

How it works:
    - Load the technique, curated mapping_json, and tables_json from the SQLite DB.
    - Resolve mapping_json references into result payloads.
    - Filter mapped results and topic table rows server-side based on viewer entitlements.

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


def _normalize_channel(channel: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize a table channel payload."""
    if not isinstance(channel, dict):
        channel = {}
    refs = [str(ref).strip() for ref in channel.get("refs", []) if str(ref).strip()]
    normalized: dict[str, Any] = {
        "effect_size_label": str(channel.get("effect_size_label", "")).strip(),
        "reliability_label": str(channel.get("reliability_label", "")).strip(),
        "refs": refs,
    }
    if "counts" in channel:
        normalized["counts"] = channel["counts"]
    return normalized


def _normalize_tables(tables: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Normalize tables_json into a stable shape."""
    if not tables:
        return []

    normalized_tables: list[dict[str, Any]] = []
    for table in tables:
        if not isinstance(table, dict):
            continue
        rows = table.get("rows", [])
        normalized_rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            normalized_rows.append(
                {
                    "row_id": str(row.get("row_id", "")).strip(),
                    "row_label": str(row.get("row_label", "")).strip(),
                    "summary_statement": str(row.get("summary_statement", "")).strip(),
                    "performance": _normalize_channel(row.get("performance")),
                    "learning": _normalize_channel(row.get("learning")),
                }
            )
        normalized_tables.append(
            {
                "table_id": str(table.get("table_id", "")).strip(),
                "table_label": str(table.get("table_label", "")).strip(),
                "rows": normalized_rows,
            }
        )
    return normalized_tables


def _is_overall_row(row: dict[str, Any]) -> bool:
    """Return True if the row is the Overall row."""
    row_id = str(row.get("row_id", "")).strip().lower()
    row_label = str(row.get("row_label", "")).strip().lower()
    return row_id == "overall" or row_label == "overall"


def _filter_tables_for_entitlement(
    tables: list[dict[str, Any]],
    viewer_entitlement: str,
) -> list[dict[str, Any]]:
    """Return tables filtered by viewer entitlement."""
    if can_view("study.results.expanded", viewer_entitlement):
        return tables

    filtered_tables: list[dict[str, Any]] = []
    for table in tables:
        rows = [row for row in table.get("rows", []) if _is_overall_row(row)]
        if not rows:
            continue
        filtered_tables.append(
            {
                **table,
                "rows": rows,
            }
        )
    return filtered_tables


def _collect_table_refs(tables: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for table in tables:
        for row in table.get("rows", []):
            for channel_name in ("performance", "learning"):
                channel = row.get(channel_name, {})
                for ref in channel.get("refs", []):
                    ref_text = str(ref).strip()
                    if ref_text:
                        refs.append(ref_text)
    return refs


def _parse_ref(ref: str) -> tuple[str, str] | None:
    if ":" not in ref:
        return None
    study_id, result_id = ref.split(":", 1)
    study_id = study_id.strip()
    result_id = result_id.strip()
    if not study_id or not result_id:
        return None
    return study_id, result_id


def _filter_table_refs(
    tables: list[dict[str, Any]],
    allowed_pairs: set[tuple[str, str]],
) -> list[dict[str, Any]]:
    """Return tables with refs filtered to allowed study/result pairs."""
    filtered_tables: list[dict[str, Any]] = []
    for table in tables:
        filtered_rows = []
        for row in table.get("rows", []):
            filtered_row = dict(row)
            for channel_name in ("performance", "learning"):
                channel = dict(filtered_row.get(channel_name, {}))
                filtered_refs = []
                for ref in channel.get("refs", []):
                    parsed = _parse_ref(str(ref))
                    if parsed and parsed in allowed_pairs:
                        filtered_refs.append(str(ref))
                channel["refs"] = filtered_refs
                filtered_row[channel_name] = channel
            filtered_rows.append(filtered_row)
        filtered_tables.append({**table, "rows": filtered_rows})
    return filtered_tables


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

        tables = _normalize_tables(technique.tables_json)
        tables = _filter_tables_for_entitlement(tables, viewer_entitlement)
        table_refs = _collect_table_refs(tables)
        table_pairs = {_parse_ref(ref) for ref in table_refs}
        table_pairs.discard(None)

        resolved_results: dict[str, dict[str, Any]] = {}
        allowed_pairs: set[tuple[str, str]] = set()

        if table_pairs and allowed_visibilities:
            results = (
                session.query(ResultModel)
                .filter(
                    tuple_(ResultModel.study_id, ResultModel.result_id).in_(table_pairs),
                    ResultModel.visibility.in_(allowed_visibilities),
                )
                .all()
            )
            allowed_pairs = {(result.study_id, result.result_id) for result in results}
            for result in results:
                ref = f"{result.study_id}:{result.result_id}"
                resolved_results[ref] = {
                    "study_id": result.study_id,
                    "result_id": result.result_id,
                    "internal_link": f"#/studies/{result.study_id}?result={result.result_id}",
                }

        tables = _filter_table_refs(tables, allowed_pairs)

    return {
        "technique_id": technique.technique_id,
        "title": technique.title,
        "summary": technique.summary,
        "visibility": technique.visibility,
        "viewer_entitlement": viewer_entitlement,
        "mapping_json": filtered_mapping,
        "results": mapped_results,
        "tables": tables,
        "resolved_results": resolved_results,
    }
