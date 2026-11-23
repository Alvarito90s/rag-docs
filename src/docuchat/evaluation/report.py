"""Renderizado de informes de evaluación en Markdown."""

from collections.abc import Sequence

from docuchat.evaluation.runner import GenerationReport, RetrievalReport


def fmt(value: float | None, digits: int = 3) -> str:
    """Formatea un valor numérico con `digits` decimales, o '—' si es None."""
    if value is None:
        return "\u2014"
    return f"{value:.{digits}f}"


def fmt_seconds(value: float | None) -> str:
    """Formatea un tiempo en segundos con 2 decimales, o '—' si es None."""
    if value is None:
        return "\u2014"
    return f"{value:.2f} s"


def render_retrieval_table(reports: Sequence[RetrievalReport]) -> str:
    """Renderiza la tabla de métricas de recuperación en Markdown."""
    lines = [
        "| Chunk | Modo | Chunks | Hit@1 | Hit@5 | MRR@10 | Fallos (top 5) |",
        "| ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for r in reports:
        misses = ", ".join(r.misses) if r.misses else "\u2014"
        lines.append(
            f"| {r.chunk_size} | {r.mode} | {r.chunks} "
            f"| {fmt(r.hit_at_1)} | {fmt(r.hit_at_5)} | {fmt(r.mrr)} "
            f"| {misses} |"
        )
    return "\n".join(lines)


def render_generation_table(report: GenerationReport) -> str:
    """Renderiza la tabla de métricas de generación en Markdown."""
    lines = [
        "| M\u00e9trica | Valor |",
        "| --- | ---: |",
        f"| Preguntas | {report.questions} "
        f"({report.answerable} con respuesta, {report.unanswerable} sin respuesta) |",
        f"| Palabras clave correctas | {fmt(report.keyword_accuracy)} |",
        f"| Precisi\u00f3n de citas | {fmt(report.citation_precision)} |",
        f"| Rechazo correcto | {fmt(report.refusal_accuracy)} |",
        f"| Falsos rechazos | {report.false_refusals} |",
        f"| Primer token (media) | {fmt_seconds(report.avg_first_token_s)} |",
        f"| Tiempo total (media) | {fmt_seconds(report.avg_total_s)} |",
    ]

    # Mostrar fallos si hay preguntas con respuesta y keywords_ok es False
    failures = [r for r in report.results if r.answerable and r.keywords_ok is False]
    if failures:
        lines.append("")
        lines.append("Fallos:")
        for f in failures:
            answer = " ".join(f.answer.split())
            if len(answer) > 120:
                answer = answer[:120] + "\u2026"
            lines.append(f"- {f.id}: {answer}")

    return "\n".join(lines)


def render_results(
    *,
    date: str,
    llm_model: str,
    embedding_model: str,
    generation_chunk_size: int | None,
    retrieval: Sequence[RetrievalReport],
    generation: GenerationReport | None,
) -> str:
    """Renderiza el informe completo de evaluación."""
    lines = [
        "# Resultados de la evaluaci\u00f3n",
        "",
        f"Fecha: {date} \u00b7 LLM: `{llm_model}` \u00b7 Embeddings: `{embedding_model}`",
        "",
        "## Recuperaci\u00f3n",
        "",
        "Preguntas con respuesta de `eval/questions.jsonl`; MRR sobre los 10 primeros resultados.",
        "",
        render_retrieval_table(retrieval),
        "",
        "## Generaci\u00f3n",
        "",
    ]
    if generation is None:
        lines.append("No ejecutada (--skip-llm).")
    else:
        lines.append(f"B\u00fasqueda h\u00edbrida, chunk {generation_chunk_size}.")
        lines.append("")
        lines.append(render_generation_table(generation))
    return "\n".join(lines) + "\n"
