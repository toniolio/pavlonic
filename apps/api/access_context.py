"""Read-access context adapter for plan-based API gating.

How it works:
    - Carries canonical plan_key for enforcement.
    - Carries compatibility viewer_entitlement for payload output.
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.core.entitlements import viewer_entitlement_for_context


@dataclass(frozen=True)
class ReadAccessContext:
    """Access context for read endpoints backed by auth-derived plan state."""

    is_authenticated: bool
    plan_key: str | None
    viewer_entitlement: str


def build_read_access_context(
    *,
    is_authenticated: bool,
    plan_key: str | None,
) -> ReadAccessContext:
    """Build read-access context from resolved request auth state."""
    return ReadAccessContext(
        is_authenticated=is_authenticated,
        plan_key=plan_key,
        viewer_entitlement=viewer_entitlement_for_context(
            is_authenticated=is_authenticated,
            plan_key=plan_key,
        ),
    )
