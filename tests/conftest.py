"""Fixtures compartidos para todos los tests."""

import os
from pathlib import Path

import pytest


@pytest.fixture()
def settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Devuelve una Settings limpia: borra DOCUCHAT_* y cambia al directorio temporal."""
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)

    from docuchat.config import Settings

    return Settings()
