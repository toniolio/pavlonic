"""Pavlonic core study models (public-safe, minimal).

How it works:
    - Define a minimal Study schema required for the seed demo JSON.
    - Provide explicit validation for required fields and allowed values.
    - Enforce cross-references (results must point to existing outcomes).

How to run:
    - Import and call Study.from_dict(data).

Expected output:
    - Returns a Study instance on valid data.
    - Raises ValueError with a clear message on invalid data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


PROVENANCE_VALUES = {"reported", "computed", "entered"}
DIRECTION_VALUES = {"positive", "negative", "neutral", "unknown"}
OUTCOME_KIND_VALUES = {"performance", "learning"}


def _require_keys(data: dict, keys: Iterable[str], context: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(f"{context} missing required field(s): {missing_list}")


def _require_type(value: object, expected: type, context: str) -> None:
    if not isinstance(value, expected):
        raise ValueError(f"{context} must be {expected.__name__}")


def _require_one_of(value: str, allowed: set[str], context: str) -> None:
    if value not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        raise ValueError(f"{context} must be one of: {allowed_list}")


@dataclass(frozen=True)
class Citation:
    title: str
    authors: list[str]
    year: int
    venue: str

    @classmethod
    def from_dict(cls, data: dict) -> "Citation":
        _require_keys(data, ("title", "authors", "year", "venue"), "citation")
        _require_type(data["title"], str, "citation.title")
        _require_type(data["authors"], list, "citation.authors")
        _require_type(data["year"], int, "citation.year")
        _require_type(data["venue"], str, "citation.venue")

        if not all(isinstance(author, str) for author in data["authors"]):
            raise ValueError("citation.authors must contain only strings")

        return cls(
            title=data["title"],
            authors=data["authors"],
            year=data["year"],
            venue=data["venue"],
        )


@dataclass(frozen=True)
class Outcome:
    outcome_id: str
    label: str
    kind: str

    @classmethod
    def from_dict(cls, data: dict) -> "Outcome":
        _require_keys(data, ("outcome_id", "label", "kind"), "outcome")
        _require_type(data["outcome_id"], str, "outcome.outcome_id")
        _require_type(data["label"], str, "outcome.label")
        _require_type(data["kind"], str, "outcome.kind")
        _require_one_of(data["kind"], OUTCOME_KIND_VALUES, "outcome.kind")
        return cls(
            outcome_id=data["outcome_id"],
            label=data["label"],
            kind=data["kind"],
        )


@dataclass(frozen=True)
class Effect:
    type: str
    value: float
    direction: str
    provenance: str

    @classmethod
    def from_dict(cls, data: dict) -> "Effect":
        _require_keys(data, ("type", "value", "direction", "provenance"), "effect")
        _require_type(data["type"], str, "effect.type")
        _require_type(data["value"], (int, float), "effect.value")
        _require_type(data["direction"], str, "effect.direction")
        _require_type(data["provenance"], str, "effect.provenance")
        _require_one_of(data["direction"], DIRECTION_VALUES, "effect.direction")
        _require_one_of(data["provenance"], PROVENANCE_VALUES, "effect.provenance")
        return cls(
            type=data["type"],
            value=float(data["value"]),
            direction=data["direction"],
            provenance=data["provenance"],
        )


@dataclass(frozen=True)
class Significance:
    type: str
    value: float
    provenance: str

    @classmethod
    def from_dict(cls, data: dict) -> "Significance":
        _require_keys(data, ("type", "value", "provenance"), "significance")
        _require_type(data["type"], str, "significance.type")
        _require_type(data["value"], (int, float), "significance.value")
        _require_type(data["provenance"], str, "significance.provenance")
        _require_one_of(data["provenance"], PROVENANCE_VALUES, "significance.provenance")
        return cls(
            type=data["type"],
            value=float(data["value"]),
            provenance=data["provenance"],
        )


@dataclass(frozen=True)
class Reliability:
    rating: str
    provenance: str

    @classmethod
    def from_dict(cls, data: dict) -> "Reliability":
        _require_keys(data, ("rating", "provenance"), "reliability")
        _require_type(data["rating"], str, "reliability.rating")
        _require_type(data["provenance"], str, "reliability.provenance")
        _require_one_of(data["provenance"], PROVENANCE_VALUES, "reliability.provenance")
        return cls(
            rating=data["rating"],
            provenance=data["provenance"],
        )


@dataclass(frozen=True)
class Result:
    result_id: str
    result_label: str
    result_description: str | None
    outcome_id: str
    effect: Effect
    significance: Significance
    reliability: Reliability
    notes: str | None

    @classmethod
    def from_dict(cls, data: dict) -> "Result":
        _require_keys(
            data,
            (
                "result_id",
                "result_label",
                "outcome_id",
                "effect",
                "significance",
                "reliability",
            ),
            "result",
        )
        _require_type(data["result_id"], str, "result.result_id")
        _require_type(data["result_label"], str, "result.result_label")
        _require_type(data["outcome_id"], str, "result.outcome_id")

        description = data.get("result_description")
        if description is not None:
            _require_type(description, str, "result.result_description")

        notes = data.get("notes")
        if notes is not None:
            _require_type(notes, str, "result.notes")

        return cls(
            result_id=data["result_id"],
            result_label=data["result_label"],
            result_description=description,
            outcome_id=data["outcome_id"],
            effect=Effect.from_dict(data["effect"]),
            significance=Significance.from_dict(data["significance"]),
            reliability=Reliability.from_dict(data["reliability"]),
            notes=notes,
        )


@dataclass(frozen=True)
class Study:
    study_id: str
    is_synthetic: bool
    citation: Citation
    study_type: str
    viewer_entitlement: str
    groups: list[dict]
    outcomes: list[Outcome]
    results: list[Result]

    @classmethod
    def from_dict(cls, data: dict) -> "Study":
        _require_keys(
            data,
            (
                "study_id",
                "is_synthetic",
                "citation",
                "study_type",
                "viewer_entitlement",
                "groups",
                "outcomes",
                "results",
            ),
            "study",
        )
        _require_type(data["study_id"], str, "study.study_id")
        _require_type(data["is_synthetic"], bool, "study.is_synthetic")
        _require_type(data["study_type"], str, "study.study_type")
        _require_type(data["viewer_entitlement"], str, "study.viewer_entitlement")
        _require_type(data["groups"], list, "study.groups")
        _require_type(data["outcomes"], list, "study.outcomes")
        _require_type(data["results"], list, "study.results")

        if not data["is_synthetic"]:
            raise ValueError("study.is_synthetic must be true for demo data")

        citation = Citation.from_dict(data["citation"])
        outcomes = [Outcome.from_dict(item) for item in data["outcomes"]]
        results = [Result.from_dict(item) for item in data["results"]]

        outcome_ids = {outcome.outcome_id for outcome in outcomes}
        missing_refs = [result.result_id for result in results if result.outcome_id not in outcome_ids]
        if missing_refs:
            missing_list = ", ".join(sorted(missing_refs))
            raise ValueError(f"results reference unknown outcomes: {missing_list}")

        return cls(
            study_id=data["study_id"],
            is_synthetic=data["is_synthetic"],
            citation=citation,
            study_type=data["study_type"],
            viewer_entitlement=data["viewer_entitlement"],
            groups=data["groups"],
            outcomes=outcomes,
            results=results,
        )
