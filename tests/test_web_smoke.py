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
    assert "Pavlonic Study Viewer" in content


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


def test_study_id_parsing_and_404_message_template() -> None:
    module_path = Path(__file__).resolve().parents[1] / "apps" / "web" / "study_id.js"
    code = f"""
      import {{ getStudyIdFromLocation }} from '{module_path.as_uri()}';
      const hashResult = getStudyIdFromLocation({{ hash: '#/study/0001', search: '' }});
      const queryResult = getStudyIdFromLocation({{ hash: '', search: '?study=0002' }});
      const defaultResult = getStudyIdFromLocation({{ hash: '', search: '' }});
      console.log(JSON.stringify({{ hashResult, queryResult, defaultResult }}));
    """

    output = _run_node_module(code)
    if output.get("skipped"):
        return

    assert output["hashResult"] == "0001"
    assert output["queryResult"] == "0002"
    assert output["defaultResult"] == "0001"

    app_js = (Path(__file__).resolve().parents[1] / "apps" / "web" / "app.js").read_text(
        encoding="utf-8"
    )
    assert "Study not found:" in app_js
    assert "hashchange" in app_js
    assert "popstate" in app_js
