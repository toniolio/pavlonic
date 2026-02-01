# Pavlonic Agent Notes (public-safe)

## Repo intent
Rebuild Pavlonic as an evidence engine + practice tracker.

## Privacy
- `docs-private/` is gitignored and may contain private specs/data. Never add it to git.
- Never introduce secrets into the repo. Use `.env` locally (gitignored).

## Commands
Python venv: `.venv/`
Run:
- `python -m pytest`
- `ruff check .`

## Work style
- Make small, coherent commits.
- Before coding: propose a short plan + list files to change.
- After coding: run checks/tests and report results.
