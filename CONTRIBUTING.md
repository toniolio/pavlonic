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

Use the single dev command to run both the API and web viewer:

- `make setup`
- `make dev`

Then open:

- API: `http://127.0.0.1:8000/v1/studies/0001`
- Web: `http://127.0.0.1:8001/`
