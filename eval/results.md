# Resultados de la evaluación

Fecha: 2026-11-24 12:53 · LLM: `Qwen3.6-35B-A3B-6bit` · Embeddings: `Qwen3-Embedding-0.6B-4bit-DWQ`

## Recuperación

Preguntas con respuesta de `eval/questions.jsonl`; MRR sobre los 10 primeros resultados.

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

## Generación

Búsqueda híbrida, chunk 800.

| Métrica | Valor |
| --- | ---: |
| Preguntas | 42 (32 con respuesta, 10 sin respuesta) |
| Palabras clave correctas | 0.938 |
| Precisión de citas | 0.968 |
| Rechazo correcto | 1.000 |
| Falsos rechazos | 1 |
| Primer token (media) | 0.75 s |
| Tiempo total (media) | 0.90 s |

Fallos:
- q09: El proveedor entregará la cafetera principal, el filtro permanente de acero inoxidable, el dosificador de café y un paño…
- q17: No lo sé con la información de los documentos.
