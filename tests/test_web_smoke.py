"""Smoke test for the static web viewer HTML."""

from pathlib import Path


def test_web_index_exists_and_has_marker() -> None:
    html_path = Path(__file__).resolve().parents[1] / "apps" / "web" / "index.html"

    assert html_path.exists()

    content = html_path.read_text(encoding="utf-8")
    assert "Pavlonic Study Viewer" in content
