# Phase 2 Public Read-Only Site Snapshot

This is a public, factual snapshot of what exists at the end of Phase 2 / Epic E003 (public read-only site MVP).
It is a snapshot document and should not be updated to reflect later changes.

## What Phase 2 adds
- Technique payload contract now supports JSON-first “topic tables” intended for rendering evidence tables (server returns render-ready tables plus resolved references).
- Static web viewer supports basic site navigation:
  - Technique page route
  - Study page route
  - Deep link targeting of a study result row via query param.
- Evidence Table UI on technique pages:
  - summary rows + expandable details with accessible toggles (ARIA).
  - internal links from technique refs to study deep links.
- Study page result rows support expandable details and stable DOM ids for deep-link targeting.
- Minimal metadata baseline:
  - default `<title>`, meta description, and basic Open Graph tags.
  - runtime page title updates based on the current route.
- Explicitly documents current SEO limitations due to hash routing (defers canonicals/sitemap/structured data until SSR/path routing exists).

## Local development (current)
From repo root:

```bash
make setup
make db-reset
make db-seed
make dev
```

- API: http://127.0.0.1:8000
- Web: http://127.0.0.1:8001

## Routes (web viewer)
- `#/techniques/<slug>`
- `#/studies/<id>`
- Deep link to a result row: `#/studies/<id>?result=R1`

Legacy entry routes are accepted for backward compatibility:
- `#/study/<id>`
- `?study=<id>`
The viewer should generate only the canonical routes above.

## Endpoints (unchanged)
- `GET /v1/studies/{study_id}`
- `GET /v1/techniques/{technique_id_or_slug}`

## Entitlements
- Server-side gating is enforced for result visibility.
- `X-Pavlonic-Entitlement` remains a local dev/test override only and must not be trusted in any hosted or production environment.
- Default entitlement is `public` when the header is missing or invalid.

## Non-goals
- Real authentication or membership integration.
- Write endpoints, admin UI, ingestion agents.
- Real study data or PDFs in the repo.
- SSR/path-based routing, canonical URLs, sitemap generation, or structured data.
- UI polish beyond the minimal static viewer.
