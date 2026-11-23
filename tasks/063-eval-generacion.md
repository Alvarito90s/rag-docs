# 063 · Evaluación de la generación
Fase: 6 · Depende de: 062

## Objetivo
Pasar todas las preguntas por el `Answerer` y medir: palabras clave en la respuesta, precisión de citas, rechazo correcto ("No lo sé") y latencia (primer token y total).

## Archivos
- modificar: `src/docuchat/evaluation/runner.py` (solo AÑADIR)
- crear: `tests/evaluation/test_runner_generation.py`

## Interfaz
```python
import time
from collections.abc import Callable

from docuchat.evaluation.metrics import citation_counts, keywords_hit, ratio
from docuchat.generation.answer import Answerer


@dataclass(frozen=True)
class QuestionResult:
    """Resultado de una pregunta."""

    id: str
    answerable: bool
    answer: str
    no_answer: bool
    keywords_ok: bool | None  # None en preguntas sin respuesta
    citations_correct: int
    citations_total: int
    first_token_s: float | None  # None si no llegó ningún trozo
    total_s: float


@dataclass(frozen=True)
class GenerationReport:
    """Métricas agregadas de generación."""

    questions: int
    answerable: int
    unanswerable: int
    keyword_accuracy: float | None
    citation_precision: float | None
    refusal_accuracy: float | None
    false_refusals: int
    avg_first_token_s: float | None
    avg_total_s: float
    results: list[QuestionResult] = field(default_factory=list)


def evaluate_generation(
    answerer: Answerer,
    questions: Sequence[EvalQuestion],
    clock: Callable[[], float] = time.perf_counter,
) -> GenerationReport:
    """Responde cada pregunta y agrega las métricas."""
```

## Comportamiento
1. Por pregunta, en este orden EXACTO de llamadas a `clock` (los tests usan un reloj falso): `t0 = clock()`; dentro de `on_token`, SOLO en el primer trozo, `first = clock()`; tras `answerer.ask(...)`, `end = clock()`. `first_token_s = first - t0` (o `None` si no hubo trozos) y `total_s = end - t0`.
2. Con respuesta (`answerable`): `keywords_ok = keywords_hit(answer.text, q.answer_keywords)` (un "No lo sé" no las contiene, así que cuenta como fallo); `citations_correct, citations_total = citation_counts(answer.sources, q.expected_doc, q.expected_page)`.
3. Sin respuesta: `keywords_ok = None`, citas `0, 0`.
4. Agregados:
   - `keyword_accuracy = ratio(nº keywords_ok True, answerable)`.
   - `citation_precision = ratio(Σ citations_correct, Σ citations_total)` (solo preguntas con respuesta).
   - `refusal_accuracy = ratio(nº sin respuesta con no_answer, unanswerable)`.
   - `false_refusals` = preguntas con respuesta y `no_answer`.
   - `avg_first_token_s` = media de los `first_token_s` que no son `None` (o `None` si no hay ninguno). `avg_total_s` = media de `total_s` (0.0 si no hay preguntas).
5. `results` en el orden de `questions`. Los errores del LLM o de embeddings se propagan.

## Tests obligatorios
`tests/evaluation/test_runner_generation.py`. NO cambies los valores esperados. Nada de red.
```python
class FakeRetriever:  # devuelve siempre CONTEXT
    def search(self, query: str, top_k: int) -> list[SearchResult]:
        return CONTEXT[:top_k]


class QueueChat:  # cada llamada a stream devuelve la siguiente respuesta de la cola
    def __init__(self, answers: list[list[str]]) -> None:
        self.answers = list(answers)

    def stream(self, messages: Sequence[Message]) -> Iterator[str]:
        yield from self.answers.pop(0)


def fake_clock(values: list[float]) -> Callable[[], float]:
    it = iter(values)
    return lambda: next(it)
```
`CONTEXT = [mk("a.pdf", 1, "Alfa."), mk("b.md", 2, "Beta.")]` (helper `mk` como en `test_prompts.py`). `A = EvalQuestion(id="q01", question="¿Alfa?", expected_doc="a.pdf", expected_page=1, answer_keywords=["alfa"], answerable=True)`, `U = EvalQuestion(id="u01", question="¿Capital de Francia?", answerable=False)`. `Answerer(FakeRetriever(), chat, top_k=5, context_max_chars=6000)`.
1. Todo bien: `QueueChat([["Es alfa ", "[1]."], [NO_ANSWER]])`, reloj `[0.0, 0.5, 2.0, 10.0, 10.25, 11.0]`, preguntas `[A, U]` → `questions == 2`, `answerable == 1`, `unanswerable == 1`, `keyword_accuracy == 1.0`, `citation_precision == 1.0`, `refusal_accuracy == 1.0`, `false_refusals == 0`, `avg_first_token_s == pytest.approx(0.375)`, `avg_total_s == pytest.approx(1.5)`.
2. Detalle del 1: `results[0]` → `id == "q01"`, `answer == "Es alfa [1]."`, `keywords_ok is True`, citas `1, 1`, `first_token_s == 0.5`, `total_s == 2.0`; `results[1]` → `no_answer is True`, `keywords_ok is None`, citas `0, 0`.
3. Todo mal: `QueueChat([[NO_ANSWER], ["Es París [2]."]])`, reloj `[0, 1, 2, 3, 4, 5]` → `keyword_accuracy == 0.0`, `false_refusals == 1`, `citation_precision is None` (0 citas en preguntas con respuesta), `refusal_accuracy == 0.0`.
4. Citas a medias: `QueueChat([["alfa [1][2]."]])`, reloj `[0, 1, 2]`, preguntas `[A]` → `citation_precision == 0.5`.
5. Sin trozos: `QueueChat([[]])`, reloj `[0.0, 1.0]`, preguntas `[A]` → `results[0].first_token_s is None`, `avg_first_token_s is None`, `avg_total_s == 1.0`, `results[0].no_answer is True`.
6. Sin preguntas: `evaluate_generation(answerer, [])` → `questions == 0`, todas las ratios `None`, `avg_total_s == 0.0`.

## Aceptación
- [ ] `uv run pytest -q tests/evaluation/test_runner_generation.py` → 6 passed
- [ ] `uv run pytest -q` pasa entero
- [ ] `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src` sin errores

## Fuera de alcance
Informe y script (064). No toques lo añadido en la 062.
