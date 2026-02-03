"""Entitlement helpers for gating study sections.

How it works:
    - Provide a small can_view helper that maps sections to entitlements.
    - Provide a helper to filter study results based on visibility rules.

How to run:
    - Import can_view and call it from application code.

Expected output:
    - can_view returns True/False based on section and entitlement.
    - filter_results_for_viewer returns a Study dict with gated results removed.
"""

from __future__ import annotations

from dataclasses import asdict

from .models import Result, Study


ENTITLEMENT_VALUES = {"public", "paid"}


def can_view(section: str, viewer_entitlement: str) -> bool:
    """Return True if the viewer is allowed to see the section."""
    if viewer_entitlement not in ENTITLEMENT_VALUES:
        return False

    if section == "study.summary":
        return True
    if section == "study.results.overall":
        return True
    if section == "study.results.expanded":
        return viewer_entitlement == "paid"

    return False


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
