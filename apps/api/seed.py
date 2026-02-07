"""Deterministic DB seeding + golden fixture export.

How it works:
    - Loads the synthetic study JSON from data/demo/study_0001.json.
    - Clears v0 tables in dependency order to avoid duplicates.
    - Inserts one study, its outcomes/results, and one technique with curated mapping_json.
    - Exports a stable JSON snapshot for the golden fixture.

How to run:
    - python -c "from apps.api.seed import seed_db, write_seed_golden; seed_db(); write_seed_golden()"

Expected output:
    - A seeded database plus data/demo/seed_golden.json updated from the seeded content.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from apps.api.db import get_db_url
from apps.api.db_models import Outcome, Result, Study, Technique


REPO_ROOT = Path(__file__).resolve().parents[2]
STUDY_SOURCE_PATH = REPO_ROOT / "data" / "demo" / "study_0001.json"
GOLDEN_PATH = REPO_ROOT / "data" / "demo" / "seed_golden.json"

TECHNIQUE_ID = "spaced-practice"
TECHNIQUE_TITLE = "Spaced practice"
TECHNIQUE_SUMMARY = "Practice distributed over time to improve retention."
TECHNIQUE_VISIBILITY = "overall"
MAPPING_RESULT_IDS = ("R1", "R2")


def _load_study_source() -> dict[str, Any]:
    """Load the synthetic study JSON source."""
    if not STUDY_SOURCE_PATH.exists():
        raise FileNotFoundError(f"Missing study source: {STUDY_SOURCE_PATH}")
    return json.loads(STUDY_SOURCE_PATH.read_text(encoding="utf-8"))


def _serialize_authors(authors: list[str]) -> str:
    """Serialize authors to a stable JSON string for storage."""
    return json.dumps(authors, ensure_ascii=True)


def _deserialize_authors(authors_text: str) -> list[str]:
    """Deserialize authors JSON text back into a list."""
    try:
        parsed = json.loads(authors_text)
    except json.JSONDecodeError:
        return [part.strip() for part in authors_text.split(",") if part.strip()]
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return [str(parsed)]


def _build_mapping(study_id: str) -> list[dict[str, str]]:
    """Build the curated technique mapping entries."""
    return [{"study_id": study_id, "result_id": result_id} for result_id in MAPPING_RESULT_IDS]


def _sorted_mapping(mapping: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return a deterministically ordered mapping list."""
    normalized = [
        {"study_id": item["study_id"], "result_id": item["result_id"]}
        for item in mapping
    ]
    return sorted(normalized, key=lambda item: (item["study_id"], item["result_id"]))


def seed_db() -> None:
    """Seed the database with deterministic synthetic data."""
    db_url = get_db_url()
    engine = create_engine(db_url, future=True)

    source = _load_study_source()
    citation = source["citation"]

    study_id = source["study_id"]
    mapping = _build_mapping(study_id)
    source_result_ids = {result["result_id"] for result in source["results"]}
    missing = [result_id for result_id in MAPPING_RESULT_IDS if result_id not in source_result_ids]
    if missing:
        raise ValueError(f"Mapping result IDs missing from source: {missing}")

    study = Study(
        study_id=study_id,
        is_synthetic=bool(source["is_synthetic"]),
        title=citation["title"],
        authors=_serialize_authors(citation["authors"]),
        year=int(citation["year"]),
        venue=citation["venue"],
        study_type=source["study_type"],
    )

    outcomes = [
        Outcome(
            study_id=study_id,
            outcome_id=outcome["outcome_id"],
            label=outcome["label"],
            kind=outcome["kind"],
        )
        for outcome in source["outcomes"]
    ]

    results = [
        Result(
            study_id=study_id,
            result_id=result["result_id"],
            outcome_id=result["outcome_id"],
            result_label=result["result_label"],
            result_description=result.get("result_description"),
            effect_type=result["effect"]["type"],
            effect_value=result["effect"]["value"],
            effect_direction=result["effect"]["direction"],
            effect_provenance=result["effect"]["provenance"],
            significance_type=result["significance"]["type"],
            significance_value=result["significance"]["value"],
            significance_provenance=result["significance"]["provenance"],
            reliability_rating=result["reliability"]["rating"],
            reliability_provenance=result["reliability"]["provenance"],
            visibility=result["visibility"],
        )
        for result in source["results"]
    ]

    technique = Technique(
        technique_id=TECHNIQUE_ID,
        title=TECHNIQUE_TITLE,
        summary=TECHNIQUE_SUMMARY,
        visibility=TECHNIQUE_VISIBILITY,
        mapping_json=mapping,
    )

    with Session(engine) as session:
        with session.begin():
            session.query(Technique).delete()
            session.query(Result).delete()
            session.query(Outcome).delete()
            session.query(Study).delete()

            session.add(study)
            session.add_all(outcomes)
            session.add_all(results)
            session.add(technique)


def _study_to_dict(study: Study) -> dict[str, Any]:
    """Convert a Study ORM instance into a stable dict."""
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


def _outcome_to_dict(outcome: Outcome) -> dict[str, Any]:
    """Convert an Outcome ORM instance into a stable dict."""
    return {
        "study_id": outcome.study_id,
        "outcome_id": outcome.outcome_id,
        "label": outcome.label,
        "kind": outcome.kind,
    }


def _result_to_dict(result: Result) -> dict[str, Any]:
    """Convert a Result ORM instance into a stable dict."""
    return {
        "study_id": result.study_id,
        "result_id": result.result_id,
        "outcome_id": result.outcome_id,
        "result_label": result.result_label,
        "result_description": result.result_description,
        "visibility": result.visibility,
        "effect": {
            "type": result.effect_type,
            "value": result.effect_value,
            "direction": result.effect_direction,
            "provenance": result.effect_provenance,
        },
        "significance": {
            "type": result.significance_type,
            "value": result.significance_value,
            "provenance": result.significance_provenance,
        },
        "reliability": {
            "rating": result.reliability_rating,
            "provenance": result.reliability_provenance,
        },
    }


def _technique_to_dict(technique: Technique) -> dict[str, Any]:
    """Convert a Technique ORM instance into a stable dict."""
    mapping = technique.mapping_json or []
    return {
        "technique_id": technique.technique_id,
        "title": technique.title,
        "summary": technique.summary,
        "visibility": technique.visibility,
        "mapping_json": _sorted_mapping(mapping),
    }


def export_seed_data() -> dict[str, Any]:
    """Export the seeded DB content into a stable JSON-friendly dict."""
    db_url = get_db_url()
    engine = create_engine(db_url, future=True)

    with Session(engine) as session:
        studies = session.query(Study).order_by(Study.study_id).all()
        outcomes = (
            session.query(Outcome)
            .order_by(Outcome.study_id, Outcome.outcome_id)
            .all()
        )
        results = (
            session.query(Result)
            .order_by(Result.study_id, Result.result_id)
            .all()
        )
        techniques = session.query(Technique).order_by(Technique.technique_id).all()

    return {
        "studies": [_study_to_dict(study) for study in studies],
        "outcomes": [_outcome_to_dict(outcome) for outcome in outcomes],
        "results": [_result_to_dict(result) for result in results],
        "techniques": [_technique_to_dict(technique) for technique in techniques],
    }


def write_seed_golden(output_path: Path = GOLDEN_PATH) -> Path:
    """Write the golden fixture JSON to disk."""
    data = export_seed_data()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path
