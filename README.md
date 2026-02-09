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

Auth endpoints require a JWT secret:

```bash
export PAVLONIC_AUTH_JWT_SECRET="dev-only-change-me"
# Optional:
# export PAVLONIC_AUTH_JWT_ALGORITHM="HS256"
# export PAVLONIC_AUTH_ACCESS_TOKEN_TTL_SECONDS="86400"
# export PAVLONIC_AUTH_BCRYPT_ROUNDS="12"
```

Then hit the API endpoints (default public vs paid override). `X-Pavlonic-Entitlement` is a dev-only testing override and must not be enabled or used in production:

```bash
# Default public (no header)
curl http://127.0.0.1:8000/v1/studies/0001
curl http://127.0.0.1:8000/v1/techniques/spaced-practice

# Paid override
curl -H "X-Pavlonic-Entitlement: paid" http://127.0.0.1:8000/v1/studies/0001
```

Auth smoke (register -> login -> me):

```bash
curl -sS -X POST http://127.0.0.1:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"dev-password"}'

TOKEN=$(curl -sS -X POST http://127.0.0.1:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"dev-password"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

curl -sS http://127.0.0.1:8000/v1/auth/me \
  -H "Authorization: Bearer ${TOKEN}"
```

## SEO note (Phase 2)

The current public viewer uses hash routing (`#/techniques/...`, `#/studies/...`) and a static client-rendered page, so SEO is intentionally limited in this phase.

Canonical tags, sitemap generation, and structured data are deferred until SSR/path routing is in place.
