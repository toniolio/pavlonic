#!/usr/bin/env python
"""Public specs export stub.

This script verifies public-safe placeholders exist and prints a manual
export workflow for now.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_PRIVATE = REPO_ROOT / "docs-private"
DOCS_SPECS = REPO_ROOT / "docs" / "specs"

REQUIRED_PUBLIC_SPECS = (
    "data-model.md",
    "front-end-spec.md",
    "evidence-synthesis-weighting.md",
    "content-ops-playbook.md",
    "identity-entitlements-seo.md",
)


def main() -> int:
    print("Public specs export (manual for now)")
    print("1) Update canonical docs in docs-private/ (DOCX or source format)")
    print("2) Export to Markdown using your preferred tool")
    print("3) Sanitize the Markdown for public release")
    print("4) Save the sanitized Markdown into docs/specs/")

    if not DOCS_PRIVATE.exists():
        print("\nERROR: docs-private/ not found. Create it locally for private specs.")
        return 1

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
