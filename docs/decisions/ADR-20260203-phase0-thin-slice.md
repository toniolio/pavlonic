# ADR-0002: Phase 0 “thin slice” foundation

## Context

Pavlonic is being rebuilt as an evidence engine (and later, a practice tracker) in a public repository with private canonical specs stored locally in `docs-private/` (gitignored).

Early development needs:
- fast end-to-end confidence that the plumbing works
- a stable “shape” for Study data and serialization
- a minimal dev workflow that does not require remembering commands
- public-safe artifacts (no private specs, no real study data, no secrets)

## Decision

Build a Phase 0 “thin slice” that exercises the core path end-to-end using **synthetic demo data** only:

1. Define a minimal Study data shape and validation logic in `packages/core/`.
2. Store a synthetic demo Study JSON under `data/demo/`.
3. Expose a read endpoint in the API (`GET /v1/studies/{study_id}`) backed by the demo loader.
4. Render a single Study view in a static web viewer (`apps/web/`) that fetches the API.
5. Provide a single local dev command (`make dev`) that runs API + web together.
6. Add tests at each layer (schema/loader, API, web smoke).

Entitlements are implemented as a centralized stub so gating behavior can be swapped later without rewriting every surface.

## Consequences

- We have a working end-to-end path that is easy to run and easy to debug.
- Tests provide “gut checks” for basic correctness while the system is still small.
- The repo remains safe to share publicly:
  - canonical specs stay private
  - demo data stays synthetic
  - no authentication or paid-content enforcement is implemented yet (only a stub)
- Later phases can replace the demo data source, expand the schema, and add real auth/entitlements without discarding the thin slice.
