"""Ejecución y reporting de evaluación de DocuChat."""

import argparse
import dataclasses
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from openai import OpenAIError

from docuchat.config import Settings, get_settings
from docuchat.evaluation.dataset import EvalQuestion, load_questions
from docuchat.evaluation.judge import Judge
from docuchat.evaluation.report import render_results
from docuchat.evaluation.runner import (
    GenerationReport,
    RetrievalReport,
    build_eval_index,
    eval_settings,
    evaluate_generation,
    evaluate_retrieval,
)
from docuchat.evaluation.variants import parse_variants, variant_settings
from docuchat.generation.answer import build_answerer
from docuchat.generation.llm_client import ChatModel, make_chat_model
from docuchat.index.embeddings import Embedder, EmbeddingError
from docuchat.retrieval.searcher import SearchMode, build_searcher


@dataclass(frozen=True)
class VariantResult:
    """Informes de una variante: recuperación y una generación por pasada."""

    variant: str
    retrieval: list[RetrievalReport]
    generations: list[GenerationReport]  # vacía si no se evalúa la generación


def run_variant(
    base: Settings,
    questions: list[EvalQuestion],
    *,
    variant: str,
    chunk_sizes: list[int],
    modes: list[SearchMode],
    data_root: Path,
    generation_chunk_size: int | None,
    runs: int = 1,
    embedder: Embedder | None = None,
    chat: ChatModel | None = None,
    judge: Judge | None = None,
) -> VariantResult:
    """Indexa, evalúa recuperación y generación con una variante."""
    settings = variant_settings(base, variant)
    reports: list[RetrievalReport] = []

    if runs < 1:
        raise ValueError("runs debe ser al menos 1")

    for cs in chunk_sizes:
        print(f"[{variant}] Indexando chunks de {cs}...")
        s = eval_settings(settings, data_root / variant, cs)
        chunks = build_eval_index(s, embedder)
        print(f"[{variant}]   {chunks} chunks creados")
        searcher = build_searcher(s, embedder=embedder)
        for mode in modes:
            print(f"[{variant}]   Evaluando modo {mode.value}...")
            report = evaluate_retrieval(searcher, questions, mode, chunk_size=cs, chunks=chunks)
            reports.append(dataclasses.replace(report, variant=variant))

    generations: list[GenerationReport] = []
    if generation_chunk_size is not None:
        print(f"[{variant}] Preparando generación con chunk {generation_chunk_size}...")
        gen_s = eval_settings(settings, data_root / variant, generation_chunk_size)
        if generation_chunk_size not in chunk_sizes:
            build_eval_index(gen_s, embedder)
        retriever = build_searcher(gen_s, embedder=embedder)
        answerer = build_answerer(gen_s, retriever=retriever, chat=chat)
        for i in range(1, runs + 1):
            print(f"[{variant}]   Evaluando generación (pasada {i}/{runs})...")
            gen_report = evaluate_generation(answerer, questions, judge=judge)
            generations.append(dataclasses.replace(gen_report, variant=variant))

    return VariantResult(
        variant=variant,
        retrieval=reports,
        generations=generations,
    )


def run_evaluation(
    base: Settings,
    questions: list[EvalQuestion],
    *,
    chunk_sizes: list[int],
    modes: list[SearchMode],
    data_root: Path,
    generation_chunk_size: int | None,
    embedder: Embedder | None = None,
    chat: ChatModel | None = None,
) -> tuple[list[RetrievalReport], GenerationReport | None]:
    """MISMA firma que ahora; envoltura de run_variant con variant="base"."""
    result = run_variant(
        base,
        questions,
        variant="base",
        chunk_sizes=chunk_sizes,
        modes=modes,
        data_root=data_root,
        generation_chunk_size=generation_chunk_size,
        embedder=embedder,
        chat=chat,
    )
    return result.retrieval, result.generations[0] if result.generations else None


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada CLI para la evaluación."""
    parser = argparse.ArgumentParser(description="Evalúa DocuChat con eval/questions.jsonl")
    parser.add_argument(
        "--questions",
        default="eval/questions.jsonl",
        help="Ruta al dataset de preguntas (JSONL)",
    )
    parser.add_argument(
        "--documents-dir",
        default="samples",
        help="Directorio con los documentos",
    )
    parser.add_argument(
        "--data-root",
        default="data/eval",
        help="Raíz para los datos de evaluación",
    )
    parser.add_argument(
        "--chunk-sizes",
        default="500,800,1200",
        help="Tamaños de chunk separados por coma",
    )
    parser.add_argument(
        "--modes",
        default="hybrid,vector,bm25",
        help="Modos de búsqueda separados por coma",
    )
    parser.add_argument(
        "--generation-chunk-size",
        type=int,
        default=800,
        help="Tamaño de chunk para la generación",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Pasadas de la generación, para medir la variabilidad",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Omitir la etapa de generación",
    )
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Juzga la fidelidad de cada respuesta con un LLM",
    )
    parser.add_argument(
        "--judge-model",
        default=None,
        help="Modelo del juez (por defecto DOCUCHAT_LLM_MODEL)",
    )
    parser.add_argument(
        "--variants",
        default="base",
        help="Variantes separadas por coma (ver evaluation/variants.py)",
    )
    parser.add_argument(
        "--out",
        default="eval/results.md",
        help="Ruta del informe Markdown",
    )
    parser.add_argument(
        "--json",
        default="eval/results.json",
        help="Ruta del informe JSON",
    )

    args = parser.parse_args(argv)

    if args.judge and args.skip_llm:
        parser.error("--judge necesita la generación: quita --skip-llm")

    if args.runs < 1:
        parser.error("--runs debe ser al menos 1")

    try:
        variant_names = parse_variants(args.variants)
    except ValueError as e:
        parser.error(str(e))

    base = get_settings().model_copy(update={"documents_dir": Path(args.documents_dir)})

    questions = load_questions(Path(args.questions))

    chunk_sizes = [int(x) for x in args.chunk_sizes.split(",")]
    modes = [SearchMode(m.strip()) for m in args.modes.split(",")]
    generation_chunk_size = None if args.skip_llm else args.generation_chunk_size
    data_root = Path(args.data_root)

    judge: Judge | None = None
    judge_model: str | None = None
    if args.judge:
        judge_model = args.judge_model or base.llm_model
        judge = Judge(make_chat_model(base.model_copy(update={"llm_model": judge_model})))

    try:
        all_reports: list[RetrievalReport] = []
        all_generations: dict[str, list[GenerationReport]] = {}
        for var_name in variant_names:
            result = run_variant(
                base,
                questions,
                variant=var_name,
                chunk_sizes=chunk_sizes,
                modes=modes,
                data_root=data_root,
                generation_chunk_size=generation_chunk_size,
                runs=args.runs,
                judge=judge,
            )
            all_reports.extend(result.retrieval)
            if result.generations:
                all_generations[var_name] = result.generations
    except (OpenAIError, EmbeddingError) as e:
        print(
            f"Error con el servidor de modelos: {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return 1

    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    markdown = render_results(
        date=date,
        llm_model=base.llm_model,
        embedding_model=base.embedding_model,
        generation_chunk_size=generation_chunk_size,
        retrieval=all_reports,
        generation=None,
        generations=all_generations or None,
        questions_file=args.questions,
        judge_model=judge_model,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")

    first_gen = None
    for _v, gens in all_generations.items():
        if gens:
            first_gen = gens[0]
            break

    json_data: dict[str, object] = {
        "date": date,
        "llm_model": base.llm_model,
        "embedding_model": base.embedding_model,
        "variants": variant_names,
        "retrieval": [asdict(r) for r in all_reports],
        "generation": asdict(first_gen) if first_gen is not None else None,
        "generations": {v: [asdict(g) for g in gens] for v, gens in all_generations.items()},
    }
    json_path = Path(args.json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return 0
