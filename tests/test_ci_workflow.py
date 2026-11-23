"""Pruebas del workflow CI (spec 071)."""

import os
from pathlib import Path

import pytest

from docuchat.api.app import create_app
from docuchat.config import Settings

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github" / "workflows" / "ci.yml"


@pytest.fixture()
def ci_text() -> str:
    return CI.read_text()


# ---------- Test 1: job check completo ----------
def test_job_check_complete(ci_text: str) -> None:
    assert "uv run pytest -q" in ci_text
    assert "uv run mypy src" in ci_text
    assert "uv sync --locked" in ci_text


# ---------- Test 2: existe job docker ----------
def test_job_docker_exists(ci_text: str) -> None:
    assert "  docker:" in ci_text
    assert "needs: check" in ci_text
    assert "docker build -t docuchat:ci ." in ci_text


# ---------- Test 3: docker va después de check ----------
def test_docker_after_check(ci_text: str) -> None:
    assert ci_text.index("  check:") < ci_text.index("  docker:")


# ---------- Test 4: /api/health es ruta real de la app ----------
def test_health_is_real_route(ci_text: str, monkeypatch, tmp_path) -> None:
    _del_kwargs: dict[str, bool] = {"raise": False}
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            monkeypatch.delenv(key, **_del_kwargs)
    monkeypatch.chdir(tmp_path)
    settings = Settings(data_dir=tmp_path / "data")
    app = create_app(settings)
    assert "http://127.0.0.1:8001/api/health" in ci_text
    assert "/api/health" in set(app.openapi()["paths"])


# ---------- Test 5: sin tabuladores ----------
def test_no_tabs(ci_text: str) -> None:
    assert "\t" not in ci_text
