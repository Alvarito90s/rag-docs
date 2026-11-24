# DocuChat Local

App RAG 100 % local: indexa documentos (PDF, DOCX, MD, TXT) y responde
preguntas con citas [documento, página] usando un LLM local.

## Tu papel: ejecutor
Eres el agente que IMPLEMENTA. Las decisiones de diseño ya están tomadas
en las specs de tasks/. No rediseñes, no añadas funcionalidades que no
pida la spec y no cambies interfaces definidas en ella.
Si la spec es ambigua o imposible, NO improvises: para y explícalo en
el informe, en "Bloqueos".

## Cómo trabajar una tarea
1. Lee la spec completa (tasks/NNN-nombre.md) y los archivos que cita.
2. Implementa solo lo que pide, en los archivos que indica.
3. Ejecuta tests, ruff y mypy. Corrige y repite hasta que pasen
   (máximo 3 intentos por error; si sigue fallando, para).
4. Actualiza docs/STATE.md (módulos, qué funciona, qué falta).
5. Escribe reports/NNN-nombre.md con la plantilla de reports/_TEMPLATE.md.
6. No hagas commit: lo hace el humano tras la revisión.

Con varias specs ("ejecuta tasks/010 a 014"): en orden, un informe por
tarea; si una queda bloqueada, para la cadena.

## Stack (no añadas dependencias que la spec no autorice)
- Python 3.12, gestor uv
- FastAPI, Jinja2 + HTMX (sin frameworks JS)
- ChromaDB persistente, SQLite (stdlib sqlite3) con FTS5 para BM25
- PyMuPDF, python-docx, Typer, rich, pydantic-settings
- Servidor de modelos: oMLX local (API compatible con OpenAI, exige API key)
- Cliente LLM y embeddings: librería `openai` con base_url configurable
- Cliente del reranker: `httpx` (la librería `openai` no tiene endpoint de rerank)
- PROHIBIDO: LangChain, LlamaIndex, Haystack

## Estructura
```
src/docuchat/
  config.py        # Settings (pydantic-settings, prefijo DOCUCHAT_)
  models.py        # Document, Page, Chunk, SearchResult
  ingest/          # loaders por formato + scanner de carpetas
  index/           # chunker, embeddings, vector_store, bm25, registry
  retrieval/       # vector, bm25, fusion (RRF)
  generation/      # llm_client, prompts, citations
  api/             # app FastAPI, routers, templates/, static/
  cli.py           # comandos Typer: ingest, search, ask, serve
tests/             # espejo de src/, fixtures en tests/fixtures/
scripts/           # utilidades: check_env.py, make_samples.py
samples/           # documentos de prueba (generados por make_samples.py)
eval/              # questions.jsonl, run_eval.py, results.md
tasks/             # specs del cerebro (solo lectura para ti)
reports/           # tus informes, uno por spec
docs/STATE.md      # estado del proyecto, lo mantienes tú
```

## Comandos
- Instalar: `uv sync`
- Tests: `uv run pytest -q`
- Lint: `uv run ruff check . && uv run ruff format --check .`
- Tipos: `uv run mypy src`
- Entorno: `uv run python scripts/check_env.py`
- App: `uv run docuchat serve`

## Reglas de código
1. Toda función nueva lleva type hints y al menos un test.
2. Archivos de menos de 300 líneas.
3. Los tests NO llaman al servidor de modelos real (oMLX): usa mocks/fakes.
4. Nada de configuración hardcodeada: todo pasa por config.py.
5. Si no sabes cómo funciona una API de librería, dilo en el informe;
   no la inventes.
6. Nunca leas ni escribas `.env` ni `~/.omlx/`: contienen la clave del humano.
7. Los tests que da la spec son el contrato: NO cambies sus valores esperados
   para que pasen. Si crees que un test de la spec está mal, para y explícalo
   en "Bloqueos".
8. Nunca edites archivos de tasks/.

## Decisiones tomadas (las añade el humano)
- Chunk por defecto: 800 caracteres, 120 de solape.
- Fusión híbrida: RRF con k=60.
- Citas en el texto como [n]; se resuelven a documento+página en citations.py.
- Reranker: `Qwen3-Reranker-0.6B-4bit` vía `POST /v1/rerank` de oMLX (puerta H2).
  Su respuesta real está en tests/fixtures/rerank_response.json: no la modifiques.
- Rerank activo por defecto con 10 candidatos (puerta H3): Hit@1 híbrido 0.643 → 0.771
  con +0.23 s por búsqueda. Los tests nunca usan el reranker real (fixture en tests/conftest.py).
- Contexto de metadatos activo por defecto (puerta H5, spec 113): «Documento «fuente». Primera frase.»,
  sin LLM. Hit@1 híbrido v2 0.771 → 0.929 e implícitas 0.2 → 1.0, con 0 s de ingesta extra; mejor que el
  contexto con LLM por chunk (0.900–0.914, unas 40 veces más lento), que queda opcional y apagado.
