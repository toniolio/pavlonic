# ADR-0004: Entitlements gating + curated technique rollups

## Context

We need server-side gating for result visibility and a minimal technique rollup path without committing to a full rollup engine.
The web viewer should remain dumb and only render what the API returns.

## Decision

- Enforce result visibility server-side for both studies and techniques.
- Use a curated JSON mapping (`techniques.mapping_json`) to resolve technique rollups.
- Allow a local dev/test override via `X-Pavlonic-Entitlement`; it must not be trusted in any hosted or production environment.

## Consequences

- Public requests only receive `overall` results; paid requests can receive `expanded` results.
- Technique rollups are deterministic and reversible without new schema.
- The API is the enforcement point; the UI stays a renderer.
