"""Demo data loader for the seed Study JSON.

How it works:
    - Load the demo JSON file from data/demo/study_0001.json.
    - Parse and validate it into a Study model.

How to run:
    - python -c "from packages.core.loader import load_demo_study; print(load_demo_study())"
    - make test (via tests that call the loader)

Expected output:
    - A Study instance on success.
    - ValueError with a clear message on invalid data.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Study


DEMO_STUDY_PATH = Path(__file__).resolve().parents[2] / "data" / "demo" / "study_0001.json"


def load_demo_study(path: Path | None = None) -> Study:
    """Load the demo Study JSON from disk and validate it."""
    json_path = path or DEMO_STUDY_PATH

    # Ensure the expected file exists before attempting to read it.
    if not json_path.exists():
        raise FileNotFoundError(f"Demo study JSON not found: {json_path}")

    with json_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    return Study.from_dict(data)
