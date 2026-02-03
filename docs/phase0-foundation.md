# Phase 0 Foundation Snapshot

This document is a factual snapshot of what exists at the end of Phase 0 / Epic E001 (“foundation first thin slice”).

**Goal of this phase:** prove the end-to-end plumbing of Pavlonic’s “evidence engine” with a minimal, verifiable vertical slice:
- a single synthetic study record
- a validated domain model + loader
- a read API endpoint
- a tiny web viewer that renders a study
- a centralized, testable entitlement gating stub (no real auth)

This phase intentionally does **not** implement real membership/auth, content ops workflows, extraction agents, rollups, or a production UI.


## What exists now

### Data
- `data/demo/study_0001.json`
  - Synthetic-only seed study data for scaffolding.
  - Safe to keep public (no real study data; no paid content).

### Core domain (Python)
- `packages/core/models.py`
  - Minimal domain objects for a Study, Citation, Outcomes, Results, etc.
  - Includes a `Study.to_dict()` helper for JSON-safe serialization.
- `packages/core/loader.py`
  - Loads demo studies by ID (e.g., `"0001"`) from `data/demo/`.
- `packages/core/entitlements.py`
  - Central gating helper (e.g., `can_view(...)`) used for consistent filtering.
  - This is a stub — it enforces rules, but does not authenticate users.

### API (FastAPI)
- `apps/api/main.py`
  - Endpoint: `GET /v1/studies/{study_id}`
  - Returns the Study as JSON.
  - Applies entitlement gating server-side (the web viewer renders what it receives).
  - Includes dev-only CORS allowance to support the local web viewer.

### Web viewer (static)
- `apps/web/index.html`, `apps/web/app.js`
  - Fetches the API study payload and renders:
    - title + citation
    - outcomes list
    - results table
- Routing / selection
  - Study ID selection supports query param (`?study=0001`) and hash routing (e.g., `#/study/0001`).

### Developer ergonomics
- `Makefile`
  - `make setup` installs minimal Python tooling
  - `make lint` runs Ruff
  - `make test` runs Pytest
  - `make dev` runs API + web server locally together

### Documentation
- `AGENT.md` (public-safe agent notes)
- `CONTRIBUTING.md` (public contributing + how to run)
- `docs/decisions/ADR-0001-project-structure.md`


## How to run (local)

From the repo root:

```bash
make setup
make dev
```

Then open:

- API: `http://127.0.0.1:8000/v1/studies/0001`
- Web: `http://127.0.0.1:8001/`
- Web (hash route): `http://127.0.0.1:8001/#/study/0001`
- Web (query param): `http://127.0.0.1:8001/?study=0001`
