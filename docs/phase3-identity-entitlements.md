# Phase 3 Identity + Entitlements Snapshot

This is a public, factual snapshot of what exists at the end of **Phase 3 / Epic E004 (Identity + Entitlements MVP)**.  
It is a snapshot document and should not be updated to reflect later changes.

## What Phase 3 adds

### Identity (local auth)
- Introduces a minimal, local identity system to support membership gating:
  - `POST /v1/auth/register`
  - `POST /v1/auth/login`
  - `GET /v1/auth/me`
- API requests authenticate using `Authorization: Bearer <token>`.

### Entitlements (plan-based, server-side)
- Access is derived **server-side** from the authenticated user’s persisted `plan_key`.
- Canonical plan keys:
  - `free`
  - `basic_paid`
- “Fail closed” behavior:
  - missing/invalid/expired token or unknown user → never grants paid access
  - unknown plan keys → treated as the most restrictive access (equivalent to free)

### Dev override decommissioned
- The legacy dev entitlement override header used in earlier phases is **removed as a trusted input**.
- The API does not use any request header to elevate access (tests may include legacy strings only to assert they are ignored).

### Viewer remains dumb
- The static viewer does not implement content gating logic.
- It renders whatever the API returns for the current identity/plan context.

### Cache-safety for entitlement-sensitive responses
- For authenticated read responses that vary by entitlements, the API sets:
  - `Cache-Control: no-store`
  - `Vary: Authorization`

### Local paid-access validation workflow
- Adds a repeatable local workflow (replacing manual SQLite one-liners) to validate paid behavior safely.

## Local development (current)

From repo root:

- `make setup`
- `make db-reset`
- `make db-seed`
- `make dev`

- API: `http://127.0.0.1:8000`
- Web: `http://127.0.0.1:8001`

## Endpoints

Existing read endpoints (unchanged):
- `GET /v1/studies/{study_id}`
- `GET /v1/techniques/{technique_id_or_slug}`

New auth endpoints:
- `POST /v1/auth/register`
- `POST /v1/auth/login`
- `GET /v1/auth/me`

## Local paid-access validation

1) Start local services:
- `make db-reset`
- `make db-seed`
- `make dev`

2) Register and login in the viewer at `http://127.0.0.1:8001/`.

3) Flip plan to paid:
- `python scripts/set_user_plan.py --email <email> --plan basic_paid`

4) Refresh the viewer and confirm paid content appears.

5) Flip back to free if needed:
- `python scripts/set_user_plan.py --email <email> --plan free`

## Non-goals (still out of scope)

- Payments / billing integration.
- Email verification, password reset, or refresh tokens.
- Admin UI or write endpoints for content ingestion.
- Real study PDFs or proprietary datasets committed to the repo.
- SSR/path-based routing, canonicals/sitemaps, or structured data.
