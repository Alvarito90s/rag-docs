"""Ejecución y reporting de evaluación de DocuChat."""

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from openai import OpenAIError

from docuchat.config import Settings, get_settings
from docuchat.evaluation.dataset import EvalQuestion, load_questions
from docuchat.evaluation.report import render_results
from docuchat.evaluation.runner import (
    GenerationReport,
    RetrievalReport,
    build_eval_index,
    eval_settings,
    evaluate_generation,
    evaluate_retrieval,
)
from docuchat.generation.llm_client import ChatModel
from docuchat.index.embeddings import Embedder, EmbeddingError
from docuchat.retrieval.searcher import SearchMode, build_searcher


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
    """Ejecuta la evaluación completa y devuelve los informes."""
    from docuchat.generation.answer import build_answerer

    reports: list[RetrievalReport] = []

    for cs in chunk_sizes:
        print(f"Indexando chunks de {cs}...")
        s = eval_settings(base, data_root, cs)
        chunks = build_eval_index(s, embedder)
        print(f"  {chunks} chunks creados")
        searcher = build_searcher(s, embedder=embedder)
        for mode in modes:
            print(f"  Evaluando modo {mode.value}...")
            report = evaluate_retrieval(searcher, questions, mode, chunk_size=cs, chunks=chunks)
            reports.append(report)

    generation: GenerationReport | None = None
    if generation_chunk_size is not None:
        print(f"Preparando generación con chunk {generation_chunk_size}...")
        gen_s = eval_settings(base, data_root, generation_chunk_size)
        if generation_chunk_size not in chunk_sizes:
            build_eval_index(gen_s, embedder)
        retriever = build_searcher(gen_s, embedder=embedder)
        answerer = build_answerer(gen_s, retriever=retriever, chat=chat)
        print("  Evaluando generación...")
        generation = evaluate_generation(answerer, questions)

    return reports, generation


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada CLI para la evaluación."""
    parser = argparse.ArgumentParser(description="Evalúa DocuChat con eval/questions.jsonl")
    parser.add_argument(
        "--questions", default="eval/questions.jsonl", help="Ruta al dataset de preguntas (JSONL)"
    )
    parser.add_argument("--documents-dir", default="samples", help="Directorio con los documentos")
    parser.add_argument(
        "--data-root", default="data/eval", help="Raíz para los datos de evaluación"
    )
    parser.add_argument(
        "--chunk-sizes", default="500,800,1200", help="Tamaños de chunk separados por coma"
    )
    parser.add_argument(
        "--modes", default="hybrid,vector,bm25", help="Modos de búsqueda separados por coma"
    )
    parser.add_argument(
        "--generation-chunk-size", type=int, default=800, help="Tamaño de chunk para la generación"
    )
    parser.add_argument("--skip-llm", action="store_true", help="Omitir la etapa de generación")
    parser.add_argument("--out", default="eval/results.md", help="Ruta del informe Markdown")
    parser.add_argument("--json", default="eval/results.json", help="Ruta del informe JSON")

    args = parser.parse_args(argv)

    base = get_settings().model_copy(update={"documents_dir": Path(args.documents_dir)})

    questions = load_questions(Path(args.questions))

    chunk_sizes = [int(x) for x in args.chunk_sizes.split(",")]
    modes = [SearchMode(m.strip()) for m in args.modes.split(",")]
    generation_chunk_size = None if args.skip_llm else args.generation_chunk_size
    data_root = Path(args.data_root)

    try:
        reports, generation = run_evaluation(
            base,
            questions,
            chunk_sizes=chunk_sizes,
            modes=modes,
            data_root=data_root,
            generation_chunk_size=generation_chunk_size,
        )
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
        retrieval=reports,
        generation=generation,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")

    json_data = {
        "date": date,
        "llm_model": base.llm_model,
        "embedding_model": base.embedding_model,
        "retrieval": [asdict(r) for r in reports],
        "generation": asdict(generation) if generation is not None else None,
    }
    json_path = Path(args.json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return 0
