# ADR-0003: Data layer uses SQLite + Alembic + deterministic seed

## Context

Phase 1 needs a minimal, reproducible database layer that can power read-only study and technique pages.
We need a boring local default, explicit migrations, and deterministic seed data for tests.

## Decision

- Use SQLite as the local default database (`PAVLONIC_DB_URL` override supported).
- Use Alembic for migrations under `apps/api/migrations/`.
- Maintain deterministic seed data and a golden fixture under `data/demo/seed_golden.json`.

## Consequences

- Local development is simple and file-backed by default.
- Schema changes are explicit and versioned.
- Tests can validate seed determinism via the golden fixture.
