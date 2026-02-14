# ADR-20260214-auth-plan-entitlements

Date: 2026-02-14  
Status: Accepted  
Owners: Pavlonic

## Context

Phase 2 (public read-only site MVP) used a **dev-only override** mechanism to simulate paid access (e.g., a request header / viewer toggle). That was useful for early iteration but created a security footgun and blurred the line between “debug convenience” and “access control.”

Epic E004 introduced identity (local email/password) and plan-based entitlements. We needed a minimal but real model that:

- enforces access **server-side**
- keeps the web viewer as a “dumb renderer”
- **fails closed** in all ambiguous/error cases
- preserves the existing output surface (`viewer_entitlement`) for compatibility while migrating enforcement to a safer model

## Decision

1) **Entitlements are derived server-side** from the authenticated user and their persisted `plan_key`.

- Access decisions MUST be computed in the API layer (FastAPI) on every request.
- The server is the source of truth for content gating.

2) **Decommission all client/dev entitlement overrides** as trusted inputs.

- Legacy override mechanisms (e.g., `X-Pavlonic-Entitlement`) are not a trusted runtime input.
- The viewer must not inject any entitlement override into requests.
- If the header string exists in tests, it is only to assert that it is ignored.

3) **Fail closed** is mandatory.

- Missing/invalid/expired token, missing user, or unknown plan key MUST never grant paid access.
- Unknown `plan_key` maps to the most restrictive behavior (equivalent to free/public preview).

4) **Compatibility output remains** (`viewer_entitlement`).

- API responses may still include `viewer_entitlement` as `public|paid` to preserve downstream compatibility.
- This is output-only; it must not be used as an enforcement input.

## Consequences

### Positive
- Eliminates a class of “debug override becomes production bug” risks.
- Centralizes access control logic and makes it testable.
- Preserves a stable output surface (`viewer_entitlement`) while enforcing via the safer `plan_key` model.

### Negative / Tradeoffs
- Local testing of paid mode requires auth + a plan assignment workflow (no longer a single header flip).
- Requires explicit cache-safety handling for entitlement-sensitive responses.

## Alternatives considered

- **Keep a dev override in API** (rejected): too easy to leak into prod; encourages client-driven access control.
- **Encode plan/entitlements in JWT** (rejected): harder to revoke/change plan; risks stale entitlements until token expiry; encourages trusting client-provided claims.
- **Client-side gating** (rejected): increases leak risk and breaks “viewer is dumb” invariant.

## Related implementation notes

- Request context reads `Authorization: Bearer <token>` and resolves user → `plan_key` → entitlements.
- Tests must include regression coverage that the legacy header cannot elevate.

## References

- Phase snapshot: `docs/phase3-identity-entitlements.md`
- Code areas: `apps/api/request_context.py`, `packages/core/entitlements.py`, `apps/api/studies.py`, `apps/api/techniques.py`
