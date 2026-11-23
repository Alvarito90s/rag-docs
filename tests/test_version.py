"""Pruebas de versión 1.0.0 (spec 073)."""

import tomllib
from pathlib import Path

import docuchat
from docuchat.api.app import create_app
from docuchat.config import Settings

ROOT = Path(__file__).resolve().parents[1]
V = "1.0.0"


def test_pyproject_matches_init() -> None:
    with (ROOT / "pyproject.toml").open("rb") as f:
        pyproject = tomllib.load(f)
    pyproject_version = pyproject["project"]["version"]
    init_version = docuchat.__version__
    assert pyproject_version == init_version == V


def test_changelog_version_line() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text()
    first_heading = next(line for line in changelog.splitlines() if line.startswith("## ["))
    assert first_heading == "## [1.0.0] - 2026-11-23"
    assert "### Añadido" in changelog


def test_app_version(settings: Settings) -> None:
    app = create_app(settings)
    assert app.version == V
