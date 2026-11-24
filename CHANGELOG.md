# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones según [SemVer](https://semver.org/lang/es/).

## [1.1.0] - 2026-11-24

### Añadido
- Reranker `Qwen3-Reranker-0.6B-4bit` vía `POST /v1/rerank` de oMLX, activo por defecto sobre 10 candidatos. Si falla, la búsqueda vuelve al orden de RRF.
- Contexto de metadatos en cada chunk («Documento «fuente». Primera frase.»), activo por defecto y sin LLM. Solo se usa para buscar: las respuestas y las citas muestran el texto original.
- Contexto escrito por el LLM para cada chunk, opcional (`DOCUCHAT_CONTEXTUAL_ENABLED=true`) y con caché persistente. Sustituye al de metadatos.
- Evaluación v2: 15 documentos y 80 preguntas en 8 categorías (`samples_v2/`, `eval/questions_v2.jsonl`), variantes de configuración (`--variants`), juez de fidelidad (`--judge`), repeticiones (`--runs`) y Hit@1 por categoría.

### Cambiado
- BM25 pasa a SQLite FTS5: el índice léxico es persistente y ya no se reconstruye en memoria al arrancar. Sale la dependencia `rank-bm25`.
- Eval v2 (híbrido, chunk 800): Hit@1 0.643 → 0.929, preguntas implícitas 0.0 → 1.0 y falsos rechazos 10 → 2.
- Eval v1 (híbrido, chunk 800): Hit@1 0.906 → 1.000. La generación empeora en dos preguntas ambiguas (q09 y q17): palabras clave 1.000 → 0.938 y 1 falso rechazo.

### Para actualizar desde la 1.0
- Reindexa con `uv run docuchat ingest --reset` para que los documentos ya indexados reciban el contexto.
- Descarga `Qwen3-Reranker-0.6B-4bit` en oMLX o desactiva el reranker con `DOCUCHAT_RERANK_ENABLED=false`.

## [1.0.1] - 2026-11-23

### Corregido
- Falso rechazo en preguntas ambiguas (q17 de la evaluación): el prompt pide ahora responder para el caso concreto y decir a cuál se refiere, en vez de "No lo sé".

### Cambiado
- Temperatura por defecto del LLM: 0 (antes 0,2), para que las respuestas y la evaluación sean reproducibles.
- Evaluación de generación: palabras clave 1.000, precisión de citas 0.971 y 0 falsos rechazos; el rechazo correcto se mantiene en 1.000.

### Añadido
- README en inglés (`README.en.md`).

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
