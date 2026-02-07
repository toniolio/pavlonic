# Phase 1 Data Layer Snapshot

This is a public, factual snapshot of what exists at the end of Phase 1 / Epic E002 (data layer MVP).
It is a snapshot document and should not be updated to reflect later changes.

## What Phase 1 adds
- DB-backed read API for studies and techniques.
- Alembic migrations for the v0 schema cut line.
- Deterministic seed data with a golden fixture.
- Technique rollup endpoint backed by curated mapping.

## Local development (current)
From repo root:

```bash
make setup
make db-reset
make db-seed
make dev
```

## Endpoints
- `GET /v1/studies/{study_id}`
- `GET /v1/techniques/{technique_id_or_slug}`

## Entitlements
- Server-side gating is enforced for result visibility.
- `X-Pavlonic-Entitlement` is a local dev/test override only and must not be trusted in any hosted or production environment.
- Default entitlement is `public` when the header is missing or invalid.

## Non-goals
- Real authentication or membership integration.
- Write endpoints, admin UI, ingestion agents.
- Real study data or PDFs in the repo.
- UI polish beyond the minimal static viewer.
