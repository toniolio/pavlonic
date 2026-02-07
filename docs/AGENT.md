# Pavlonic Agent Notes (public-safe)

## Repo intent
Rebuild Pavlonic as an evidence engine + practice tracker.

This repo is public. Assume anything committed will be visible forever.

## Canonical artifacts (private-first)
The source of truth lives in **gitignored** private docs. Before any non-trivial work, read the relevant artifacts:

- Specs (canonical): `docs-private/specs-private/`
- Epics (work plan): `docs-private/epics-private/`
- Roadmaps (sequencing): `docs-private/roadmaps-private/`

If private docs are not present locally, **do not guess**. Ask for the missing artifact(s) or proceed only with trivial repo hygiene.

## Privacy and safety rules (hard requirements)
- `docs-private/` is gitignored and may contain private specs, prompts, and data. **Never add it to git.**
- Never introduce secrets into the repo. Use `.env*` locally (gitignored).
- Never commit real study data, paid content, proprietary prompts, or anything that could be considered competitive IP.
- Public docs must be paraphrased/sanitized summaries only (when requested).

## Default workflow (must follow)
1. **Pre-flight (always):**
   - State what you will do (1–2 sentences).
   - List which private artifacts you consulted (spec(s) + epic + roadmap).
   - List files you plan to change.
   - Call out any assumptions.

2. **Implement:**
   - Keep scope tight to the requested epic/story.
   - Prefer boring, explicit code over cleverness.
   - Centralize domain rules (avoid scattered one-off logic).

3. **Quality gate (always):**
   - Run `make lint` and `make test` (or the equivalent commands below).
   - Report results in the final message.

4. **Commit discipline:**
   - Small, coherent commits.
   - Each commit message explains the “why” (not just “wip”).

5. **Epic closeout (when applicable):**
   - Update the public phase snapshot and add ADR(s) capturing key decisions.
   - Write a private debrief in `docs-private/ops-private/`.

## Architecture discipline (do not drift)
- Do not invent new domain fields, rollup rules, or entitlement rules ad hoc.
- If a change affects architecture or future interoperability:
  - record it in an ADR under `docs/decisions/` (public-safe, no private text)
  - update the relevant canonical model/schema code
  - add/adjust tests

## Documentation style (default verbose)
- For any non-trivial module/script: include at top:
  - “How it works”
  - “How to run”
  - “Expected output”
- Add docstrings + inline comments for non-trivial logic.
- Update docs when behavior changes.

## Commands
Preferred:
- `make setup`
- `make lint`
- `make test`

Fallback (if needed):
- `python -m pytest`
- `ruff check .`

## Documentation policy
- Some docs are historical snapshots (e.g., `docs/phase0-foundation.md`) and must NOT be updated to reflect current behavior.
- Root `README.md` and `Makefile` are the source of truth for current setup commands.
- When updating docs, prefer living docs (`README.md`, `CONTRIBUTING.md`, `docs/AGENT.md`) over snapshot docs.
