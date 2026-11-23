# 064 · Informe y script `eval/run_eval.py`
Fase: 6 · Depende de: 063

## Objetivo
Ejecutar la comparativa completa (tamaños de chunk × modos de búsqueda, más la generación) y escribir `eval/results.md` y `eval/results.json`.

## Archivos
Excepción a la regla de 3 archivos: `eval/run_eval.py` es un envoltorio de 6 líneas.
- crear: `src/docuchat/evaluation/report.py`
- crear: `src/docuchat/evaluation/run.py`
- crear: `eval/run_eval.py`
- crear: `tests/evaluation/test_report_run.py`

## Interfaz
`report.py`:
```python
def fmt(value: float | None, digits: int = 3) -> str:
    """'—' si None; si no, con `digits` decimales."""

def fmt_seconds(value: float | None) -> str:
    """'—' si None; si no, '0.46 s'."""

def render_retrieval_table(reports: Sequence[RetrievalReport]) -> str: ...
def render_generation_table(report: GenerationReport) -> str: ...
def render_results(
    *,
    date: str,
    llm_model: str,
    embedding_model: str,
    generation_chunk_size: int | None,
    retrieval: Sequence[RetrievalReport],
    generation: GenerationReport | None,
) -> str: ...
```
`run.py`:
```python
def run_evaluation(
    base: Settings,
    questions: Sequence[EvalQuestion],
    *,
    chunk_sizes: Sequence[int],
    modes: Sequence[SearchMode],
    data_root: Path,
    generation_chunk_size: int | None,
    embedder: Embedder | None = None,
    chat: ChatModel | None = None,
) -> tuple[list[RetrievalReport], GenerationReport | None]: ...

def main(argv: list[str] | None = None) -> int: ...
```
`eval/run_eval.py` (contenido exacto):
```python
"""Evalúa DocuChat con eval/questions.jsonl y escribe eval/results.md."""

import sys

from docuchat.evaluation.run import main

if __name__ == "__main__":
    sys.exit(main())
```

## Comportamiento
1. `fmt(0.84375)` → `"0.844"`; `fmt_seconds(0.456)` → `"0.46 s"`; ambos con `None` → `"—"`.
2. `render_retrieval_table` (líneas unidas con `"\n"`, sin salto final):
   ```
   | Chunk | Modo | Chunks | Hit@1 | Hit@5 | MRR@10 | Fallos (top 5) |
   | ---: | --- | ---: | ---: | ---: | ---: | --- |
   | 800 | bm25 | 26 | 0.844 | 1.000 | 0.909 | — |
   ```
   Una fila por informe, en orden; `misses` unidos con `", "` o `—` si está vacío.
3. `render_generation_table` (líneas con `"\n"`):
   ```
   | Métrica | Valor |
   | --- | ---: |
   | Preguntas | 42 (32 con respuesta, 10 sin respuesta) |
   | Palabras clave correctas | 0.969 |
   | Precisión de citas | 1.000 |
   | Rechazo correcto | 1.000 |
   | Falsos rechazos | 1 |
   | Primer token (media) | 0.46 s |
   | Tiempo total (media) | 0.61 s |
   ```
   Si hay preguntas con respuesta y `keywords_ok is False`, añade una línea en blanco, `"Fallos:"` y una línea `f"- {id}: {answer}"` por cada una (respuesta en una línea con `" ".join(answer.split())`, cortada a 120 caracteres con `"…"` si es más larga).
4. `render_results` devuelve (con `"\n"` y un salto final):
   ```
   # Resultados de la evaluación

   Fecha: {date} · LLM: `{llm_model}` · Embeddings: `{embedding_model}`

   ## Recuperación

   Preguntas con respuesta de `eval/questions.jsonl`; MRR sobre los 10 primeros resultados.

   {tabla de recuperación}

   ## Generación

   {si generation es None: "No ejecutada (--skip-llm)." ; si no: f"Búsqueda híbrida, chunk {generation_chunk_size}." + línea en blanco + tabla de generación}
   ```
5. `run_evaluation`: para cada tamaño: `s = eval_settings(base, data_root, cs)`, `chunks = build_eval_index(s, embedder)`, `searcher = build_searcher(s, embedder=embedder)` y un `evaluate_retrieval` por modo (en el orden recibido). Si `generation_chunk_size` no es `None`: `s = eval_settings(base, data_root, generation_chunk_size)`; si ese tamaño no estaba en `chunk_sizes`, `build_eval_index(s, embedder)`; `answerer = build_answerer(s, retriever=build_searcher(s, embedder=embedder), chat=chat)` y `evaluate_generation(answerer, questions)`. Imprime una línea de progreso por paso (`print`).
6. `main` (con `argparse`): `--questions` (`eval/questions.jsonl`), `--documents-dir` (`samples`), `--data-root` (`data/eval`), `--chunk-sizes` (`"500,800,1200"`), `--modes` (`"hybrid,vector,bm25"`), `--generation-chunk-size` (`800`), `--skip-llm` (flag: sin generación), `--out` (`eval/results.md`), `--json` (`eval/results.json`). `base = get_settings().model_copy(update={"documents_dir": Path(documents_dir)})`. Escribe el Markdown (UTF-8) y el JSON (`{"date", "llm_model", "embedding_model", "retrieval": [asdict...], "generation": asdict o None}`, `ensure_ascii=False`, `indent=2`). `date = datetime.now().strftime("%Y-%m-%d %H:%M")`. Devuelve 0. `OpenAIError` o `EmbeddingError` → `print(f"Error con el servidor de modelos: {type(e).__name__}: {e}", file=sys.stderr)` y devuelve 1.

## Tests obligatorios
`tests/evaluation/test_report_run.py`. NO cambies los valores esperados. Nada de red. `FakeEmbedder` como en la 062; `RefuseChat` cuyo `stream` siempre emite `NO_ANSWER`.
1. `fmt(0.84375) == "0.844"`, `fmt(None) == "—"`, `fmt_seconds(0.456) == "0.46 s"`, `fmt_seconds(None) == "—"`.
2. `render_retrieval_table([RetrievalReport(800, "bm25", 26, 32, 0.84375, 1.0, 0.9088541666666666, []), RetrievalReport(500, "vector", 45, 32, 0.9, 0.95, 0.92, ["q03", "q17"])])` → las 4 líneas exactas (cabecera, separador, `| 800 | bm25 | 26 | 0.844 | 1.000 | 0.909 | — |`, `| 500 | vector | 45 | 0.900 | 0.950 | 0.920 | q03, q17 |`).
3. `render_generation_table` con un `GenerationReport(42, 32, 10, 0.96875, 1.0, 1.0, 1, 0.456, 0.61, results=[QuestionResult("q17", True, "No lo sé con la información de los documentos.", True, False, 0, 0, 0.4, 0.5)])` → contiene exactamente las 9 líneas de la tabla del punto 3 del comportamiento, y termina en `"Fallos:\n- q17: No lo sé con la información de los documentos."`.
4. `render_results(..., generation=None)` contiene `"# Resultados de la evaluación"`, `"## Recuperación"`, `"No ejecutada (--skip-llm)."` y termina en `"\n"`.
5. `run_evaluation(base, preguntas, chunk_sizes=[800], modes=[SearchMode.BM25], data_root=tmp_path / "eval", generation_chunk_size=None, embedder=FakeEmbedder())` → un informe con `hit_at_1 == pytest.approx(27 / 32)` y generación `None`.
6. Con `generation_chunk_size=800` y `chat=RefuseChat()` → `generation.questions == 42`, `false_refusals == 32`, `refusal_accuracy == 1.0`.
7. `main`: `monkeypatch.setattr("docuchat.index.indexer.make_embedder", lambda s: FakeEmbedder())` y lo mismo en `"docuchat.retrieval.searcher.make_embedder"`; `main(["--skip-llm", "--chunk-sizes", "800", "--modes", "bm25", "--data-root", str(tmp_path / "d"), "--out", str(tmp_path / "r.md"), "--json", str(tmp_path / "r.json"), "--questions", str(QUESTIONS), "--documents-dir", str(SAMPLES)])` → `0`; `r.md` contiene `"| 800 | bm25 | 26 | 0.844 | 1.000 | 0.909 | — |"`; `json.loads(r.json)["retrieval"][0]["hit_at_1"] == pytest.approx(27 / 32)` y `["generation"] is None`.
8. `main` con un embedder que lanza `APIConnectionError` (mismos parches) → devuelve `1` y `capsys` (stderr) contiene `"Error con el servidor de modelos: APIConnectionError"`.

## Aceptación
- [ ] `uv run pytest -q tests/evaluation/test_report_run.py` → 8 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores
- [ ] `uv run python eval/run_eval.py --help` muestra las opciones
- [ ] (humano, con oMLX) `uv run python eval/run_eval.py` → escribe `eval/results.md` y `eval/results.json` (tarda unos minutos); revisarlos y versionarlos

## Fuera de alcance
README y Docker (Fase 7). No toques `runner.py`, `metrics.py` ni `dataset.py`.
