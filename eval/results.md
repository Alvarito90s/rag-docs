# Resultados de la evaluación

Fecha: 2026-11-23 15:42 · LLM: `Qwen3.6-35B-A3B-6bit` · Embeddings: `Qwen3-Embedding-0.6B-4bit-DWQ`

## Recuperación

Preguntas con respuesta de `eval/questions.jsonl`; MRR sobre los 10 primeros resultados.

| Chunk | Modo | Chunks | Hit@1 | Hit@5 | MRR@10 | Fallos (top 5) |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 500 | hybrid | 45 | 0.844 | 1.000 | 0.917 | — |
| 500 | vector | 45 | 0.938 | 1.000 | 0.952 | — |
| 500 | bm25 | 45 | 0.844 | 1.000 | 0.898 | — |
| 800 | hybrid | 26 | 0.906 | 1.000 | 0.953 | — |
| 800 | vector | 26 | 0.938 | 1.000 | 0.958 | — |
| 800 | bm25 | 26 | 0.844 | 1.000 | 0.909 | — |
| 1200 | hybrid | 23 | 0.906 | 1.000 | 0.953 | — |
| 1200 | vector | 23 | 0.938 | 1.000 | 0.958 | — |
| 1200 | bm25 | 23 | 0.875 | 1.000 | 0.924 | — |

## Generación

Búsqueda híbrida, chunk 800.

| Métrica | Valor |
| --- | ---: |
| Preguntas | 42 (32 con respuesta, 10 sin respuesta) |
| Palabras clave correctas | 1.000 |
| Precisión de citas | 0.971 |
| Rechazo correcto | 1.000 |
| Falsos rechazos | 0 |
| Primer token (media) | 0.57 s |
| Tiempo total (media) | 0.75 s |
