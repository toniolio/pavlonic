"""Request context helpers for API endpoints.

How it works:
    - Read the viewer entitlement from a strict header override.
    - Default to "public" for missing/invalid values.

How to run:
    - Import get_viewer_entitlement and call it inside a FastAPI handler.

Expected output:
    - Returns "public" or "paid" based on request headers.
"""

from __future__ import annotations

from fastapi import Request

from packages.core.entitlements import ENTITLEMENT_VALUES


ENTITLEMENT_HEADER = "X-Pavlonic-Entitlement"
DEFAULT_VIEWER_ENTITLEMENT = "public"


def get_viewer_entitlement(request: Request) -> str:
    """Return the viewer entitlement derived from the request headers."""
    raw_value = request.headers.get(ENTITLEMENT_HEADER, "").strip().lower()
    if raw_value in ENTITLEMENT_VALUES:
        return raw_value
    return DEFAULT_VIEWER_ENTITLEMENT
