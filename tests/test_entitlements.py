"""Unit tests for entitlement policy helpers."""

from packages.core.entitlements import (
    VIEWER_ENTITLEMENT_PAID,
    VIEWER_ENTITLEMENT_PUBLIC,
    can_view,
    can_view_for_plan_key,
    has_full_access,
    has_preview_access,
    is_paid_plan_key,
    viewer_entitlement_for_context,
)


def test_plan_key_is_paid_mapping() -> None:
    assert is_paid_plan_key("basic_paid") is True
    assert is_paid_plan_key("free") is False
    assert is_paid_plan_key("unknown") is False
    assert is_paid_plan_key(None) is False


def test_plan_key_preview_vs_full_access_mapping() -> None:
    assert has_full_access("basic_paid") is True
    assert has_preview_access("basic_paid") is False

    assert has_full_access("free") is False
    assert has_preview_access("free") is True


def test_can_view_for_plan_key_fail_closed_for_unknown_or_none_plan() -> None:
    assert can_view_for_plan_key("study.summary", "unknown") is True
    assert can_view_for_plan_key("study.results.overall", "unknown") is True
    assert can_view_for_plan_key("study.results.expanded", "unknown") is False

    assert can_view_for_plan_key("study.summary", None) is True
    assert can_view_for_plan_key("study.results.overall", None) is True
    assert can_view_for_plan_key("study.results.expanded", None) is False


def test_viewer_entitlement_compatibility_mapping_is_output_only() -> None:
    assert (
        viewer_entitlement_for_context(
            is_authenticated=False,
            plan_key=None,
        )
        == VIEWER_ENTITLEMENT_PUBLIC
    )
    assert (
        viewer_entitlement_for_context(
            is_authenticated=True,
            plan_key="free",
        )
        == VIEWER_ENTITLEMENT_PUBLIC
    )
    assert (
        viewer_entitlement_for_context(
            is_authenticated=True,
            plan_key="unknown",
        )
        == VIEWER_ENTITLEMENT_PUBLIC
    )
    assert (
        viewer_entitlement_for_context(
            is_authenticated=True,
            plan_key="basic_paid",
        )
        == VIEWER_ENTITLEMENT_PAID
    )
    assert (
        viewer_entitlement_for_context(
            is_authenticated=False,
            plan_key="basic_paid",
        )
        == VIEWER_ENTITLEMENT_PUBLIC
    )


def test_plan_enforcement_helpers_do_not_accept_viewer_entitlement_inputs() -> None:
    assert is_paid_plan_key("public") is False
    assert is_paid_plan_key("paid") is False
    assert can_view_for_plan_key("study.results.expanded", "public") is False
    assert can_view_for_plan_key("study.results.expanded", "paid") is False


def test_can_view_summary_and_overall() -> None:
    assert can_view("study.summary", "public") is True
    assert can_view("study.results.overall", "public") is True


def test_can_view_expanded_requires_paid() -> None:
    assert can_view("study.results.expanded", "public") is False
    assert can_view("study.results.expanded", "paid") is True


def test_can_view_unknown_entitlement_denied() -> None:
    assert can_view("study.results.expanded", "unknown") is False
