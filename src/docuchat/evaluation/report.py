"""Renderizado de informes de evaluación en Markdown."""

import re
from collections.abc import Mapping, Sequence

from docuchat.evaluation.repeats import RunsSummary, summarize_runs
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


def render_runs_table(summary: RunsSummary) -> str:
    """Tabla Markdown de media, mínimo y máximo, más la línea de pasadas e inestables."""
    lines = [
        "| Métrica | Media | Mín | Máx |",
        "| --- | ---: | ---: | ---: |",
        f"| Palabras clave correctas | {fmt(summary.keyword_accuracy.mean)} "
        f"| {fmt(summary.keyword_accuracy.low)} | {fmt(summary.keyword_accuracy.high)} |",
        f"| Precisión de citas | {fmt(summary.citation_precision.mean)} "
        f"| {fmt(summary.citation_precision.low)} | {fmt(summary.citation_precision.high)} |",
        f"| Rechazo correcto | {fmt(summary.refusal_accuracy.mean)} "
        f"| {fmt(summary.refusal_accuracy.low)} | {fmt(summary.refusal_accuracy.high)} |",
        f"| Falsos rechazos | {fmt(summary.false_refusals.mean, 2)} "
        f"| {fmt(summary.false_refusals.low, 0)} | {fmt(summary.false_refusals.high, 0)} |",
    ]
    if summary.faithfulness.mean is not None:
        lines.append(
            f"| Fidelidad (juez) | {fmt(summary.faithfulness.mean)} "
            f"| {fmt(summary.faithfulness.low)} | {fmt(summary.faithfulness.high)} |"
        )
    lines.extend(
        [
            f"| Tiempo total (media) | {fmt_seconds(summary.avg_total_s.mean)} "
            f"| {fmt_seconds(summary.avg_total_s.low)} | {fmt_seconds(summary.avg_total_s.high)} |",
            "",
            f"Pasadas: {summary.runs} · Preguntas inestables: "
            f"{', '.join(summary.unstable) if summary.unstable else '\u2014'}",
        ]
    )
    return "\n".join(lines)


def _has_variant_reports(reports: Sequence[RetrievalReport]) -> bool:
    """True si algún informe tiene variant != 'base'."""
    return any(r.variant != "base" for r in reports)


def render_retrieval_table(reports: Sequence[RetrievalReport]) -> str:
    """Renderiza la tabla de métricas de recuperación en Markdown."""
    if _has_variant_reports(reports):
        lines = [
            "| Variante | Chunk | Modo | Chunks | Hit@1 | Hit@5 | MRR@10 | Fallos (top 5) |",
            "| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |",
        ]
        for r in reports:
            misses = ", ".join(r.misses) if r.misses else "\u2014"
            lines.append(
                f"| {r.variant} | {r.chunk_size} | {r.mode} | {r.chunks} "
                f"| {fmt(r.hit_at_1)} | {fmt(r.hit_at_5)} | {fmt(r.mrr)} "
                f"| {misses} |"
            )
    else:
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
    ]

    # Insertar fila de fidelidad después de "Falsos rechazos"
    if report.judged + report.unjudged > 0:
        lines.append(
            f"| Fidelidad (juez) | {fmt(report.faithfulness)} "
            f"({report.judged} juzgadas, {report.unjudged} sin juzgar) |"
        )

    lines.extend(
        [
            f"| Primer token (media) | {fmt_seconds(report.avg_first_token_s)} |",
            f"| Tiempo total (media) | {fmt_seconds(report.avg_total_s)} |",
        ]
    )

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

    # Mostrar respuestas sin respaldo del juez
    not_supported = [r for r in report.results if r.faithful is False]
    if not_supported:
        lines.append("")
        lines.append("Sin respaldo según el juez:")
        for r in not_supported:
            texto = "; ".join(r.unsupported)
            # Colapsar espacios
            texto = re.sub(r"\s+", " ", texto).strip()
            if len(texto) > 160:
                texto = texto[:160] + "\u2026"
            lines.append(f"- {r.id}: {texto}")

    return "\n".join(lines)


def render_category_table(
    retrieval: Sequence[RetrievalReport],
    generation: GenerationReport | None,
    chunk_size: int,
) -> str:
    """Tabla de Hit@1 por categoría y palabras clave; "" si no aplica."""
    reports = [r for r in retrieval if r.chunk_size == chunk_size]
    if not reports:
        return ""
    cats = list(reports[0].by_category)
    if not cats or cats == ["general"]:
        return ""

    modes = [r.mode for r in reports]
    if _has_variant_reports(reports):
        headers = [
            "Categoría",
            "Preguntas",
        ] + [f"Hit@1 {r.variant}/{r.mode}" for r in reports]
    else:
        headers = ["Categoría", "Preguntas"] + [f"Hit@1 {m}" for m in modes]
    if generation is not None:
        headers.append("Palabras clave")

    sep = ["---"] + ["---:"] * (len(headers) - 1)

    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(sep) + " |")

    for cat in cats:
        cells = [cat, str(reports[0].by_category[cat].questions)]
        for r in reports:
            cs = r.by_category.get(cat)
            if cs is not None:
                cells.append(fmt(cs.hit_at_1))
            else:
                cells.append("\u2014")
        if generation is not None:
            cells.append(fmt(generation.keywords_by_category.get(cat)))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_results(
    *,
    date: str,
    llm_model: str,
    embedding_model: str,
    generation_chunk_size: int | None,
    retrieval: Sequence[RetrievalReport],
    generation: GenerationReport | None,
    generations: Mapping[str, Sequence[GenerationReport]] | None = None,
    questions_file: str = "eval/questions.jsonl",
    judge_model: str | None = None,
) -> str:
    """Renderiza el informe completo de evaluación."""
    header = f"Fecha: {date} \u00b7 LLM: `{llm_model}` \u00b7 Embeddings: `{embedding_model}`"
    if judge_model is not None:
        header += f" \u00b7 Juez: `{judge_model}`"
    lines = [
        "# Resultados de la evaluaci\u00f3n",
        "",
        header,
        "",
    ]
    if judge_model is not None and judge_model == llm_model:
        lines.extend(
            [
                "Nota: el juez es el mismo modelo que responde; la fidelidad es orientativa.",
                "",
            ]
        )
    lines.extend(
        [
            "## Recuperaci\u00f3n",
            "",
            f"Preguntas con respuesta de `{questions_file}`; MRR sobre los 10 primeros resultados.",
            "",
            render_retrieval_table(retrieval),
            "",
        ]
    )

    cs = (
        generation_chunk_size
        if generation_chunk_size is not None
        else (retrieval[0].chunk_size if retrieval else None)
    )
    cat_table = ""
    if cs is not None:
        single_variant = list(generations) == ["base"] if generations else True
        single_pass = single_variant and len(generations["base"]) == 1 if generations else True
        if generation is not None and not generations:
            gen_for_cat = generation
        elif single_variant and single_pass and generations:
            gen_for_cat = generations["base"][0]
        else:
            gen_for_cat = None
        cat_table = render_category_table(retrieval, gen_for_cat, cs)
    if cat_table:
        lines.extend(["### Por categor\u00eda (chunk " + str(cs) + ")", "", cat_table, ""])

    # Sección de generación
    lines.append("## Generaci\u00f3n")
    lines.append("")
    if generations is None:
        if generation is None:
            lines.append("No ejecutada (--skip-llm).")
        else:
            lines.append(f"B\u00fasqueda h\u00edbrida, chunk {generation_chunk_size}.")
            lines.append("")
            lines.append(render_generation_table(generation))
    elif list(generations) == ["base"]:
        if len(generations["base"]) > 1:
            lines.append(f"B\u00fasqueda h\u00edbrida, chunk {generation_chunk_size}.")
            lines.append("")
            lines.append(render_runs_table(summarize_runs(generations["base"])))
        else:
            lines.append(f"B\u00fasqueda h\u00edbrida, chunk {generation_chunk_size}.")
            lines.append("")
            lines.append(render_generation_table(generations["base"][0]))
    else:
        lines.append(f"B\u00fasqueda h\u00edbrida, chunk {generation_chunk_size}.")
        for v, runs in generations.items():
            lines.append("")
            lines.append(f"### Variante `{v}`")
            lines.append("")
            if len(runs) > 1:
                lines.append(render_runs_table(summarize_runs(runs)))
            else:
                lines.append(render_generation_table(runs[0]))

    return "\n".join(lines) + "\n"
