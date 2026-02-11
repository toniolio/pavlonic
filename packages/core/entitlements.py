"""Entitlement helpers for plan-key and compatibility entitlement policy.

How it works:
    - Canonical enforcement is plan-key based (`free`, `basic_paid`).
    - Compatibility output remains `viewer_entitlement` (`public|paid`) for E004.
    - Unknown/missing plan keys fail closed to preview-only behavior.
    - Existing can_view(section, viewer_entitlement) callers remain supported.

How to run:
    - Import plan-key helpers for new enforcement logic.
    - Keep using can_view in legacy callers until endpoint rewiring is complete.
"""

from __future__ import annotations

from dataclasses import asdict

from .models import Result, Study


PLAN_KEY_FREE = "free"
PLAN_KEY_BASIC_PAID = "basic_paid"
PLAN_KEY_VALUES = {PLAN_KEY_FREE, PLAN_KEY_BASIC_PAID}

VIEWER_ENTITLEMENT_PUBLIC = "public"
VIEWER_ENTITLEMENT_PAID = "paid"
ENTITLEMENT_VALUES = {VIEWER_ENTITLEMENT_PUBLIC, VIEWER_ENTITLEMENT_PAID}

CONTENT_ACCESS_RULES_VERSION = 1


def is_paid_plan_key(plan_key: str | None) -> bool:
    """Return True only for the canonical paid plan key."""
    return plan_key == PLAN_KEY_BASIC_PAID


def has_preview_access(plan_key: str | None) -> bool:
    """Return True when preview access is allowed for the plan key."""
    return not is_paid_plan_key(plan_key)


def has_full_access(plan_key: str | None) -> bool:
    """Return True when full access is allowed for the plan key."""
    return is_paid_plan_key(plan_key)


def can_view_for_plan_key(section: str, plan_key: str | None) -> bool:
    """Return True when a canonical plan key can view the section.

    This function accepts canonical plan keys only. Non-canonical inputs
    fail closed by behaving as preview-only.
    """
    if section == "study.summary":
        return True
    if section == "study.results.overall":
        return True
    if section == "study.results.expanded":
        return has_full_access(plan_key)

    return False


def viewer_entitlement_for_context(
    *,
    is_authenticated: bool,
    plan_key: str | None,
) -> str:
    """Return compatibility `viewer_entitlement` derived from auth + plan.

    Mapping is fixed for E004:
    - unauthenticated (any plan value) -> public
    - authenticated free/unknown -> public
    - authenticated basic_paid -> paid
    """
    if is_authenticated and is_paid_plan_key(plan_key):
        return VIEWER_ENTITLEMENT_PAID
    return VIEWER_ENTITLEMENT_PUBLIC


def can_view(section: str, viewer_entitlement: str) -> bool:
    """Return True if the compatibility viewer entitlement can see section."""
    if viewer_entitlement not in ENTITLEMENT_VALUES:
        return False

    plan_key = (
        PLAN_KEY_BASIC_PAID
        if viewer_entitlement == VIEWER_ENTITLEMENT_PAID
        else PLAN_KEY_FREE
    )
    return can_view_for_plan_key(section, plan_key)


def _is_result_visible(result: Result, viewer_entitlement: str) -> bool:
    if result.visibility == "overall":
        return can_view("study.results.overall", viewer_entitlement)
    if result.visibility == "expanded":
        return can_view("study.results.expanded", viewer_entitlement)
    return False


def filter_results_for_viewer(study: Study) -> dict:
    """Serialize a Study dict with results filtered by entitlements."""
    payload = asdict(study)
    payload["results"] = [
        asdict(result)
        for result in study.results
        if _is_result_visible(result, study.viewer_entitlement)
    ]
    return payload
