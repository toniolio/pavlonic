# Public specs (status)

This repo is public. Canonical specs and roadmaps are **private** and live locally under `docs-private/` (gitignored). Do **not** commit them.

## What exists publicly right now

There are no public spec documents yet.

For a public-safe snapshot of what exists, see:
- `docs/phase0-foundation.md`
- `docs/decisions/`

## Working with private specs (local-only)

If you have access to the canonical specs locally:
- place them under `docs-private/specs-private/`
- keep them out of git (this directory is gitignored)

When making changes that are guided by private specs:
- do **not** quote or copy private content into the public repo
- in public docs/ADRs, you may write: **“See private specs.”** (without details)

## Principles

- Keep the public repo safe to share.
- Use synthetic demo data only (`data/demo/`).
- Keep private study data, paid content, and extraction prompts out of git.
