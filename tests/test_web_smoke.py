"""Smoke tests for the static web viewer HTML and JS helpers."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def test_web_index_exists_and_has_marker() -> None:
    html_path = Path(__file__).resolve().parents[1] / "apps" / "web" / "index.html"

    assert html_path.exists()

    content = html_path.read_text(encoding="utf-8")
    assert "Pavlonic Viewer" in content
    assert "data-evidence-table-container" in content


def _run_node_module(code: str) -> dict:
    node = shutil.which("node")
    if not node:
        return {"skipped": True, "reason": "node not installed"}

    result = subprocess.run(
        [node, "--input-type=module", "-e", code],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)

    return json.loads(result.stdout)


def test_route_parsing_and_error_message_template() -> None:
    module_path = Path(__file__).resolve().parents[1] / "apps" / "web" / "study_id.js"
    code = f"""
      import {{ getRouteFromLocation, getStudyIdFromLocation }} from '{module_path.as_uri()}';
      const techniqueRoute = getRouteFromLocation({{ hash: '#/techniques/spaced-practice', search: '' }});
      const studyRoute = getRouteFromLocation({{ hash: '#/studies/0001?result=R1', search: '' }});
      const legacyHashRoute = getRouteFromLocation({{ hash: '#/study/0002', search: '' }});
      const legacyQueryRoute = getRouteFromLocation({{ hash: '', search: '?study=0003' }});
      const defaultRoute = getRouteFromLocation({{ hash: '', search: '' }});
      const studyId = getStudyIdFromLocation({{ hash: '#/studies/0005', search: '' }});
      console.log(JSON.stringify({{ techniqueRoute, studyRoute, legacyHashRoute, legacyQueryRoute, defaultRoute, studyId }}));
    """

    output = _run_node_module(code)
    if output.get("skipped"):
        return

    assert output["techniqueRoute"] == {
        "page": "technique",
        "id": "spaced-practice",
        "resultId": None,
    }
    assert output["studyRoute"] == {"page": "study", "id": "0001", "resultId": "R1"}
    assert output["legacyHashRoute"] == {"page": "study", "id": "0002", "resultId": None}
    assert output["legacyQueryRoute"] == {"page": "study", "id": "0003", "resultId": None}
    assert output["defaultRoute"] == {"page": "study", "id": "0001", "resultId": None}
    assert output["studyId"] == "0005"

    app_js = (Path(__file__).resolve().parents[1] / "apps" / "web" / "app.js").read_text(
        encoding="utf-8"
    )
    assert "Study not found:" in app_js
    assert "Technique not found:" in app_js
    assert "data-evidence-toggle" in app_js
    assert "data-evidence-row" in app_js
    assert "aria-expanded" in app_js
    assert "aria-controls" in app_js
    assert "hashchange" in app_js
    assert "popstate" in app_js
