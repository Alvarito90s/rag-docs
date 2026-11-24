# DocuChat Local

[![CI](https://github.com/Alvarito90s/RAG-Docs/actions/workflows/ci.yml/badge.svg)](https://github.com/Alvarito90s/RAG-Docs/actions/workflows/ci.yml)

**Español** · [English](README.en.md)

Pregunta a tus documentos sin que salgan de tu ordenador. DocuChat responde con citas `[n]` que enlazan a la página exacta del documento, y dice "No lo sé" cuando la respuesta no está.

![Demo: pregunta, respuesta en streaming y cita que abre el PDF en la página](docs/demo.gif)

## Qué hace

- Indexa PDF, DOCX, Markdown y TXT de una carpeta. La indexación es incremental: solo reprocesa lo que ha cambiado.
- Búsqueda híbrida: vectorial (ChromaDB) y BM25 (SQLite FTS5), fusionadas con Reciprocal Rank Fusion y reordenadas con un reranker.
- Cada fragmento se indexa con el nombre de su documento y su primera frase. Así se encuentran las páginas que no nombran el producto del que hablan, sin llamar al LLM.
- Respuestas en streaming con citas que se resuelven a documento y página; en la web, la cita abre el PDF en esa página.
- CLI (`ingest`, `search`, `ask`, `serve`) y web con FastAPI y HTMX, sin frameworks de JavaScript.
- 100 % local: los modelos los sirve oMLX en Apple Silicon. Sin LangChain, LlamaIndex ni Haystack.

## Cómo funciona

```
documentos ─► loaders ─► limpieza ─► chunks (800 car., 120 de solape) ─► contexto ─┬─► embeddings ─► ChromaDB
                                                                                   └─► BM25 (SQLite FTS5)

pregunta ─┬─► búsqueda vectorial ─┐
          └─► BM25 ───────────────┴─► RRF (k=60) ─► reranker (10 candidatos) ─► top 5 ─► prompt ─► LLM (streaming)
                                                                                                     │
                                                                   respuesta con [n] ─► documento y página
```

El contexto es una línea que se antepone al fragmento solo para buscarlo: «Documento «manual_hervidor_k1.pdf». Gracias por elegir el hervidor Termia K1.». Lo que ves en las respuestas y en las citas es el texto original.

| Pieza | Tecnología |
| --- | --- |
| LLM | `Qwen3.6-35B-A3B-6bit` vía oMLX (API compatible con OpenAI) |
| Embeddings | `Qwen3-Embedding-0.6B-4bit-DWQ` (1024 dimensiones) |
| Vectores | ChromaDB persistente, distancia coseno |
| Léxico | SQLite FTS5 (BM25 persistente, en la biblioteca estándar) |
| Reranker | `Qwen3-Reranker-0.6B-4bit` vía `POST /v1/rerank` de oMLX |
| Registro | SQLite (hash SHA-256 por documento) |
| Web | FastAPI, Jinja2, HTMX, Server-Sent Events |

## Resultados

Dos evaluaciones, con la configuración por defecto: búsqueda híbrida, reranker y contexto de metadatos.

### Corpus difícil (v2): qué aporta cada forma de contexto

80 preguntas sobre los 15 documentos de `samples_v2/`, repartidas en 8 categorías. Hay manuales casi iguales de tres modelos, un contrato y su adenda, tablas y páginas que no nombran el producto del que hablan. 70 preguntas tienen respuesta y 10 no. Los datos están en [`eval/questions_v2.jsonl`](eval/questions_v2.jsonl) y el informe completo en [`eval/results-v2.md`](eval/results-v2.md).

La tabla compara cuánto cuesta indexar con cada forma de contexto y cuánto mejora la búsqueda. Búsqueda híbrida con reranker y chunk 800; la ingesta es la de los 15 documentos (73 chunks):

| Contexto de cada chunk | Llamadas al LLM | Ingesta | Hit@1 | Hit@5 | MRR@10 | Implícitas | Distractor | Mejoran | Empeoran |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ninguno | 0 | 2.6 s | 0.771 | 0.914 | 0.827 | 0.2 | 0.9 | — | — |
| **Metadatos (por defecto)** | **0** | **2.6 s** | **0.929** | **0.971** | **0.946** | **1.0** | **1.0** | **13** | **2** |
| Una frase del LLM por documento | 15 | ≈ 10 s | 0.886 | 0.957 | 0.918 | 0.9 | 0.9 | 11 | 3 |
| Una frase del LLM por chunk | 73 | ≈ 100 s | 0.914 | 0.971 | 0.939 | 1.0 | 0.8 | 13 | 3 |

- **Metadatos** es «Documento «nombre del archivo». Primera frase del documento.», el mismo para todos los chunks del documento. No llama al LLM.
- **Por chunk** es el retrieval contextual clásico: el LLM lee el principio del documento y la página, y escribe una o dos frases que sitúan el chunk. Se activa con `DOCUCHAT_CONTEXTUAL_ENABLED=true`. La primera ingesta tarda unas 40 veces más; después hay caché.
- **Por documento** se midió con un prototipo y no está en la app: es más cara y peor que la de metadatos.
- **Mejoran / Empeoran** cuentan las preguntas cuyo primer resultado pasa a ser correcto o deja de serlo frente a no usar contexto. La búsqueda es determinista: repetida 3 veces, da lo mismo en las 70 preguntas.

Hit@1 por categoría (búsqueda híbrida con reranker, chunk 800):

| Categoría | Sin contexto | Metadatos | LLM por chunk |
| --- | ---: | ---: | ---: |
| Literal | 1.000 | 0.900 | 1.000 |
| Paráfrasis | 0.400 | 0.700 | 0.700 |
| Numérica | 1.000 | 0.900 | 1.000 |
| Distractor | 0.900 | 1.000 | 0.800 |
| Implícita | 0.200 | 1.000 | 1.000 |
| Tabla | 1.000 | 1.000 | 0.900 |
| Profunda | 0.900 | 1.000 | 1.000 |

Generación en la v2 (chunk 800): con metadatos, las palabras clave correctas pasan de 0.914 a 0.971 y los falsos rechazos, de 6 a 2. La precisión de citas y el rechazo correcto se quedan en 1.000 con y sin contexto.

Cómo leerlo:

- **Las preguntas implícitas son la trampa.** «¿Cuántos minutos hay que esperar para volver a encender el K2?» se responde en una página que solo dice «el hervidor». Sin contexto, esa página es igual en los tres manuales. Con el nombre del documento delante, el buscador sabe cuál es la del K2.
- **El contexto con LLM no gana al de metadatos y cuesta 40 veces más.** Sus 3 regresiones se repiten en cada generación de contextos y no son ruido. Por ejemplo, el contexto del manual del K1 dice «códigos de error E1, E2 y E3» y el del K2 no, así que la pregunta por el E3 del K2 encuentra antes el K1.
- **Las 2 regresiones de los metadatos** son l09, donde la primera frase de la adenda («Adenda al contrato de mantenimiento informático») le gana al contrato, y n09, donde el dato sale de otra página del mismo informe.

### Corpus original (v1)

42 preguntas sobre los 7 documentos de `samples/`: 32 tienen respuesta en una página concreta y 10 no la tienen. El dataset está en [`eval/questions.jsonl`](eval/questions.jsonl) y el informe completo en [`eval/results.md`](eval/results.md).

**Recuperación** (32 preguntas con respuesta; MRR sobre los 10 primeros resultados):

| Chunk | Modo | Chunks | Hit@1 | Hit@5 | MRR@10 | Fallos (top 5) |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 500 | hybrid | 45 | 1.000 | 1.000 | 1.000 | — |
| 500 | vector | 45 | 0.969 | 1.000 | 0.984 | — |
| 500 | bm25 | 45 | 1.000 | 1.000 | 1.000 | — |
| 800 | hybrid | 26 | 1.000 | 1.000 | 1.000 | — |
| 800 | vector | 26 | 0.969 | 1.000 | 0.977 | — |
| 800 | bm25 | 26 | 1.000 | 1.000 | 1.000 | — |
| 1200 | hybrid | 23 | 1.000 | 1.000 | 1.000 | — |
| 1200 | vector | 23 | 1.000 | 1.000 | 1.000 | — |
| 1200 | bm25 | 23 | 1.000 | 1.000 | 1.000 | — |

**Generación** (búsqueda híbrida, chunk 800):

| Métrica | Valor |
| --- | ---: |
| Preguntas | 42 (32 con respuesta, 10 sin respuesta) |
| Palabras clave correctas | 0.938 |
| Precisión de citas | 0.968 |
| Rechazo correcto | 1.000 |
| Falsos rechazos | 1 |
| Primer token (media) | 0.75 s |
| Tiempo total (media) | 0.90 s |

Cómo leerlo:

- **La búsqueda híbrida acierta las 32 a la primera** con chunk 800. En la v1.0.1, sin reranker ni contexto, se quedaba en 0.906.
- **La generación v1 empeora en dos preguntas**, aunque el buscador siempre pone primero la página correcta. Las dos fallan siempre de la misma forma en 2 pasadas, así que no es ruido. Ambas son preguntas ambiguas y el contexto solo cambia el orden de los otros fragmentos o el quinto, y con eso el LLM responde distinto:
  - q17 («¿Durante cuánto tiempo es gratuito el soporte técnico?») vuelve a responder «No lo sé»;
  - q09 responde con lo que trae la caja de la cafetera, no con lo que entrega el proveedor al acabar el contrato.

  En la v2, en cambio, los falsos rechazos bajan de 6 a 2. El balance es claramente favorable, pero el LLM sigue siendo sensible al orden del contexto.

Para repetir la evaluación (con oMLX arrancado; la v2 con el juez tarda bastante más):

```bash
uv run python eval/run_eval.py              # v1: recuperación y generación
uv run python eval/run_eval.py --skip-llm   # v1: solo recuperación
uv run python eval/run_eval.py --questions eval/questions_v2.jsonl --documents-dir samples_v2 \
  --variants sin_contexto,base,contextual --judge --out eval/results-v2.md --json eval/results-v2.json
```

Los tiempos de respuesta de `eval/results-v2.md` se midieron con otra evaluación en marcha a la vez: no sirven como medida de latencia.

## Requisitos

- Mac con Apple Silicon (oMLX usa MLX).
- [uv](https://docs.astral.sh/uv/) y Python 3.12.
- oMLX escuchando en `127.0.0.1:8000`, con API key y estos modelos descargados:
  - `Qwen3.6-35B-A3B-6bit`: solo los pesos ocupan unos 27 GB de memoria unificada. Cualquier modelo de chat que sirva oMLX vale cambiando `DOCUCHAT_LLM_MODEL`.
  - `Qwen3-Embedding-0.6B-4bit-DWQ`.
  - `Qwen3-Reranker-0.6B-4bit`. Si no está, la búsqueda funciona igual, pero con el orden de RRF; se desactiva con `DOCUCHAT_RERANK_ENABLED=false`.

## Puesta en marcha

```bash
git clone https://github.com/Alvarito90s/RAG-Docs.git
cd RAG-Docs
uv sync
cp .env.example .env                    # pon tu clave de oMLX en DOCUCHAT_LLM_API_KEY
uv run python scripts/check_env.py      # comprueba que oMLX responde con el LLM y los embeddings
uv run docuchat ingest                  # indexa samples/
uv run docuchat ask "¿Qué significa el error E-17 de la cafetera?"
uv run docuchat serve                   # http://127.0.0.1:8001
```

Para usar tus documentos, pon la carpeta en `DOCUCHAT_DOCUMENTS_DIR` o pásala a `ingest`.

## CLI

| Comando | Qué hace |
| --- | --- |
| `docuchat ingest [CARPETA]` | Indexa la carpeta (incremental). `--reset` reconstruye el índice desde cero; `--dry-run` solo lista documentos y páginas. |
| `docuchat search "TEXTO"` | Muestra los fragmentos más relevantes. `--mode hybrid\|vector\|bm25`, `-k N`. |
| `docuchat ask "PREGUNTA"` | Responde en streaming y lista las fuentes citadas. `-k N` fragmentos de contexto. |
| `docuchat serve` | Arranca la web en `http://127.0.0.1:8001`. `--host`, `--port`. |

## Web y API

La web tiene dos páginas: el chat (`/`) y los documentos indexados con un botón para reindexar (`/documents`).

| Método | Ruta | Qué hace |
| --- | --- | --- |
| GET | `/api/health` | Estado, número de documentos y chunks, modelos |
| GET | `/api/documents` | Documentos indexados |
| POST | `/api/search` | Búsqueda (`query`, `top_k`, `mode`) |
| POST | `/api/ask` | Respuesta por Server-Sent Events: `token`, `done` (con las fuentes) o `error` |
| POST | `/api/ingest` | Lanza una indexación en segundo plano (202) |
| GET | `/api/ingest/{job_id}` | Estado de la indexación |
| GET | `/files/{source}` | Sirve el documento original (las citas enlazan aquí con `#page=N`) |

## Docker

MLX necesita Metal, así que los modelos no pueden ir dentro de un contenedor. La imagen lleva solo la app y usa el oMLX del Mac a través de `host.docker.internal`.

```bash
docker compose up --build
```

- Abre `http://127.0.0.1:8001` y pulsa reindexar en **Documentos**.
- La carpeta `./samples` se monta en `/documents` en solo lectura. Para tus documentos, cambia ese volumen en [`compose.yaml`](compose.yaml).
- El índice vive en el volumen `docuchat-data`, así que sobrevive a reinicios.
- La clave se lee de tu `.env` al arrancar. Nunca se copia a la imagen: `.dockerignore` la excluye.

Si el contenedor no llega a oMLX, comprueba la conexión desde dentro:

```bash
docker compose exec docuchat python -c "from docuchat.env_check import main; raise SystemExit(main())"
```

## Configuración

Todo se configura con variables `DOCUCHAT_*` en `.env`; [`.env.example`](.env.example) tiene la lista completa con sus valores por defecto. Las más útiles:

| Variable | Por defecto | Para qué |
| --- | --- | --- |
| `DOCUCHAT_LLM_API_KEY` | (vacía) | Clave de oMLX |
| `DOCUCHAT_LLM_MODEL` | `Qwen3.6-35B-A3B-6bit` | Modelo de chat |
| `DOCUCHAT_EMBEDDING_MODEL` | `Qwen3-Embedding-0.6B-4bit-DWQ` | Modelo de embeddings |
| `DOCUCHAT_DOCUMENTS_DIR` | `samples` | Carpeta de documentos |
| `DOCUCHAT_DATA_DIR` | `data` | Índice (Chroma y registro SQLite) |
| `DOCUCHAT_CHUNK_SIZE` / `DOCUCHAT_CHUNK_OVERLAP` | `800` / `120` | Tamaño y solape de los chunks, en caracteres |
| `DOCUCHAT_TOP_K` | `5` | Fragmentos que se pasan al LLM |
| `DOCUCHAT_LLM_TEMPERATURE` | `0` | Aleatoriedad del LLM; 0 da respuestas reproducibles |
| `DOCUCHAT_LLM_THINKING` | `false` | Razonamiento de Qwen (más lento) |
| `DOCUCHAT_RERANK_ENABLED` / `DOCUCHAT_RERANK_CANDIDATES` | `true` / `10` | Reranker y cuántos candidatos de RRF reordena |
| `DOCUCHAT_CONTEXTUAL_META_ENABLED` | `true` | Contexto de metadatos (nombre del documento y primera frase), sin LLM |
| `DOCUCHAT_CONTEXTUAL_ENABLED` | `false` | Contexto escrito por el LLM para cada fragmento; sustituye al de metadatos y la ingesta tarda unas 40 veces más |

Si cambias el modelo de embeddings, reconstruye el índice con `docuchat ingest --reset`: la app se niega a mezclar vectores de modelos distintos. Haz lo mismo si cambias las opciones de contexto o si vienes de la v1.0: los documentos que no han cambiado no se vuelven a indexar.

## Decisiones de diseño

- **Sin frameworks de RAG.** Cada pieza (loaders, chunker, fusión, prompts, citas) es un módulo pequeño que se lee y se prueba por separado.
- **Chunks de 800 caracteres con 120 de solape.** En la evaluación empatan con 1200 y superan a 500 con búsqueda híbrida, y dan al LLM fragmentos más cortos.
- **Instrucción solo en las consultas.** Qwen3-Embedding recomienda prefijar la pregunta con una instrucción; los documentos se indexan sin ella.
- **RRF con k=60 y sin vecinos repetidos.** De dos chunks adyacentes de la misma página solo queda el mejor, para no gastar contexto en texto solapado.
- **Reranker sobre 10 candidatos.** Con 20, Hit@1 sube algo más en la eval v2 (0.814 frente a 0.771), pero cada búsqueda tarda el doble: 0,48 s más en lugar de 0,23 s.
- **Contexto de metadatos en vez de contexto con LLM.** Se midieron las dos (tabla de resultados): el de metadatos es gratis y acierta más.
- **Citas `[n]` validadas.** Las que no corresponden a ningún fragmento se descartan y se avisa.
- **Temperatura 0 y una regla para preguntas ambiguas.** Las respuestas son reproducibles y, si la pregunta no concreta a qué se refiere, el modelo responde para el caso que encuentra en vez de decir "No lo sé".
- **Razonamiento desactivado** por latencia; se activa con `DOCUCHAT_LLM_THINKING=true`.
- **Índice que se repara solo.** Si el registro SQLite y Chroma se desincronizan, la siguiente indexación reprocesa lo que falta.

## Cómo se ha construido

El proyecto se ha desarrollado con dos agentes y un humano que revisa:

- Un **cerebro** (Claude) escribe una spec por tarea en [`tasks/`](tasks): objetivo, archivos, firmas exactas y tests con valores esperados que no se pueden cambiar.
- Un **ejecutor** (Qwen 3.6 en local, con opencode) implementa cada spec y deja un informe en [`reports/`](reports). Sus reglas están en [`AGENTS.md`](AGENTS.md).
- El cerebro verifica cada informe ejecutando la suite y probando contra los modelos reales. Si algo no cuadra, escribe una spec de corrección (las `NNN-b`).

El estado del proyecto se mantiene en [`docs/STATE.md`](docs/STATE.md).

## Desarrollo

```bash
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
uv run mypy src
```

Los tests no llaman a oMLX: usan embeddings y modelos de chat falsos. La CI ejecuta lo mismo y además construye la imagen Docker.

```
src/docuchat/
  config.py      configuración (pydantic-settings, prefijo DOCUCHAT_)
  ingest/        loaders por formato, limpieza y escáner de carpetas
  index/         chunker, embeddings, Chroma, FTS5, contexto, registro e indexador
  retrieval/     fusión RRF, reranker y buscador híbrido
  generation/    cliente LLM, prompts, citas y Answerer
  evaluation/    dataset, métricas, ejecución e informe
  api/           FastAPI, plantillas y estáticos
  cli.py         comandos ingest, search, ask y serve
```

## Limitaciones

- Los modelos necesitan un Mac con Apple Silicon. La app habla con cualquier servidor compatible con la API de OpenAI (`DOCUCHAT_LLM_BASE_URL`), pero solo se ha probado con oMLX.
- No hay OCR: los PDF escaneados sin capa de texto no se indexan.
- El contexto con LLM tarda alrededor de 1,3 s por fragmento la primera vez (hay caché). Por eso va apagado por defecto.
- La evaluación usa dos corpus pequeños y generados (`samples/` y `samples_v2/`); los números no se pueden extrapolar a cualquier colección.

## Licencia

[MIT](LICENSE)
