#!/usr/bin/env python
"""Public specs export stub.

Purpose:
    Provide a public-safe, manual export workflow for specs while ensuring the
    expected public placeholders exist in the repository.

What it validates:
    - The local private specs directory (docs-private/) exists.
    - Each required public mirror placeholder exists in docs/specs/.

Expected output:
    - Always prints a short, numbered manual export checklist.
    - Prints either a success message or a specific error summary.

Failure conditions:
    - Exits with status 1 if docs-private/ is missing.
    - Exits with status 1 if any required public spec placeholder is missing.
    - Exits with status 0 only when all validations pass.

How it works:
    - Resolve the repo root from this file location.
    - Check for docs-private/.
    - Check for all required docs/specs/*.md placeholder files.

How to run:
    - make specs
    - python scripts/spec_export_stub.py

Expected output (success):
    Public specs export (manual for now)
    1) Update canonical docs in docs-private/ (DOCX or source format)
    2) Export to Markdown using your preferred tool
    3) Sanitize the Markdown for public release
    4) Save the sanitized Markdown into docs/specs/

    All public spec placeholders are present.
"""

from __future__ import annotations

from pathlib import Path


# Resolve paths once so validation and messaging are consistent.
REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_PRIVATE = REPO_ROOT / "docs-private"
DOCS_SPECS = REPO_ROOT / "docs" / "specs"

# Placeholder files expected to exist as public mirrors.
REQUIRED_PUBLIC_SPECS = (
    "data-model.md",
    "front-end-spec.md",
    "evidence-synthesis-weighting.md",
    "content-ops-playbook.md",
    "identity-entitlements-seo.md",
)


def main() -> int:
    """Print export instructions and validate public spec placeholders."""
    print("Public specs export (manual for now)")
    print("1) Update canonical docs in docs-private/ (DOCX or source format)")
    print("2) Export to Markdown using your preferred tool")
    print("3) Sanitize the Markdown for public release")
    print("4) Save the sanitized Markdown into docs/specs/")

    # Private specs must exist locally but are never committed.
    if not DOCS_PRIVATE.exists():
        print("\nERROR: docs-private/ not found. Create it locally for private specs.")
        return 1

    # Ensure all public placeholders exist to prevent partial exports.
    missing = [name for name in REQUIRED_PUBLIC_SPECS if not (DOCS_SPECS / name).exists()]
    if missing:
        print("\nERROR: Missing public spec placeholders:")
        for name in missing:
            print(f"- {DOCS_SPECS / name}")
        return 1

    print("\nAll public spec placeholders are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
