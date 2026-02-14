# Contributing

Thanks for helping improve Pavlonic. This repo is public, so never commit private specs, paid content, or real study data.

## Quick start

Exact commands:

- `make setup`
- `make lint`
- `make test`

## Repository layout (high level)

- `apps/` — application entry points (web, API)
- `packages/` — shared core packages
- `scripts/` — tooling and automation
- `docs/` — public-safe documentation
- `docs/decisions/` — architecture decision records (ADRs)
- `docs-private/` — private canonical specs (gitignored; never committed)

## Decision logging

Record architectural decisions in `docs/decisions/` using the ADR template.

If a change needs spec reference, write “See private specs” without quoting.

## Run API locally

Use the single dev command to run both the API and web viewer (DB-backed API requires seed):

- `make setup`
- `make db-reset`
- `make db-seed`
- `make dev`

Then open:

- API: `http://127.0.0.1:8000/v1/studies/0001`
- Web: `http://127.0.0.1:8001/`

## Local paid-access validation

Paid access is derived server-side from the authenticated user's `plan_key`.
The legacy `X-Pavlonic-Entitlement` header override is removed and ignored.

1. Start local services:
- `make db-reset`
- `make db-seed`
- `make dev`
2. Register and login in the Account panel at `http://127.0.0.1:8001/`.
3. Flip plan to paid:
- `python scripts/set_user_plan.py --email <email> --plan basic_paid`
4. Refresh the viewer and confirm paid content appears.
5. Flip back to free if needed:
- `python scripts/set_user_plan.py --email <email> --plan free`

Web route examples:

- Canonical study route: `http://127.0.0.1:8001/#/studies/0001`
- Canonical deep link: `http://127.0.0.1:8001/#/studies/0001?result=R1`
- Canonical technique route: `http://127.0.0.1:8001/#/techniques/spaced-practice`
- Legacy study hash route (accepted): `http://127.0.0.1:8001/#/study/0001`
- Legacy study query param (accepted): `http://127.0.0.1:8001/?study=0001`
