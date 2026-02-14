# ADR-20260214-auth-contract-jwt

Date: 2026-02-14  
Status: Accepted  
Owners: Pavlonic

## Context

Pavlonic needs a minimal identity layer to support plan-based entitlements. The system must remain simple (no external IdP yet), compatible with a static web viewer, and safe-by-default.

We must define a stable contract for:

- registration and login
- authentication on API requests
- session persistence in the viewer
- failure behavior (especially avoiding accidental elevation)

## Decision

1) Implement local auth endpoints:

- `POST /v1/auth/register`
- `POST /v1/auth/login`
- `GET /v1/auth/me`

2) Use **Bearer JWT** for API authentication:

- Client sends `Authorization: Bearer <token>`
- `/v1/auth/me` is strict:
  - 401 on missing/invalid/expired token
  - 401 if token is valid but user cannot be resolved

3) Token contents are **identity only**:

- JWT contains identity (e.g., `sub = user_id`)
- Do **not** encode plan/entitlements in the token

4) Login failures are non-enumerating:

- Wrong password and unknown email return the same generic 401 failure

5) Viewer session persistence:

- Viewer stores token in localStorage under key: `pavlonic_access_token`
- Viewer attaches bearer token to API calls when present
- Viewer clears token on 401 from `/v1/auth/me`

## Consequences

### Positive
- Works with a static front-end (no server-side sessions required).
- Plan changes are effective immediately (because plan is resolved from DB per request).
- Clear, testable authentication boundary.

### Negative / Tradeoffs
- localStorage is convenient but not the long-term ideal for production security posture (future hardening expected).
- No refresh token mechanism yet; users re-login after token expiry.

## Alternatives considered

- **Cookie sessions** (rejected for now): complicates static viewer hosting and CSRF considerations.
- **Refresh tokens** (deferred): adds complexity not needed for MVP.
- **Embed plan/entitlements in token** (rejected): stale claims + revocation difficulty.

## References

- Phase snapshot: `docs/phase3-identity-entitlements.md`
- Viewer: `apps/web/app.js`, `apps/web/index.html`
- API: `apps/api/auth.py`, `apps/api/main.py`
