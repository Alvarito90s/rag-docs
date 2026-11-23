# Informe 070 · Imagen Docker y compose
Estado: COMPLETADA

## Cambios
- `Dockerfile`: imagen con Python 3.12-slim, uv 0.13.9 como builder, vars de entorno oMLX vía host.docker.internal, usuario no-root `docuchat`.
- `.dockerignore`: excluye .env, .git, .venv, cachés y carpetas de desarrollo.
- `compose.yaml`: servicio `docuchat` con puertos mapeados a 127.0.0.1:8001, volúmenes para samples y datos persistentes, extra_hosts para host.docker.internal.
- `tests/test_docker_files.py`: 7 tests que validan contenido de los 3 archivos.

## Verificación
- `uv run pytest -q tests/test_docker_files.py` → **7 passed**
- `uv run pytest -q` → **447 passed**, 5 warnings (preexistentes, SwigPyPacked)
- `uv run ruff check .` → All checks passed
- `uv run ruff format --check .` → 147 files already formatted
- `uv run mypy src` → Success: no issues found in 37 source files

## Decisiones que tomé
- Ninguna: todos los archivos se copiaron tal cual de la spec. El único ajuste fue el `import re` al inicio del archivo de tests para satisfacer ruff E402.

## Bloqueos y dudas
- **No se construyó la imagen Docker**: el entorno no dispone de Docker Desktop. La aceptación humana (docker compose up --build, curl al health endpoint, reindexación y consulta) corresponde al humano según la spec ("Fuera de alcance: el ejecutor no tiene Docker: no intentes construir la imagen; anótalo en el informe").
