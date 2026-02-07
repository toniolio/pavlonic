# Pavlonic

Private specs live in docs-private/ and are not committed.

## Built with AI (seriously)

This project is built with AI coding agents (e.g., Codex) to accelerate development. That said, I’m treating it like a real software project:

- human review of meaningful diffs
- tests + linting as a baseline gate
- eval harnesses for extraction/rollups where correctness matters
- metrics published as the system matures

The goal is to produce something genuinely useful for users. But I’m also using this repo to sharpen my ability to work effectively with AI tools, while remaining skeptical of the hype.

## Repository structure

- `apps/web/` — web app scaffold
- `apps/api/` — API scaffold
- `packages/core/` — shared core package
- `scripts/` — automation scripts
- `docs/specs/` — public specs (empty for now)
- `docs-private/` — private specs (never committed)

## Local development (DB-backed API)

To use the DB-backed API locally, run migrations and seed the SQLite database before starting the dev server:

```bash
make db-reset
make db-seed
make dev
```

Then hit the API endpoints (default public vs paid override). `X-Pavlonic-Entitlement` is a dev-only testing override and must not be enabled or used in production:

```bash
# Default public (no header)
curl http://127.0.0.1:8000/v1/studies/0001
curl http://127.0.0.1:8000/v1/techniques/spaced-practice

# Paid override
curl -H "X-Pavlonic-Entitlement: paid" http://127.0.0.1:8000/v1/studies/0001
```

## SEO note (Phase 2)

The current public viewer uses hash routing (`#/techniques/...`, `#/studies/...`) and a static client-rendered page, so SEO is intentionally limited in this phase.

Canonical tags, sitemap generation, and structured data are deferred until SSR/path routing is in place.
