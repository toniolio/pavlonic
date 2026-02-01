# ADR-0001: Project structure

## Context

Pavlonic is a public repo with private canonical specs in `docs-private/`. We need a simple, boring monorepo layout that supports a web app, an API, shared core code, and clear documentation. See private specs for canonical details.

## Decision

Use a minimal monorepo layout:

- `apps/` for application entry points
- `packages/` for shared core packages
- `scripts/` for automation and tooling
- `docs/` for public-safe documentation
- `docs/decisions/` for ADRs
- `docs-private/` for private canonical specs (gitignored)

## Consequences

- New contributors can find code and docs predictably.
- Architecture decisions are recorded in ADRs.
- Private specs remain outside git, with public docs staying sanitized.
