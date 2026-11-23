# 055 · /files para abrir documentos y comando `serve`
Fase: 5 · Depende de: 052

## Objetivo
Servir los documentos originales (para abrir el PDF en la página citada con `#page=N`) y arrancar la app con `docuchat serve`.

## Archivos
Excepción a la regla de 3 archivos: los cambios en `app.py` y `cli.py` son de pocas líneas.
- crear: `src/docuchat/api/routes_web.py`
- modificar: `src/docuchat/api/app.py` (solo incluir el router web en `create_app`)
- modificar: `src/docuchat/cli.py` (solo AÑADIR el comando `serve` y sus imports)
- crear: `tests/api/test_files.py`
- modificar: `tests/test_cli.py` (solo AÑADIR tests)

## Interfaz
`src/docuchat/api/routes_web.py`:
```python
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from docuchat.api.app import ServicesDep
from docuchat.ingest.scanner import is_supported

router = APIRouter()


def resolve_document(root: Path, source: str) -> Path | None:
    """Ruta del documento source dentro de root, o None si sale de root, no existe o no es soportado."""


@router.get("/files/{source:path}")
def get_file(source: str, services: ServicesDep) -> FileResponse: ...
```
`src/docuchat/cli.py`:
```python
import uvicorn

from docuchat.api.app import create_app


@app.command()
def serve(
    host: Annotated[str | None, typer.Option("--host", help="Por defecto DOCUCHAT_API_HOST.")] = None,
    port: Annotated[int | None, typer.Option("--port", help="Por defecto DOCUCHAT_API_PORT.")] = None,
) -> None:
    """Arranca la app web."""
```

## Comportamiento
1. `resolve_document`: `base = root.resolve()`; `path = (base / source).resolve()`; devuelve `path` solo si `path.is_relative_to(base)`, `path.is_file()` y `is_supported(path)`. Si no, `None`. Esto bloquea `../` y enlaces fuera de la carpeta.
2. `GET /files/{source:path}`: `resolve_document(settings.documents_dir, source)`; `None` → `HTTPException(404, "Documento no encontrado")`. Si no → `FileResponse(path)` SIN `filename` (así el navegador lo abre en línea y el visor de PDF respeta `#page=N`).
3. `create_app`: añade `app.include_router(web_router)` (import dentro de la función, como el de la API).
4. `serve`: `settings = get_settings()`; `h = host or settings.api_host`; `p = port or settings.api_port`. `create_app(settings)`; `EmbeddingModelMismatchError` → `str(e)` por stderr, exit 1. Imprime `f"DocuChat en http://{h}:{p}"` y llama a `uvicorn.run(app, host=h, port=p)`.

## Tests obligatorios
`tests/api/test_files.py` (fixtures de `conftest.py`). NO cambies los valores esperados.
1. `GET /files/manual_cafetera.pdf` → 200, `content-type == "application/pdf"`, el cuerpo empieza por `b"%PDF"`, y la cabecera `content-disposition` NO existe o no contiene `"attachment"`.
2. `GET /files/apuntes_redes.md` → 200 y `"Modelo OSI" in response.text`.
3. Inexistente: `GET /files/nada.pdf` → 404 y `detail == "Documento no encontrado"`.
4. Fuera de la carpeta (parametrizado, 2 casos): `GET /files/../data/x.pdf` y `GET /files/%2E%2E/%2E%2E/etc/passwd` → 404.
5. No soportado: crea `docs / "nota.exe"` → `GET /files/nota.exe` → 404.
6. `resolve_document(tmp_path, "../x.pdf") is None`; con `tmp_path / "a.pdf"` creado → `resolve_document(tmp_path, "a.pdf") == (tmp_path / "a.pdf").resolve()`.

Añadir a `tests/test_cli.py`:
36. `test_36_serve`: `calls = []`; `monkeypatch.setattr("uvicorn.run", lambda app, host, port: calls.append((host, port)))`; con el entorno limpio de `index_env` y `serve --port 9123` → exit 0, `calls == [("127.0.0.1", 9123)]`, salida contiene `"DocuChat en http://127.0.0.1:9123"`.
37. `test_37_serve_model_mismatch`: `ingest SAMPLES`; env `DOCUCHAT_EMBEDDING_MODEL=otro` y `get_settings.cache_clear()`; `serve` → exit 1, `"Reindexa con --reset"`, y `uvicorn.run` no se llama.

## Aceptación
- [ ] `uv run pytest -q tests/api/test_files.py` → 7 passed; `uv run pytest -q tests/test_cli.py` → 36 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] (humano) `uv run docuchat serve` y abrir `http://127.0.0.1:8001/files/manual_cafetera.pdf#page=7` → el PDF se abre en la página 7; `http://127.0.0.1:8001/docs` muestra la API

## Fuera de alcance
Páginas HTML (056, 057). No cambies los endpoints de `/api`.
