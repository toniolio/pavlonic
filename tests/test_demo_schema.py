"""Tests for the demo Study schema and loader."""

from packages.core.loader import load_demo_study


def test_demo_study_validates() -> None:
    study = load_demo_study()

    assert study.study_id == "0001"
    assert study.is_synthetic is True
    assert len(study.outcomes) > 0
    assert len(study.results) > 0


def test_demo_results_reference_known_outcomes() -> None:
    study = load_demo_study()
    outcome_ids = {outcome.outcome_id for outcome in study.outcomes}

    for result in study.results:
        assert result.outcome_id in outcome_ids


def test_demo_loader_accepts_study_id() -> None:
    study = load_demo_study("0001")

    assert study.study_id == "0001"


def test_demo_study_to_dict_round_trip() -> None:
    study = load_demo_study("0001")

    assert study.to_dict()["study_id"] == "0001"
