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
