#!/usr/bin/env python
"""Public specs export stub.

Purpose:
    Provide a public-safe, manual export workflow for specs while verifying the
    public specs README is present in the repository.

What it validates:
    - The public specs README exists at docs/specs/README.md.
    - The local private specs directory (docs-private/) exists, but only warns
      if it is missing.

Expected output:
    - Always prints a short, numbered manual export checklist.
    - Prints either a success message or a clear warning/error summary.

Failure conditions:
    - Exits with status 1 if docs/specs/README.md is missing.
    - Never fails due to a missing docs-private/ directory.
    - Exits with status 0 when required public docs are present.

How it works:
    - Resolve the repo root from this file location.
    - Check for docs/specs/README.md (required).
    - Check for docs-private/ (warn if missing).

How to run:
    - make specs
    - python scripts/spec_export_stub.py

Expected output (success):
    Public specs export (manual for now)
    1) Update canonical docs in docs-private/ (DOCX or source format)
    2) Export to Markdown using your preferred tool
    3) Sanitize the Markdown for public release
    4) Save the sanitized Markdown into docs/specs/

    Public specs README is present.
    All checks completed.
"""

from __future__ import annotations

from pathlib import Path


# Resolve paths once so validation and messaging are consistent.
REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_PRIVATE = REPO_ROOT / "docs-private"
DOCS_SPECS = REPO_ROOT / "docs" / "specs"
PUBLIC_SPECS_README = DOCS_SPECS / "README.md"


def main() -> int:
    """Print export instructions and validate public spec docs."""
    print("Public specs export (manual for now)")
    print("1) Update canonical docs in docs-private/ (DOCX or source format)")
    print("2) Export to Markdown using your preferred tool")
    print("3) Sanitize the Markdown for public release")
    print("4) Save the sanitized Markdown into docs/specs/")

    # README must exist to anchor the public-safe workflow.
    if not PUBLIC_SPECS_README.exists():
        print("\nERROR: docs/specs/README.md is missing.")
        print("Create it to document the public-safe specs workflow.")
        return 1

    # Private specs are expected locally, but absence should not fail CI.
    if not DOCS_PRIVATE.exists():
        print("\nWARNING: docs-private/ not found.")
        print("Create it locally to store canonical private specs.")
    else:
        print("\nPrivate specs directory is present.")

    print("Public specs README is present.")
    print("All checks completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
