"""Pruebas de contenido del README (spec 072, 074).

Ningún test llama a oMLX.
"""

import os
import re
from pathlib import Path

import typer

from docuchat.api.app import create_app
from docuchat.cli import app
from docuchat.config import Settings

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text("utf-8")
README_EN = (ROOT / "README.en.md").read_text("utf-8")
RESULTS = (ROOT / "eval" / "results.md").read_text("utf-8")
PENDIENTES = {"docs/demo.gif"}


# ---------- Test 1: copia exacta ----------
def test_1_exact_copy() -> None:
    """Los bytes de README.md son iguales a los de tasks/assets/074/README.md."""
    assert (ROOT / "README.md").read_bytes() == (
        ROOT / "tasks" / "assets" / "074" / "README.md"
    ).read_bytes()


# ---------- Test 2: tabla de recuperación al día ----------
def test_2_recovery_table() -> None:
    """Las 9 líneas de resultados de recuperación están en README."""
    results_lines = RESULTS.splitlines()
    matching = [line for line in results_lines if re.match(r"\| (500|800|1200) \|", line)]
    assert len(matching) == 9, f"Se esperaban 9 líneas, se encontraron {len(matching)}"
    for line in matching:
        assert line in README, f"Falta en README: {line}"


# ---------- Test 3: tabla de generación al día ----------
def test_3_generation_table() -> None:
    """Las líneas de resultados de generación están en README."""
    lines = RESULTS.splitlines()
    header = "| Métrica | Valor |"
    start = None
    for i, line in enumerate(lines):
        if line.strip() == header:
            start = i + 1
            break
    assert start is not None, f"No se encontró cabecera de generación: {header!r}"
    generation = []
    for line in lines[start:]:
        if line.strip() == "":
            break
        generation.append(line)
    for line in generation:
        assert line in README, f"Falta en README: {line}"


# ---------- Test 4: comandos reales ----------
def test_4_real_commands() -> None:
    """El conjunto de comandos del README coincide con los de la CLI."""
    found = set(re.findall(r"(?:uv run )docuchat ([a-z]+)|`docuchat ([a-zA-Z0-9_-]+)", README))
    commands = {c for pair in found for c in pair if c}
    # También los backtick solos (sin alternación por los espacios en "search "TEXTO"`)
    found2 = set(re.findall(r"`docuchat ([a-zA-Z0-9_-]+)", README))
    commands.update(c for c in found2 if c.isalpha() and c in "ingest search ask serve")
    assert commands == {"ingest", "search", "ask", "serve"}, f"Comandos: {commands}"
    cmd = typer.main.get_command(app)
    cli_commands = set(cmd.commands)
    assert commands.issubset(cli_commands), f"Faltan en CLI: {commands - cli_commands}"


# ---------- Test 5: enlaces locales ----------
def test_5_local_links() -> None:
    """Todos los enlaces locales existen, salvo los PENDIENTES."""
    links = re.findall(r"\]\(([^)#\s]+)\)", README)
    local_links = [line for line in links if not line.startswith("http")]
    for link in local_links:
        if link not in PENDIENTES:
            assert (ROOT / link).exists(), f"Enlace roto: {link}"
    assert len(local_links) - len(PENDIENTES & set(local_links)) >= 9


# ---------- Test 6: variables reales ----------
def test_6_real_variables() -> None:
    """Las DOCUCHAT_ del README son subconjunto de Settings."""
    readme_vars = set(re.findall(r"DOCUCHAT_([A-Z_]+)", README))
    settings_vars = set(Settings.model_fields)
    readme_as_snake = {v.lower() for v in readme_vars}
    assert readme_as_snake.issubset(settings_vars), (
        f"Variables fuera de Settings: {readme_as_snake - settings_vars}"
    )
    assert len(readme_vars) >= 8, f"Solo {len(readme_vars)} variables distintas"


# ---------- Test 7: rutas de la API reales ----------
def test_7_real_api_routes(monkeypatch, tmp_path) -> None:
    """Las 7 rutas de la API en README están en la app."""
    _del_kwargs: dict[str, bool] = {"raise": False}
    for key in list(os.environ):
        if key.startswith("DOCUCHAT_"):
            monkeypatch.delenv(key, **_del_kwargs)
    monkeypatch.chdir(tmp_path)
    settings = Settings(data_dir=tmp_path / "data")
    app_instance = create_app(settings)
    api_paths = set(app_instance.openapi()["paths"])
    routes = []
    for line in README.splitlines():
        m = re.match(r"\| (?:GET|POST) \| (`[^`]+`)", line)
        if m:
            route = m.group(1).strip("`")
            routes.append(route)
    assert len(routes) == 7, f"Se esperaban 7 rutas, se encontraron {len(routes)}: {routes}"
    for route in routes:
        assert route in api_paths, f"Ruta no encontrada: {route}"


# ---------- Test 8: copia exacta del inglés ----------
def test_8_exact_copy_en() -> None:
    """Los bytes de README.en.md son iguales a los de tasks/assets/074/README.en.md."""
    assert (ROOT / "README.en.md").read_bytes() == (
        ROOT / "tasks" / "assets" / "074" / "README.en.md"
    ).read_bytes()


# ---------- Test 9: inglés al día ----------
def test_9_english_up_to_date() -> None:
    """El README en inglés está actualizado con los resultados."""
    # Las 9 filas de recuperación están en README_EN
    results_lines = RESULTS.splitlines()
    matching = [line for line in results_lines if re.match(r"\| (500|800|1200) \|", line)]
    assert len(matching) == 9, f"Se esperaban 9 líneas, se encontraron {len(matching)}"
    for line in matching:
        assert line in README_EN, f"Falta en README_EN: {line}"

    # Palabras clave, precisión de citas, falsos rechazos
    assert "| Keyword accuracy | 1.000 |" in README_EN
    assert "| Citation precision | 0.971 |" in README_EN
    assert "| False refusals | 0 |" in README_EN

    # Enlaces locales existen (misma regla que test 5)
    links = re.findall(r"\]\(([^)#\s]+)\)", README_EN)
    local_links = [line for line in links if not line.startswith("http")]
    for link in local_links:
        if link not in PENDIENTES:
            assert (ROOT / link).exists(), f"Enlace roto en inglés: {link}"

    # Los dos README se enlazan entre sí
    assert "[English](README.en.md)" in README
    assert "[Español](README.md)" in README_EN
