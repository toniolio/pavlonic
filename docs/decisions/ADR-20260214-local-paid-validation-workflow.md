# ADR-20260214-local-paid-validation-workflow

Date: 2026-02-14  
Status: Accepted  
Owners: Pavlonic

## Context

After decommissioning dev entitlement overrides, developers still need a repeatable way to validate:

- unauth preview behavior
- authenticated free behavior
- authenticated paid behavior

We want a workflow that is:

- safe (does not introduce a bypass mechanism)
- deterministic and scriptable
- easy to describe in README/CONTRIBUTING

## Decision

Adopt an explicit local workflow for paid-mode testing:

1) Start local services and seed demo data:

- `make db-reset`
- `make db-seed`
- `make dev`

2) Register + login via the web viewer Account panel (`http://127.0.0.1:8001/`)

3) Flip plan using a CLI script:

- `python scripts/set_user_plan.py --email <email> --plan basic_paid`
- (Optional revert) `python scripts/set_user_plan.py --email <email> --plan free`

This workflow replaces any “header override” or viewer toggle approach.

### Script requirements (non-negotiable behavior)

`scripts/set_user_plan.py` must:
- validate plan keys strictly (`free`, `basic_paid`)
- normalize email then exact-match the stored email
- support DB override for dev/test (`--db` as path or SQLAlchemy URL)
- fail non-zero for missing user or duplicate matches (no partial updates)
- be runnable without requiring `PYTHONPATH=.`

## Consequences

### Positive
- Provides a clean way to test paid behavior without a bypass.
- Improves developer ergonomics vs manual sqlite one-liners.
- Makes the local workflow easy to document and repeat.

### Negative / Tradeoffs
- Slightly more steps than a single header flip.
- Requires developers to understand “register/login then flip plan.”

## Alternatives considered

- **Keep a dev-only header override** (rejected): security footgun, too easy to leak into prod.
- **Direct sqlite manual commands** (rejected): error-prone, not repeatable, encourages ad-hoc workflows.

## References

- README / contributing sections describing the canonical workflow
- Script: `scripts/set_user_plan.py`
- DB helpers: `apps/api/db.py`
