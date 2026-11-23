# 070 · Imagen Docker y compose
Fase: 7 · Depende de: 064-b

## Objetivo
Empaquetar la app (no los modelos) en una imagen Docker que use el oMLX del host a través de `host.docker.internal`. Arrancarla con `docker compose up --build`.

## Archivos
- crear: `Dockerfile`
- crear: `.dockerignore`
- crear: `compose.yaml`
- crear: `tests/test_docker_files.py`

## Contenido exacto
Copia estos tres archivos tal cual; no cambies versiones, rutas ni orden.

`Dockerfile`:
```dockerfile
# DocuChat en contenedor. Los modelos NO van dentro (MLX necesita Metal): se usa el oMLX del host.
FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencias primero: esta capa solo se reconstruye si cambia uv.lock.
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN uv sync --locked --no-dev --no-editable

ENV PATH="/app/.venv/bin:$PATH" \
    DOCUCHAT_API_HOST=0.0.0.0 \
    DOCUCHAT_API_PORT=8001 \
    DOCUCHAT_DOCUMENTS_DIR=/documents \
    DOCUCHAT_DATA_DIR=/data \
    DOCUCHAT_LLM_BASE_URL=http://host.docker.internal:8000/v1 \
    DOCUCHAT_EMBEDDING_BASE_URL=http://host.docker.internal:8000/v1

RUN useradd --create-home --uid 1000 docuchat \
    && mkdir -p /data /documents \
    && chown docuchat /data
USER docuchat

EXPOSE 8001
CMD ["docuchat", "serve"]
```

`.dockerignore`:
```
.env
.env.*
.git
.github
.claude
.venv
.mypy_cache
.pytest_cache
.ruff_cache
**/__pycache__
**/.DS_Store
data
docs
eval
reports
samples
scripts
tasks
tests
```

`compose.yaml`:
```yaml
services:
  docuchat:
    build: .
    image: docuchat:local
    ports:
      - "127.0.0.1:8001:8001"
    env_file:
      - path: .env
        required: false
    # environment gana a env_file: las rutas y URLs del .env local no valen dentro del contenedor.
    environment:
      DOCUCHAT_API_HOST: 0.0.0.0
      DOCUCHAT_DOCUMENTS_DIR: /documents
      DOCUCHAT_DATA_DIR: /data
      DOCUCHAT_LLM_BASE_URL: http://host.docker.internal:8000/v1
      DOCUCHAT_EMBEDDING_BASE_URL: http://host.docker.internal:8000/v1
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - ./samples:/documents:ro
      - docuchat-data:/data
    restart: unless-stopped

volumes:
  docuchat-data:
```

## Por qué así (lo ha comprobado el cerebro)
- `ghcr.io/astral-sh/uv:0.13.9` y `python:3.12-slim-bookworm` existen. El wheel que genera `uv build` incluye `templates/`, `static/` y `static/vendor/htmx.min.js`, así que `--no-editable` funciona.
- `docuchat serve` arranca y `/api/health` responde 200 sin oMLX, así que la CI (spec 071) puede probar la imagen.
- La clave entra en tiempo de ejecución desde `.env` (`env_file`) y nunca se copia a la imagen.

## Comportamiento
No hay código Python nuevo. Los tests comprueban el texto de los tres archivos; nada de YAML ni de `docker` en los tests (ni `pyyaml` ni dependencias nuevas).

## Tests obligatorios
`tests/test_docker_files.py`. NO cambies los valores esperados. `ROOT = Path(__file__).resolve().parents[1]`. Helper `env_names(text: str) -> set[str]` que devuelve los nombres que captura `re.findall(r"DOCUCHAT_([A-Z_]+)", text)` en minúsculas.
1. `.dockerignore`: el conjunto de sus líneas (con `strip`, sin vacías) contiene `.env`, `.env.*`, `.venv`, `data` y `.git`.
2. `Dockerfile`:
   - ninguna línea que empiece por `COPY` contiene `.env`;
   - no contiene `"COPY . ."`;
   - contiene `"DOCUCHAT_API_HOST=0.0.0.0"` y `"USER docuchat"`.
3. `Dockerfile` fija la versión de uv: `re.search(r"ghcr\.io/astral-sh/uv:\d+\.\d+\.\d+ ", text)` no es `None`.
4. Parametrizado (`Dockerfile`, `compose.yaml`): `env_names(text)` no está vacío y es subconjunto de `set(Settings.model_fields)`. Así se detecta una variable mal escrita.
5. `compose.yaml` contiene `'"127.0.0.1:8001:8001"'`, `'"host.docker.internal:host-gateway"'`, `"required: false"` y `"./samples:/documents:ro"`.
6. Las URL de los modelos de `Dockerfile` y de `compose.yaml` coinciden:
   - en ambos aparece `http://host.docker.internal:8000/v1` exactamente 2 veces;
   - ninguno contiene `127.0.0.1:8000`.

## Aceptación
- [ ] `uv run pytest -q tests/test_docker_files.py` → 7 passed
- [ ] `uv run pytest -q` pasa entero (447)
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] (humano, con Docker Desktop y oMLX arrancado) `docker compose up --build`:
  - `curl -s http://127.0.0.1:8001/api/health` devuelve `"status":"ok"`;
  - en `/documents`, reindexar da 7 documentos;
  - una pregunta en el chat responde con citas.
  - Si no conecta con oMLX, comprueba con el comando de diagnóstico del README.
- [ ] (humano) `docker compose down`

## Fuera de alcance
CI (071), README (072). No toques `src/` ni `pyproject.toml`. El ejecutor no tiene Docker: no intentes construir la imagen; anótalo en el informe.
