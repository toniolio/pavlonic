"""Demo data loader for the seed Study JSON.

How it works:
    - Resolve a demo study path from either:
      - no argument (defaults to study_0001.json), or
      - a study id string (e.g., "0001"), or
      - an explicit file path string/Path.
    - Load the JSON and validate it into a Study model.

How to run:
    - python -c "from packages.core.loader import load_demo_study; print(load_demo_study())"
    - python -c "from packages.core.loader import load_demo_study; print(load_demo_study('0001'))"
    - make test (via tests that call the loader)

Expected output:
    - A Study instance on success.
    - ValueError with a clear message on invalid data.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Study


DEMO_STUDY_DIR = Path(__file__).resolve().parents[2] / "data" / "demo"
DEFAULT_STUDY_ID = "0001"
DEFAULT_STUDY_PATH = DEMO_STUDY_DIR / f"study_{DEFAULT_STUDY_ID}.json"


def _resolve_demo_path(path: str | Path | None) -> Path:
    """Resolve a demo study file path from an id, path, or default."""
    if path is None:
        return DEFAULT_STUDY_PATH

    if isinstance(path, Path):
        return path

    # Treat bare strings without a file suffix as study IDs.
    if "." not in path and "/" not in path and "\\" not in path:
        return DEMO_STUDY_DIR / f"study_{path}.json"

    return Path(path)


def load_demo_study(path: str | Path | None = None) -> Study:
    """Load the demo Study JSON from disk and validate it."""
    json_path = _resolve_demo_path(path)

    # Ensure the expected file exists before attempting to read it.
    if not json_path.exists():
        raise FileNotFoundError(f"Demo study JSON not found: {json_path}")

    with json_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    return Study.from_dict(data)
