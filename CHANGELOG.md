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
