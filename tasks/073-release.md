# 073 · Versión 1.0.0 y CHANGELOG
Fase: 7 · Depende de: 072

## Objetivo
Subir la versión a 1.0.0 y crear el `CHANGELOG.md`. Así el humano puede etiquetar `v1.0.0` y publicar la release.

## Archivos
- modificar: `pyproject.toml` (solo `version`)
- modificar: `src/docuchat/__init__.py` (solo `__version__`)
- modificar: `uv.lock` (solo regenerándolo con `uv lock`, nunca a mano)
- crear: `CHANGELOG.md`
- crear: `tests/test_version.py`

## Comportamiento
1. `version = "1.0.0"` en `pyproject.toml` y `__version__ = "1.0.0"` en `src/docuchat/__init__.py`.
2. `uv lock` para que el lockfile recoja la versión nueva. Si no, la CI falla en `uv sync --locked`. `uv lock --check` debe salir con código 0.
3. `CHANGELOG.md`, contenido exacto:
```markdown
# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones según [SemVer](https://semver.org/lang/es/).

## [1.0.0] - 2026-11-23

Primera versión pública.

### Añadido
- Ingesta de PDF, DOCX, Markdown y TXT con limpieza de texto y páginas.
- Indexación incremental (hash SHA-256) en ChromaDB y registro SQLite, con autorreparación.
- Búsqueda híbrida: vectorial y BM25 fusionadas con RRF (k=60).
- Respuestas en streaming con un LLM local (oMLX) y citas `[n]` resueltas a documento y página.
- CLI: `ingest`, `search`, `ask` y `serve`.
- Web con FastAPI y HTMX: chat con Server-Sent Events, enlaces a la página citada y gestión de documentos.
- Evaluación reproducible (`eval/run_eval.py`): Hit@k, MRR, precisión de citas y rechazo correcto.
- Imagen Docker que usa el oMLX del host, y CI que la construye y la arranca.

### Problemas conocidos
- q17 de la evaluación: el modelo responde "No lo sé" aunque recupera la página correcta.
```

## Tests obligatorios
`tests/test_version.py`. NO cambies los valores esperados. Usa `tomllib` (stdlib).
1. `tomllib.load(pyproject)["project"]["version"] == docuchat.__version__ == "1.0.0"`.
2. Para `CHANGELOG.md`:
   - la primera línea que empieza por `"## ["` es `"## [1.0.0] - 2026-11-23"`;
   - el archivo contiene `"### Añadido"`.
3. `create_app(settings).version == "1.0.0"`. Prepara `settings` como en el test 4 de `tests/test_ci_workflow.py`.

## Aceptación
- [ ] `uv run pytest -q tests/test_version.py` → 3 passed
- [ ] `uv run pytest -q` pasa entero (462)
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `uv lock --check` → código 0
- [ ] (humano) Revisión final:
  - CI en verde (`check` y `docker`);
  - `docs/demo.gif` grabado y versionado;
  - la Docker probada en local (spec 070).
- [ ] (humano) Publicar la release:
  - `git tag -a v1.0.0 -m "DocuChat Local 1.0.0"` y `git push origin v1.0.0`.
  - `gh release create v1.0.0 --title "DocuChat Local 1.0.0" --notes-file <(sed -n '/## \[1.0.0\]/,$p' CHANGELOG.md)`.

## Fuera de alcance
Publicar en PyPI o en un registro de imágenes. No toques otros archivos.
