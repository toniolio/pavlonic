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
    assert "data-dev-sitemap" in content
    assert 'id="account-panel"' in content
    assert 'id="auth-logged-out"' in content
    assert 'id="auth-logged-in"' in content
    assert 'id="auth-email"' in content
    assert 'id="auth-password"' in content
    assert 'id="auth-login"' in content
    assert 'id="auth-register"' in content
    assert 'id="auth-logout"' in content
    assert 'id="auth-status"' in content
    assert "<title>" in content
    assert 'name="description"' in content
    assert 'property="og:title"' in content


def test_web_app_has_auth_wiring_and_no_dev_override_header() -> None:
    app_js = (Path(__file__).resolve().parents[1] / "apps" / "web" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "pavlonic_access_token" in app_js
    assert "Authorization" in app_js
    assert "Bearer ${accessToken}" in app_js
    assert "/v1/auth/me" in app_js
    assert "auth-login" in app_js
    assert "auth-register" in app_js
    assert "auth-logout" in app_js
    assert "X-Pavlonic-Entitlement" not in app_js
    assert "data-dev-entitlement-toggle" not in app_js


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


def test_study_deep_link_targeting_markers() -> None:
    module_path = Path(__file__).resolve().parents[1] / "apps" / "web" / "results_renderer.js"
    route_module = Path(__file__).resolve().parents[1] / "apps" / "web" / "study_id.js"
    study_json = (Path(__file__).resolve().parents[1] / "data" / "demo" / "study_0001.json").read_text(
        encoding="utf-8"
    )

    code = f"""
      import {{ getRouteFromLocation }} from '{route_module.as_uri()}';
      import {{ renderStudyResultsHtml }} from '{module_path.as_uri()}';
      const route = getRouteFromLocation({{ hash: '#/studies/0001?result=R1', search: '' }});
      const study = {study_json};
      const html = renderStudyResultsHtml(study, route.resultId);
      console.log(JSON.stringify({{ html, route }}));
    """

    output = _run_node_module(code)
    if output.get("skipped"):
        return

    html = output["html"]
    assert output["route"]["resultId"] == "R1"
    assert 'id="result-R1"' in html
    assert 'data-result-targeted="true"' in html
    assert 'data-result-row="true"' in html
    assert 'data-result-toggle="true"' in html
    assert 'data-result-detail="true"' in html
