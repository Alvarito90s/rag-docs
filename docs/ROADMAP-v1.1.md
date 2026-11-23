# Plan v1.1 · Mejoras técnicas

> Plan para el cerebro y el humano. El obrero no lo lee: recibe las specs que salen de cada casilla.
> Punto de partida: v1.0.1 (467 tests, `eval/results.md` del 2026-11-23).

## Cómo se usa

1. El humano pasa al cerebro el prompt de arranque de `docs/BRAIN_PROMPT.md`, junto con `AGENTS.md`, `docs/STATE.md` y este archivo. Le dice qué casillas quiere: "genera las specs 080 a 082".
2. El cerebro escribe `tasks/NNN-nombre.md`. Si una casilla supera 3 archivos o unas 200 líneas de cambio, la parte en `NNN-a` y `NNN-b`.
3. El obrero ejecuta en cadena: "ejecuta tasks/080 a 082". Escribe un informe por spec.
4. El cerebro revisa cada informe con el prompt de revisión: APROBADA o spec de corrección `NNN-b`.
5. El humano hace el commit, y además las **puertas H**: pasos con los modelos reales que ni el obrero ni la CI pueden hacer.

**No se pasa de fase sin cerrar su puerta H.** En la v1.0 los bugs serios salieron al probar con oMLX, no en la CI.

## Reglas comunes de la v1.1

- **Toda mejora entra apagada.** Cada una tiene un flag en `config.py` (`rerank_enabled`, `contextual_enabled`, `ocr_enabled`) con valor por defecto `False`. Solo se enciende por defecto si su puerta H lo justifica con números, y el humano lo apunta en "Decisiones tomadas" de `AGENTS.md`.
- **Con el flag apagado, el comportamiento es idéntico a la v1.0.1.** Cada spec lleva un test que lo comprueba.
- **No se toca el prompt de generación** (`generation/prompts.py`). Si no, las métricas de generación dejan de ser comparables entre fases.
- **Cambios de dependencias autorizados** (el humano los añade a la sección Stack de `AGENTS.md` antes de la spec que los usa):
  - `httpx` como dependencia explícita (fase 9). Ya está en `uv.lock` a través de `openai`.
  - Se **quita** `rank-bm25` (fase 10).
  - Tesseract como dependencia del sistema, no de Python (fase 12).
- Los tests siguen sin llamar a oMLX: fakes para el reranker, el contextualizador y el juez. `httpx.MockTransport` para el cliente HTTP.
- Cada fase termina añadiendo su variante a la evaluación (fase 8), para tener siempre una tabla de antes y después.

## Mapa

| Fase | Mejora | Specs | Puerta | Resultado |
| --- | --- | --- | --- | --- |
| 8 | Deuda + evaluación v2 | 080–086 | H1 | Línea base medible (Hit@1 lejos de 1.0) |
| 9 | Reranker | H2, 090–092 | H3 | Decisión: ¿rerank por defecto? |
| 10 | BM25 persistente en SQLite FTS5 | 100–103 | H4 | Sin regresión, sin `rank-bm25` |
| 11 | Retrieval contextual | 110–112 | H5 | Decisión: ¿contextual por defecto? |
| 12 | OCR opcional | H6, 120–121 | H7 | PDF escaneados indexables |
| 13 | Publicación v1.1.0 | 130 | — | README, CHANGELOG, resultados |

Orden de dependencias: 8 → 9 → 10 → 11 → 12 → 13. La fase 10 va antes que la 11 a propósito: el retrieval contextual cambia el texto que se indexa en BM25, y así solo se implementa una vez, sobre FTS5.

---

## Fase 8 · Deuda y evaluación v2

Objetivo: poder medir mejoras. Ahora mismo Hit@5 = 1.000 en las 9 configuraciones y el corpus tiene 26 chunks con chunk 800.

- [x] **080 · Dividir el CLI y vigilar el límite de 300 líneas** — spec escrita: `tasks/080-cli-dividir.md`.
  - `src/docuchat/cli.py` tiene 315 líneas e incumple la regla 2 de `AGENTS.md`.
  - Mover las funciones puras de formato (`build_table`, `summary_line`, `stats_line`, `format_sources`, `snippet`, `format_result`) a `src/docuchat/cli_format.py`. `cli.py` las importa, así que `from docuchat.cli import build_table` sigue funcionando en los tests.
  - Crear `tests/test_file_sizes.py`: falla si algún `.py` de `src/` tiene 300 líneas o más.
  - Fuera de alcance: cambiar comandos u opciones.

- [x] **081 · Corpus de evaluación v2** — spec escrita: `tasks/081-corpus-v2.md`.
  - Contenido como assets en `tasks/assets/081/`, escrito por el cerebro; el obrero copia y genera `samples_v2/`.
  - Tamaño: 15 documentos, 70 páginas y 73 chunks con chunk 800 (el corpus v1 tiene 26).
  - Trampas:
    - Tres manuales casi iguales: Termia K1, K2 y K3 Pro.
    - Un contrato y la adenda que cambia el precio.
    - La política de teletrabajo de 2025 y la de 2026.
    - Dos actas del comité con los mismos temas.
    - Tablas en DOCX y Markdown.
    - Un informe de 12 páginas.
    - Un reglamento numerado por artículos.
  - La trampa principal: las páginas 2, 3 y 6 de cada manual no nombran el modelo, y la cabecera que lo nombra se quita al limpiar los bordes repetidos.
  - `samples/` no se toca: la evaluación v1 sigue como prueba de regresión.

- [x] **082 · Preguntas v2 con categoría** — spec escrita: `tasks/082-preguntas-v2.md`.
  - `EvalQuestion` gana `category: str = "general"`.
  - 80 preguntas en `tasks/assets/082/questions_v2.jsonl`, 10 por categoría: `literal`, `parafrasis`, `numerica`, `distractor`, `implicita`, `tabla`, `profunda`, `sin_respuesta`.
  - Comprobado al escribirlas: las palabras clave de las 70 preguntas con respuesta están en su página esperada.
  - BM25 sin modelos ya da Hit@1 0.70 y Hit@5 0.80 sobre el corpus v2. Con chunk 800, en el v1 daba 0.844 y 1.000. Las implícitas se quedan en Hit@1 0.10.

- [ ] **083 · Métricas por categoría**
  - `RetrievalReport` gana Hit@1, Hit@5 y MRR por categoría.
  - `GenerationReport` gana el acierto de palabras clave por categoría.
  - `report.py` pinta una tabla por categoría.
  - Con el dataset v1, todo cae en `general` y el informe no cambia de forma.

- [ ] **084 · Variantes de evaluación**
  - `VARIANTS: dict[str, dict[str, object]]`: cada variante es un nombre más los cambios que aplica a `Settings`. De momento solo `{"base": {}}`.
  - `run_eval.py` gana `--variants base,...`. Cada variante indexa en su propia carpeta (`data/eval/<variante>-cs<N>`). Las tablas de recuperación y generación ganan la columna "Variante".
  - Cada fase posterior solo tendrá que añadir una entrada al diccionario.

- [ ] **085 · Repeticiones de la generación**
  - `--runs N` (por defecto 1). Para cada métrica de generación da la media y el rango mínimo–máximo.
  - Lista de **preguntas inestables**: las que cambian de resultado entre pasadas. Es la lección de q17 convertida en métrica.
  - La recuperación es determinista: se ejecuta una sola vez.

- [ ] **086 · Juez de fidelidad (opcional)**
  - Nuevo `src/docuchat/evaluation/judge.py`. Recibe la respuesta y los chunks que cita, y el LLM devuelve un JSON `{"supported": bool, "unsupported": [frases]}`.
  - Si el JSON no se puede parsear, cuenta como "sin juzgar", no como fallo.
  - Métrica nueva "Fidelidad" = respuestas sin afirmaciones sin respaldo / respuestas juzgadas.
  - Flag `--judge` y ajuste `judge_model`, que por defecto es igual a `llm_model`, con temperatura 0. El informe avisa de que el juez es el mismo modelo que responde (sesgo).
  - Tests con un `ChatModel` falso.

- [ ] **H1 · Línea base (humano)**
  1. Lee las 80 preguntas: cada una con respuesta tiene que tener **una única** página correcta.
  2. Ejecuta:
     ```bash
     uv run python eval/run_eval.py --questions eval/questions_v2.jsonl --documents-dir samples_v2 --runs 3 --judge --out eval/results-v2-baseline.md --json eval/results-v2-baseline.json
     ```
  3. Criterio: Hit@1 en modo híbrido entre 0.60 y 0.85. Si sale ≥ 0.9, el corpus sigue siendo fácil y el cerebro escribe `081-b` con más trampas.
  4. Commit de `eval/results-v2-baseline.*`: es la referencia de todas las fases siguientes.

---

## Fase 9 · Reranker

Objetivo: reordenar los candidatos de RRF con un cross-encoder. Los datos actuales lo piden: con chunk 800, vector solo (Hit@1 0.938) supera a hybrid (0.906).

- [ ] **H2 · Verificar el reranker en oMLX (humano, antes de 090)**
  1. Carga en oMLX un modelo reranker: `mlx-community/Qwen3-Reranker-0.6B-4bit`. Si oMLX no lo admite, `bge-reranker-v2-m3` en MLX.
  2. Prueba el endpoint a mano con tu clave:
     ```bash
     curl -s http://127.0.0.1:8000/v1/rerank -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d '{"model":"<modelo>","query":"¿cuánto dura la garantía?","documents":["La garantía es de 2 años.","El envío es gratuito."],"top_n":2}'
     ```
  3. Guarda la respuesta real, **sin la clave**, en `tests/fixtures/rerank_response.json`. El cerebro escribe la spec con el esquema real, no con el de la documentación de terceros (regla 5).
  4. Anota en "Decisiones tomadas" el modelo elegido. Añade `httpx` al Stack de `AGENTS.md`.

- [ ] **090 · Configuración del reranker**
  - `config.py`: `rerank_enabled: bool = False`, `rerank_base_url` (por defecto el mismo servidor), `rerank_model`, `rerank_candidates: int = 20` (debe ser ≥ `top_k`, con validador).
  - `pyproject.toml`: `httpx` explícito.
  - `env_check`: si `rerank_enabled` está activo, comprueba que el modelo aparece en `/v1/models`.

- [ ] **091 · Cliente del reranker**
  - Nuevo `src/docuchat/retrieval/reranker.py` con:
    - `Reranker` (Protocol): `rerank(query, texts) -> list[float]`, una puntuación por texto en el mismo orden de entrada.
    - `HttpReranker` (httpx, timeout y reintentos de `Settings`).
    - `RerankError`.
    - `make_reranker(settings)`.
  - Tests con `httpx.MockTransport` y la fixture real de H2: orden, `top_n`, error HTTP → `RerankError`, lista vacía sin llamada.

- [ ] **092 · Rerank en el buscador**
  - `Searcher` recibe `reranker: Reranker | None`. Con reranker, el flujo es RRF → `drop_adjacent` → los `rerank_candidates` primeros → rerank → `top_k`.
  - `SearchResult` gana `rerank_score: float | None = None`. `score` sigue siendo el de RRF, y la API lo expone en `result_to_dict`.
  - **Decisión a fijar en la spec:** si el reranker falla, se recomienda volver al orden RRF con un aviso en el log, no romper la respuesta.
  - Eval: variante `"rerank": {"rerank_enabled": True}`.
  - Test: sin reranker, la salida es idéntica a la v1.0.1.

- [ ] **H3 · Decisión sobre el reranker (humano)**
  - Ejecuta la evaluación con `--variants base,rerank` y compara con la línea base.
  - Se enciende por defecto si Hit@1 híbrido mejora al menos 0.03 **y** el tiempo total medio sube menos de 0.3 s.
  - Prueba también `docuchat ask` y la web con rerank activo.
  - Apunta la decisión y los números en `AGENTS.md`.

---

## Fase 10 · BM25 persistente con SQLite FTS5

Objetivo: quitar la limitación del README de que el índice BM25 vive en memoria y se reconstruye al arrancar. FTS5 viene con la `sqlite3` de la biblioteca estándar; está comprobado en el entorno (SQLite 3.53.1 con FTS5).

- [ ] **100 · `FtsIndex`**
  - Nuevo `src/docuchat/index/fts.py` con `FtsIndex(db_path)` y los métodos `add(chunks)`, `delete_source(source)`, `search(query, k) -> list[tuple[str, float]]`, `count()`, `sources()`, `clear()`.
  - Mover `tokenize()` aquí desde `bm25.py`; `bm25.py` la reimporta hasta la spec 103.
  - El texto se guarda **ya tokenizado** con `tokenize()` y unido por espacios, para que los tokens sean idénticos a los de ahora. La tabla usa `tokenize = "unicode61 tokenchars '_'"`, porque `\w` incluye el guion bajo.
  - La consulta es un OR de tokens entre comillas dobles, lo que evita inyectar sintaxis FTS. Se ordena por `bm25()` ascendente y se devuelve `score = -bm25`.
  - Una conexión por operación, porque la API indexa en un hilo y busca en otro.
  - `Settings.fts_path = data_dir / "fts.sqlite3"`.

- [ ] **101 · `VectorStore.get_chunks(ids)`**
  - Recupera chunks por id con `collection.get(ids=..., include=["documents", "metadatas"])`, en el orden pedido. Los ids que falten se ignoran.
  - El buscador lo necesita para dejar de cargar todos los chunks en memoria.

- [ ] **102 · El indexador escribe en FTS**
  - `Indexer` escribe y borra en FTS a la vez que en Chroma. `reset_index` también vacía FTS.
  - **Migración sin volver a calcular embeddings:** si un documento está en Chroma pero no en FTS (un índice de la v1.0.1), se rellena FTS con los chunks de Chroma.
  - Reparación al estilo de 026-b: un documento solo cuenta como "sin cambios" si está en el registro, en Chroma **y** en FTS.

- [ ] **103 · El buscador usa FTS y se retira `rank-bm25`**
  - `Searcher` busca en `FtsIndex` y desaparece la caché de `all_chunks`.
  - Borrar `index/bm25.py` y `tests/index/test_bm25.py`. Los casos de tokenización pasan a `tests/index/test_fts.py`.
  - `uv remove rank-bm25`.
  - El humano actualiza el Stack de `AGENTS.md`.

- [ ] **H4 · Sin regresión (humano)**
  - Evaluación v1 y v2 en modo `bm25` y `hybrid`: diferencia de Hit@1 y MRR de ±0.03 como máximo respecto a la línea base. Las puntuaciones de FTS5 no son idénticas a las de `rank-bm25`.
  - Arranca la app con el índice de la v1.0.1 y comprueba que la migración rellena FTS sin recalcular embeddings.
  - Mide el tiempo de la primera búsqueda antes y después.

---

## Fase 11 · Retrieval contextual

Objetivo: anteponer a cada chunk una o dos frases, generadas por el LLM al indexar, que lo sitúen en su documento. Ataca casos como q17, en los que el chunk no dice de qué producto habla.

- [ ] **110 · Campo `context` en los chunks**
  - `Chunk.context: str = ""`. `VectorStore` lo guarda en los metadatos y `chunk_from_record` lo recupera.
  - Nueva función pura `index_text(chunk) -> str`: devuelve `context + "\n\n" + text`, o solo `text` si `context` está vacío. Es lo que se usa para el embedding y para FTS.
  - El texto que ve el LLM y el usuario sigue siendo `text`.
  - Test: con `context` vacío, los textos indexados son idénticos a los de ahora.

- [ ] **111 · Contextualizador con caché**
  - Nuevo `src/docuchat/index/contextualizer.py`:
    - `Contextualizer.context_for(source, heading, page_text, chunk_text) -> str`.
    - Usa `ChatModel.complete` con temperatura 0 y sin razonamiento.
    - Prompt fijo con `CONTEXT_PROMPT_VERSION`.
    - La ventana es la página recortada a `contextual_window_chars`.
  - Caché SQLite en `data_dir / "context_cache.sqlite3"`:
    - Clave: sha256 de versión del prompt + modelo + ventana + chunk.
    - `reset_index` **no** la borra, así que reindexar o repetir la evaluación no repite llamadas.
  - `config.py`: `contextual_enabled: bool = False`, `contextual_model` (por defecto `llm_model`), `contextual_window_chars: int = 4000`, `contextual_max_chars: int = 300`.
  - Tests con un `ChatModel` falso: acierto de caché sin llamada, recorte de la salida, error del LLM → contexto vacío y aviso en el log (la ingesta no se rompe).

- [ ] **112 · Contexto en el indexador y en la evaluación**
  - Con `contextual_enabled`, `Indexer` rellena `context` antes de calcular los embeddings. El progreso informa por chunk, porque ahora la ingesta tarda bastante más.
  - Eval: variantes `"contextual"` y `"rerank+contextual"`.

- [ ] **H5 · Decisión sobre el retrieval contextual (humano)**
  - Ejecuta la evaluación con `--variants base,rerank,contextual,rerank+contextual`.
  - Mide el tiempo de ingesta de `samples_v2` con y sin contexto.
  - Lee 20 contextos generados al azar: ¿sitúan el chunk o se inventan cosas?
  - Se enciende por defecto solo si mejora Hit@1 en `implicita` y `distractor` sin empeorar el resto.

---

## Fase 12 · OCR opcional

Objetivo: indexar PDF escaneados. Quita la limitación del README de que no hay OCR.

- [ ] **H6 · Tesseract (humano)**
  - Instálalo, con el paquete de idiomas que incluye el español:
    ```bash
    brew install tesseract tesseract-lang
    ```
  - Comprueba que funciona:
    ```bash
    tesseract --list-langs
    ```
  - Antes de escribir la spec, el cerebro consulta en la documentación de PyMuPDF 1.28 cómo localiza `tessdata` (la variable `TESSDATA_PREFIX` o el parámetro `tessdata`) e incluye el fragmento correcto (regla 5).
  - El humano añade Tesseract al Stack de `AGENTS.md` como dependencia del sistema.

- [ ] **120 · OCR en el loader de PDF**
  - `config.py`: `ocr_enabled: bool = False`, `ocr_language: str = "spa+eng"`, `ocr_dpi: int = 300`, `ocr_min_chars: int = 50`.
  - Nueva función pura `needs_ocr(text, min_chars) -> bool`.
  - En `extract_paragraphs`, cuando el OCR está activo y la página tiene muy poco texto nativo:
    ```python
    tp = page.get_textpage_ocr(language=..., dpi=..., full=True)
    blocks = page.get_text("blocks", sort=True, textpage=tp)
    ```
  - Las opciones llegan desde `load_document` en `scanner.py`, nunca escritas a mano en el código.
  - Si falta Tesseract, el error queda en `IndexStats.errors` y no rompe la ingesta.
  - El test que usa Tesseract de verdad lleva `skipif(shutil.which("tesseract") is None)`.

- [ ] **121 · PDF escaneado de prueba, Docker y CI**
  - `make_samples_v2.py` genera `samples_v2/escaneado.pdf` (en `samples_v2/` para no romper los tests de `samples/`):
    ```python
    pix = page.get_pixmap(dpi=150)
    p = out.new_page(...)
    p.insert_image(p.rect, pixmap=pix)
    ```
    Test: su texto nativo está vacío.
  - Tres o cuatro preguntas nuevas en `questions_v2.jsonl`, categoría `escaneado`.
  - `Dockerfile` con `apt-get install tesseract-ocr tesseract-ocr-spa`.
  - CI con el mismo `apt-get` en el job `check`, para que el test con Tesseract se ejecute allí.
  - `env_check`: si `ocr_enabled` está activo, comprueba que existe `tesseract` y el idioma `spa`.

- [ ] **H7 · OCR real (humano)**
  - Ingesta de `samples_v2` con `DOCUCHAT_OCR_ENABLED=true`.
  - Las preguntas `escaneado` se aciertan y abren la página correcta en la web.
  - Prueba también con un PDF escaneado tuyo.
  - Hay un fallo conocido de PyMuPDF en el que el OCR pierde texto ([issue 4833](https://github.com/pymupdf/PyMuPDF/issues/4833)). Si aparece, anótalo como limitación.

---

## Fase 13 · Publicación

- [ ] **130 · v1.1.0**
  - El cerebro escribe los assets de `README.md` y `README.en.md`:
    - Resultados de la evaluación v2 por variante y por categoría.
    - Las nuevas variables `DOCUCHAT_RERANK_*`, `DOCUCHAT_CONTEXTUAL_*` y `DOCUCHAT_OCR_*`.
    - Limitaciones actualizadas.
  - `CHANGELOG.md` con la sección 1.1.0. Versión en `pyproject.toml` y `__init__.py`.
  - `eval/results.md` regenerado con la configuración por defecto final.
  - Los tests de la spec 072 que protegen el README se actualizan **en esta spec**, por decisión del cerebro, no del obrero.

---

## Riesgos conocidos

| Riesgo | Dónde | Qué hacer |
| --- | --- | --- |
| El esquema de `/v1/rerank` en tu versión de oMLX no es el que dicen terceros | 091 | H2 guarda una respuesta real como fixture antes de la spec |
| El corpus v2 sale igual de fácil | 081 | El criterio de H1 obliga a `081-b` |
| El juez es el mismo modelo que responde | 086 | Se informa como métrica orientativa; nunca decide una puerta sola |
| La ingesta con contexto es lenta (una llamada al LLM por chunk) | 111–112 | Caché persistente, flag apagado por defecto, progreso por chunk |
| FTS5 puntúa distinto que `rank-bm25` | 103 | Tolerancia de ±0.03 en H4 |
| Desincronización entre registro, Chroma y FTS (como en 026-b) | 102 | Un documento solo está "sin cambios" si está en los tres sitios |
| El obrero ajusta los tests para que pasen | todas | Regla 7 de `AGENTS.md`: el cerebro revisa los diffs de `tests/` en cada informe |

## Recuento

Unas 21 specs (más las `-b` que salgan) y 7 puertas humanas. Cadenas sugeridas para el obrero:

- 080–082: hechas y aprobadas; queda la corrección de documentación 082-b
- 083–086
- 090–092
- 100–103
- 110–112
- 120–121
- 130
