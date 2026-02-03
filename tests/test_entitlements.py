"""Unit tests for entitlement gating helpers."""

from packages.core.entitlements import can_view


def test_can_view_summary_and_overall() -> None:
    assert can_view("study.summary", "public") is True
    assert can_view("study.results.overall", "public") is True


def test_can_view_expanded_requires_paid() -> None:
    assert can_view("study.results.expanded", "public") is False
    assert can_view("study.results.expanded", "paid") is True


def test_can_view_unknown_entitlement_denied() -> None:
    assert can_view("study.results.expanded", "unknown") is False
