# Resultados de la evaluación

Fecha: 2026-11-24 12:50 · LLM: `Qwen3.6-35B-A3B-6bit` · Embeddings: `Qwen3-Embedding-0.6B-4bit-DWQ` · Juez: `Qwen3.6-35B-A3B-6bit`

Nota: el juez es el mismo modelo que responde; la fidelidad es orientativa.

## Recuperación

Preguntas con respuesta de `eval/questions_v2.jsonl`; MRR sobre los 10 primeros resultados.

| Variante | Chunk | Modo | Chunks | Hit@1 | Hit@5 | MRR@10 | Fallos (top 5) |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| sin_contexto | 500 | hybrid | 99 | 0.786 | 0.957 | 0.856 | p02, i08, i09 |
| sin_contexto | 500 | vector | 99 | 0.757 | 0.929 | 0.831 | i05, i08, i09, i10, f04 |
| sin_contexto | 500 | bm25 | 99 | 0.757 | 0.900 | 0.815 | p02, p05, p08, p09, i02, i04, i08 |
| sin_contexto | 800 | hybrid | 73 | 0.771 | 0.914 | 0.827 | p02, p08, p09, i04, i08, i10 |
| sin_contexto | 800 | vector | 73 | 0.814 | 0.943 | 0.863 | p02, i05, i08, i10 |
| sin_contexto | 800 | bm25 | 73 | 0.771 | 0.886 | 0.814 | p01, p02, p05, p08, p09, i02, i04, i08 |
| sin_contexto | 1200 | hybrid | 70 | 0.786 | 0.929 | 0.841 | p02, p09, i04, i08, i10 |
| sin_contexto | 1200 | vector | 70 | 0.814 | 0.943 | 0.863 | p02, i05, i08, i10 |
| sin_contexto | 1200 | bm25 | 70 | 0.771 | 0.886 | 0.814 | p01, p02, p05, p08, p09, i02, i04, i08 |
| base | 500 | hybrid | 99 | 0.900 | 0.986 | 0.933 | p09 |
| base | 500 | vector | 99 | 0.943 | 0.986 | 0.961 | f04 |
| base | 500 | bm25 | 99 | 0.871 | 0.914 | 0.890 | p05, p08, p09, p10, i04, i08 |
| base | 800 | hybrid | 73 | 0.929 | 0.971 | 0.946 | p08, p09 |
| base | 800 | vector | 73 | 0.943 | 0.986 | 0.960 | f04 |
| base | 800 | bm25 | 73 | 0.886 | 0.914 | 0.900 | p05, p08, p09, p10, i04, i08 |
| base | 1200 | hybrid | 70 | 0.929 | 0.971 | 0.946 | p08, p09 |
| base | 1200 | vector | 70 | 0.943 | 0.986 | 0.960 | f04 |
| base | 1200 | bm25 | 70 | 0.886 | 0.914 | 0.900 | p05, p08, p09, p10, i04, i08 |
| contextual | 500 | hybrid | 99 | 0.857 | 0.986 | 0.912 | p02 |
| contextual | 500 | vector | 99 | 0.900 | 0.986 | 0.939 | f04 |
| contextual | 500 | bm25 | 99 | 0.829 | 0.929 | 0.872 | p02, p05, p09, i04, i08 |
| contextual | 800 | hybrid | 73 | 0.914 | 0.971 | 0.939 | p02, p09 |
| contextual | 800 | vector | 73 | 0.886 | 0.971 | 0.923 | p09, i10 |
| contextual | 800 | bm25 | 73 | 0.843 | 0.900 | 0.871 | p01, p02, p05, p08, p09, i04, i08 |
| contextual | 1200 | hybrid | 70 | 0.914 | 0.971 | 0.940 | p02, p09 |
| contextual | 1200 | vector | 70 | 0.900 | 0.971 | 0.932 | p09, i10 |
| contextual | 1200 | bm25 | 70 | 0.843 | 0.900 | 0.871 | p01, p02, p05, p08, p09, i04, i08 |

### Por categoría (chunk 800)

| Categoría | Preguntas | Hit@1 sin_contexto/hybrid | Hit@1 sin_contexto/vector | Hit@1 sin_contexto/bm25 | Hit@1 base/hybrid | Hit@1 base/vector | Hit@1 base/bm25 | Hit@1 contextual/hybrid | Hit@1 contextual/vector | Hit@1 contextual/bm25 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| literal | 10 | 1.000 | 1.000 | 1.000 | 0.900 | 0.900 | 0.900 | 1.000 | 1.000 | 1.000 |
| parafrasis | 10 | 0.400 | 0.700 | 0.300 | 0.700 | 0.900 | 0.600 | 0.700 | 0.700 | 0.400 |
| numerica | 10 | 1.000 | 1.000 | 1.000 | 0.900 | 0.900 | 0.900 | 1.000 | 1.000 | 1.000 |
| distractor | 10 | 0.900 | 0.900 | 0.900 | 1.000 | 1.000 | 1.000 | 0.800 | 0.800 | 0.800 |
| implicita | 10 | 0.200 | 0.200 | 0.300 | 1.000 | 1.000 | 0.800 | 1.000 | 0.900 | 0.800 |
| tabla | 10 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.900 | 0.800 | 0.900 |
| profunda | 10 | 0.900 | 0.900 | 0.900 | 1.000 | 0.900 | 1.000 | 1.000 | 1.000 | 1.000 |

## Generación

Búsqueda híbrida, chunk 800.

### Variante `sin_contexto`

| Métrica | Valor |
| --- | ---: |
| Preguntas | 80 (70 con respuesta, 10 sin respuesta) |
| Palabras clave correctas | 0.914 |
| Precisión de citas | 1.000 |
| Rechazo correcto | 1.000 |
| Falsos rechazos | 6 |
| Fidelidad (juez) | 0.953 (64 juzgadas, 0 sin juzgar) |
| Primer token (media) | 1.44 s |
| Tiempo total (media) | 1.82 s |

Fallos:
- p02: No lo sé con la información de los documentos.
- p08: No lo sé con la información de los documentos.
- p09: No lo sé con la información de los documentos.
- i04: No lo sé con la información de los documentos.
- i08: No lo sé con la información de los documentos.
- i10: No lo sé con la información de los documentos.

Sin respaldo según el juez:
- i07: El teléfono de soporte del K3 Pro es el 900 101 203
- f02: Las placas solares cubrieron el 38 % de la electricidad consumida en 2025
- f03: La tasa de devoluciones en 2025 fue del 1,9 % de los aparatos vendidos

### Variante `base`

| Métrica | Valor |
| --- | ---: |
| Preguntas | 80 (70 con respuesta, 10 sin respuesta) |
| Palabras clave correctas | 0.971 |
| Precisión de citas | 1.000 |
| Rechazo correcto | 1.000 |
| Falsos rechazos | 2 |
| Fidelidad (juez) | 0.941 (68 juzgadas, 0 sin juzgar) |
| Primer token (media) | 0.93 s |
| Tiempo total (media) | 1.13 s |

Fallos:
- p08: No lo sé con la información de los documentos.
- p09: No lo sé con la información de los documentos.

Sin respaldo según el juez:
- i04: Para descalcificar el Termia K3 Pro se debe usar el sobre de descalcificador Termia disuelto en un litro de agua
- i07: El teléfono de soporte del K3 Pro es el 900 101 203
- f02: Las placas solares cubrieron el 38 % de la electricidad consumida en 2025
- f03: La tasa de devoluciones en 2025 fue del 1,9 %

### Variante `contextual`

| Métrica | Valor |
| --- | ---: |
| Preguntas | 80 (70 con respuesta, 10 sin respuesta) |
| Palabras clave correctas | 0.971 |
| Precisión de citas | 1.000 |
| Rechazo correcto | 1.000 |
| Falsos rechazos | 2 |
| Fidelidad (juez) | 0.941 (68 juzgadas, 0 sin juzgar) |
| Primer token (media) | 0.93 s |
| Tiempo total (media) | 1.12 s |

Fallos:
- p02: No lo sé con la información de los documentos.
- p09: No lo sé con la información de los documentos.

Sin respaldo según el juez:
- i04: Para descalcificar el Termia K3 Pro se debe usar el sobre de descalcificador Termia disuelto en un litro de agua
- i07: El teléfono de soporte del K3 Pro es el 900 101 203
- f02: Las placas solares cubrieron el 38 % de la electricidad consumida en 2025
- f03: La tasa de devoluciones en 2025 fue del 1,9 % de los aparatos vendidos
