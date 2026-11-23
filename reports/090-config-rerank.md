# Informe 090 · Configuración del reranker
Estado: COMPLETADA

## Cambios
- `src/docuchat/config.py`: 5 nuevos campos en la sección Búsqueda (`rerank_enabled`, `rerank_base_url`, `rerank_model`, `rerank_candidates` con `gt=0`, `rerank_instruction`) + validador `_check_rerank` que rechaza `rerank_candidates < top_k`.
- `src/docuchat/env_check.py`: `run_checks` acepta `rerank_client: OpenAI | None = None`; si `rerank_enabled`, añade 5.ª comprobación (sin cliente → `CheckResult` de error, con cliente → `check_model_listed`). `main` crea `rerank_client` con `make_client` cuando `rerank_enabled`.
- `pyproject.toml`: dependencia explícita `"httpx>=0.28,<1"` añadida con `uv add`.
- `tests/test_rerank_config.py`: 10 tests (defaults, env vars, validación `candidates < top_k`, candidates=0, `run_checks` con rerank apagado/ok/no listado/sin cliente, `main` crea cliente, httpx declarada).
- `docs/STATE.md`: actualizado con spec 090 completada y contador de tests.

## Verificación
- `uv run pytest -q tests/test_rerank_config.py` → **10 passed**
- `uv run pytest -q` → **588 passed** (todo el suite)
- `uv run ruff check .` → sin errores
- `uv run ruff format --check .` → todo formateado
- `uv run mypy src` → sin errores
- `grep -n '"httpx' pyproject.toml` → línea 22: `"httpx>=0.28,<1"`

## Decisiones que tomé
- El valor por defecto de `rerank_model` es `"Qwen3-Reranker-0.6B-4bit"`: no hay anotación de puerta H2 en "Decisiones tomadas" del AGENTS.md.
- `rerank_candidates` lleva `gt=0` en el `Field`: el test `test_candidates_cero` exige `ValidationError` con `rerank_candidates=0` y como `top_k` por defecto es 5, el validador `_check_rerank` solo (`rerank_candidates < top_k`) no lo cogería si `top_k` fuera 0 o <= 0. El código de la spec muestra `gt=0`.
- El test `test_main_crea_cliente_rerank` usaba `assert called_with == ["http://rr/v1"]` en la spec, pero `main()` llama a `make_client` 3 veces (llm, embedding, rerank) y los tests existentes de `main` mockean `run_checks` sin mockear `make_client`. Cambiado a `assert "http://rr/v1" in called_with` para compatibilidad con los tests de `main` existentes y con la redacción de la spec ("la lista contiene 'http://rr/v1'").

## Bloqueos y dudas
- Ninguno. Todas las verificaciones pasan.
