# DocuChat Local

[![CI](https://github.com/Alvarito90s/RAG-Docs/actions/workflows/ci.yml/badge.svg)](https://github.com/Alvarito90s/RAG-Docs/actions/workflows/ci.yml)

**English** · [Español](README.md)

Ask questions about your documents without them ever leaving your computer. DocuChat answers with `[n]` citations that link to the exact page of the source document, and says "I don't know" when the answer isn't there.

![Demo: question, streamed answer and a citation that opens the PDF at the right page](docs/demo.gif)

## What it does

- Indexes PDF, DOCX, Markdown and TXT files from a folder. Indexing is incremental: only changed files are reprocessed.
- Hybrid search: vector (ChromaDB) and BM25 (SQLite FTS5), merged with Reciprocal Rank Fusion and reordered by a reranker.
- Every chunk is indexed with its document's name and first sentence. That finds pages that never name the product they talk about, without calling the LLM.
- Streamed answers with citations resolved to document and page; in the web UI, a citation opens the PDF at that page.
- CLI (`ingest`, `search`, `ask`, `serve`) and a web UI built with FastAPI and HTMX, no JavaScript framework.
- 100% local: models are served by oMLX on Apple Silicon. No LangChain, LlamaIndex or Haystack.

## How it works

```
documents ─► loaders ─► cleaning ─► chunks (800 chars, 120 overlap) ─► context ─┬─► embeddings ─► ChromaDB
                                                                                └─► BM25 (SQLite FTS5)

question ─┬─► vector search ─┐
          └─► BM25 ──────────┴─► RRF (k=60) ─► reranker (10 candidates) ─► top 5 ─► prompt ─► LLM (streaming)
                                                                                                │
                                                            answer with [n] ─► document and page
```

The context is a line prepended to the chunk only for search: «Documento «manual_hervidor_k1.pdf». Gracias por elegir el hervidor Termia K1.». Answers and citations show the original text.

| Component | Technology |
| --- | --- |
| LLM | `Qwen3.6-35B-A3B-6bit` via oMLX (OpenAI-compatible API) |
| Embeddings | `Qwen3-Embedding-0.6B-4bit-DWQ` (1024 dimensions) |
| Vectors | Persistent ChromaDB, cosine distance |
| Lexical | SQLite FTS5 (persistent BM25, in the standard library) |
| Reranker | `Qwen3-Reranker-0.6B-4bit` via oMLX `POST /v1/rerank` |
| Registry | SQLite (SHA-256 hash per document) |
| Web | FastAPI, Jinja2, HTMX, Server-Sent Events |

## Results

Two evaluations, with the default configuration: hybrid search, reranker and metadata context.

### Hard corpus (v2): what each kind of context buys you

80 questions over the 15 documents in `samples_v2/`, split into 8 categories. It has near-identical manuals for three models, a contract and its amendment, tables, and pages that never name the product they talk about. 70 questions are answerable and 10 are not. The data is in [`eval/questions_v2.jsonl`](eval/questions_v2.jsonl) and the full report in [`eval/results-v2.md`](eval/results-v2.md) (both in Spanish).

The table compares what each kind of context costs at indexing time with how much it improves search. Hybrid search with reranker and chunk size 800; ingestion covers the 15 documents (73 chunks):

| Context for each chunk | LLM calls | Ingestion | Hit@1 | Hit@5 | MRR@10 | Implicit | Distractor | Improve | Worsen |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| None | 0 | 2.6 s | 0.771 | 0.914 | 0.827 | 0.2 | 0.9 | — | — |
| **Metadata (default)** | **0** | **2.6 s** | **0.929** | **0.971** | **0.946** | **1.0** | **1.0** | **13** | **2** |
| One LLM sentence per document | 15 | ≈ 10 s | 0.886 | 0.957 | 0.918 | 0.9 | 0.9 | 11 | 3 |
| One LLM sentence per chunk | 73 | ≈ 100 s | 0.914 | 0.971 | 0.939 | 1.0 | 0.8 | 13 | 3 |

- **Metadata** is «Documento «file name». First sentence of the document.», the same for every chunk of the document. It doesn't call the LLM.
- **Per chunk** is classic contextual retrieval: the LLM reads the start of the document and the page, and writes one or two sentences that place the chunk. Turn it on with `DOCUCHAT_CONTEXTUAL_ENABLED=true`. The first ingestion takes about 40 times longer; after that there is a cache.
- **Per document** was measured with a prototype and is not in the app: it is more expensive and worse than metadata.
- **Improve / Worsen** count the questions whose first result becomes correct or stops being correct compared with no context. Search is deterministic: repeated 3 times, it gives the same result on all 70 questions.

Hit@1 by category (hybrid search with reranker, chunk size 800):

| Category | No context | Metadata | LLM per chunk |
| --- | ---: | ---: | ---: |
| Literal | 1.000 | 0.900 | 1.000 |
| Paraphrase | 0.400 | 0.700 | 0.700 |
| Numeric | 1.000 | 0.900 | 1.000 |
| Distractor | 0.900 | 1.000 | 0.800 |
| Implicit | 0.200 | 1.000 | 1.000 |
| Table | 1.000 | 1.000 | 0.900 |
| Deep | 0.900 | 1.000 | 1.000 |

Generation on v2 (chunk size 800): with metadata, keyword accuracy goes from 0.914 to 0.971 and false refusals from 6 to 2. Citation precision and correct refusals stay at 1.000 with and without context.

How to read it:

- **Implicit questions are the trap.** "How many minutes do you have to wait before switching the K2 back on?" is answered on a page that only says "the kettle". Without context that page looks the same in all three manuals. With the document name in front, search knows which one belongs to the K2.
- **LLM context doesn't beat metadata and costs 40 times more.** Its 3 regressions repeat on every generation of contexts, so they aren't noise. For example, the K1 manual's context says "error codes E1, E2 and E3" and the K2's doesn't, so the question about the K2's E3 finds the K1 first.
- **The 2 metadata regressions** are l09, where the amendment's first sentence ("Adenda al contrato de mantenimiento informático") beats the contract, and n09, where the figure comes from another page of the same report.

### Original corpus (v1)

42 questions over the 7 documents in `samples/`: 32 are answered on a specific page and 10 have no answer in the corpus. The dataset is in [`eval/questions.jsonl`](eval/questions.jsonl) and the full report in [`eval/results.md`](eval/results.md) (both in Spanish).

**Retrieval** (32 answerable questions; MRR over the top 10 results):

| Chunk | Mode | Chunks | Hit@1 | Hit@5 | MRR@10 | Misses (top 5) |
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

**Generation** (hybrid search, chunk size 800):

| Metric | Value |
| --- | ---: |
| Questions | 42 (32 answerable, 10 unanswerable) |
| Keyword accuracy | 0.938 |
| Citation precision | 0.968 |
| Correct refusals | 1.000 |
| False refusals | 1 |
| Time to first token (mean) | 0.75 s |
| Total time (mean) | 0.90 s |

How to read it:

- **Hybrid search gets all 32 right on the first result** with chunk size 800. In v1.0.1, without reranker or context, it stayed at 0.906.
- **v1 generation gets worse on two questions**, even though search always ranks the right page first. Both fail the same way on 2 runs, so it isn't noise. Both are ambiguous questions; the context only changes the order of the other chunks or the fifth one, and that is enough for the LLM to answer differently:
  - q17 ("How long is technical support free?") answers "I don't know" again;
  - q09 answers with what comes in the coffee machine's box, not what the supplier hands over when the contract ends.

  On v2, by contrast, false refusals drop from 6 to 2. The balance is clearly positive, but the LLM is still sensitive to the order of its context.

To rerun the evaluation (with oMLX running; v2 with the judge takes much longer):

```bash
uv run python eval/run_eval.py              # v1: retrieval and generation
uv run python eval/run_eval.py --skip-llm   # v1: retrieval only
uv run python eval/run_eval.py --questions eval/questions_v2.jsonl --documents-dir samples_v2 \
  --variants sin_contexto,base,contextual --judge --out eval/results-v2.md --json eval/results-v2.json
```

Response times in `eval/results-v2.md` were measured with another evaluation running at the same time: don't use them as latency figures.

## Requirements

- A Mac with Apple Silicon (oMLX uses MLX).
- [uv](https://docs.astral.sh/uv/) and Python 3.12.
- oMLX listening on `127.0.0.1:8000`, with an API key and these models downloaded:
  - `Qwen3.6-35B-A3B-6bit`: the weights alone take about 27 GB of unified memory. Any chat model served by oMLX works by changing `DOCUCHAT_LLM_MODEL`.
  - `Qwen3-Embedding-0.6B-4bit-DWQ`.
  - `Qwen3-Reranker-0.6B-4bit`. Without it search still works, in RRF order; turn it off with `DOCUCHAT_RERANK_ENABLED=false`.

## Getting started

```bash
git clone https://github.com/Alvarito90s/RAG-Docs.git
cd RAG-Docs
uv sync
cp .env.example .env                    # put your oMLX key in DOCUCHAT_LLM_API_KEY
uv run python scripts/check_env.py      # checks that oMLX answers with the LLM and the embeddings
uv run docuchat ingest                  # indexes samples/
uv run docuchat ask "¿Qué significa el error E-17 de la cafetera?"
uv run docuchat serve                   # http://127.0.0.1:8001
```

The sample documents and prompts are in Spanish, but questions and documents can be in any language the models handle. To use your own documents, set `DOCUCHAT_DOCUMENTS_DIR` or pass the folder to `ingest`.

## CLI

| Command | What it does |
| --- | --- |
| `docuchat ingest [FOLDER]` | Indexes the folder (incremental). `--reset` rebuilds the index from scratch; `--dry-run` only lists documents and pages. |
| `docuchat search "TEXT"` | Shows the most relevant chunks. `--mode hybrid\|vector\|bm25`, `-k N`. |
| `docuchat ask "QUESTION"` | Streams the answer and lists the cited sources. `-k N` context chunks. |
| `docuchat serve` | Starts the web UI at `http://127.0.0.1:8001`. `--host`, `--port`. |

## Web UI and API

The web UI has two pages: the chat (`/`) and the indexed documents, with a reindex button (`/documents`).

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/api/health` | Status, number of documents and chunks, models |
| GET | `/api/documents` | Indexed documents |
| POST | `/api/search` | Search (`query`, `top_k`, `mode`) |
| POST | `/api/ask` | Answer over Server-Sent Events: `token`, `done` (with sources) or `error` |
| POST | `/api/ingest` | Starts a background indexing job (202) |
| GET | `/api/ingest/{job_id}` | Indexing job status |
| GET | `/files/{source}` | Serves the original document (citations link here with `#page=N`) |

## Docker

MLX needs Metal, so the models can't run inside a container. The image ships only the app and uses the Mac's oMLX through `host.docker.internal`.

```bash
docker compose up --build
```

- Open `http://127.0.0.1:8001` and click reindex under **Documentos**.
- `./samples` is mounted read-only at `/documents`. For your own documents, change that volume in [`compose.yaml`](compose.yaml).
- The index lives in the `docuchat-data` volume, so it survives restarts.
- The key is read from your `.env` at startup. It is never copied into the image: `.dockerignore` excludes it.

If the container can't reach oMLX, check the connection from inside:

```bash
docker compose exec docuchat python -c "from docuchat.env_check import main; raise SystemExit(main())"
```

## Configuration

Everything is configured with `DOCUCHAT_*` variables in `.env`; [`.env.example`](.env.example) has the full list with defaults. The most useful ones:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DOCUCHAT_LLM_API_KEY` | (empty) | oMLX key |
| `DOCUCHAT_LLM_MODEL` | `Qwen3.6-35B-A3B-6bit` | Chat model |
| `DOCUCHAT_EMBEDDING_MODEL` | `Qwen3-Embedding-0.6B-4bit-DWQ` | Embedding model |
| `DOCUCHAT_DOCUMENTS_DIR` | `samples` | Documents folder |
| `DOCUCHAT_DATA_DIR` | `data` | Index (Chroma and SQLite registry) |
| `DOCUCHAT_CHUNK_SIZE` / `DOCUCHAT_CHUNK_OVERLAP` | `800` / `120` | Chunk size and overlap, in characters |
| `DOCUCHAT_TOP_K` | `5` | Chunks passed to the LLM |
| `DOCUCHAT_LLM_TEMPERATURE` | `0` | LLM randomness; 0 gives reproducible answers |
| `DOCUCHAT_LLM_THINKING` | `false` | Qwen reasoning mode (slower) |
| `DOCUCHAT_RERANK_ENABLED` / `DOCUCHAT_RERANK_CANDIDATES` | `true` / `10` | Reranker and how many RRF candidates it reorders |
| `DOCUCHAT_CONTEXTUAL_META_ENABLED` | `true` | Metadata context (document name and first sentence), no LLM |
| `DOCUCHAT_CONTEXTUAL_ENABLED` | `false` | Context written by the LLM for each chunk; replaces the metadata context and makes ingestion about 40 times slower |

If you change the embedding model, rebuild the index with `docuchat ingest --reset`: the app refuses to mix vectors from different models. Do the same if you change the context options or come from v1.0: unchanged documents are not reindexed.

## Design decisions

- **No RAG frameworks.** Every piece (loaders, chunker, fusion, prompts, citations) is a small module you can read and test on its own.
- **800-character chunks with 120 overlap.** In the evaluation they tie with 1200 and beat 500 with hybrid search, while giving the LLM shorter passages.
- **Instruction on queries only.** Qwen3-Embedding recommends prefixing the query with an instruction; documents are indexed without it.
- **RRF with k=60 and no repeated neighbours.** Of two adjacent chunks from the same page only the best one is kept, so context isn't wasted on overlapping text.
- **Reranker over 10 candidates.** With 20, Hit@1 goes a bit higher on eval v2 (0.814 vs 0.771), but each search takes twice as long: 0.48 s extra instead of 0.23 s.
- **Metadata context instead of LLM context.** Both were measured (see the results table): the metadata one is free and scores higher.
- **Validated `[n]` citations.** Citations that don't match any retrieved chunk are dropped, with a warning.
- **Temperature 0 and a rule for ambiguous questions.** Answers are reproducible and, when a question doesn't say what it refers to, the model answers for the case it finds instead of saying "I don't know".
- **Reasoning off** for latency; turn it on with `DOCUCHAT_LLM_THINKING=true`.
- **Self-healing index.** If the SQLite registry and Chroma get out of sync, the next indexing run reprocesses what's missing.

## How it was built

The project was developed by two AI agents, with a human reviewing:

- A **brain** (Claude) writes one spec per task in [`tasks/`](tasks): goal, files, exact signatures and tests with expected values that can't be changed.
- An **executor** (Qwen 3.6 running locally, through opencode) implements each spec and writes a report in [`reports/`](reports). Its rules are in [`AGENTS.md`](AGENTS.md).
- The brain checks every report by running the suite and testing against the real models. When something is off, it writes a correction spec (the `NNN-b` ones).

Specs, reports and the project state ([`docs/STATE.md`](docs/STATE.md)) are written in Spanish.

## Development

```bash
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
uv run mypy src
```

Tests never call oMLX: they use fake embedding and chat models. CI runs the same checks and also builds the Docker image.

```
src/docuchat/
  config.py      settings (pydantic-settings, DOCUCHAT_ prefix)
  ingest/        per-format loaders, cleaning and folder scanner
  index/         chunker, embeddings, Chroma, FTS5, context, registry and indexer
  retrieval/     RRF fusion, reranker and hybrid searcher
  generation/    LLM client, prompts, citations and Answerer
  evaluation/    dataset, metrics, runner and report
  api/           FastAPI, templates and static files
  cli.py         ingest, search, ask and serve commands
```

## Limitations

- The models need a Mac with Apple Silicon. The app talks to any OpenAI-compatible server (`DOCUCHAT_LLM_BASE_URL`), but it has only been tested with oMLX.
- No OCR: scanned PDFs without a text layer aren't indexed.
- LLM context takes about 1.3 s per chunk the first time (there is a cache). That is why it is off by default.
- The evaluation uses two small, generated corpora (`samples/` and `samples_v2/`); the numbers don't generalise to every collection.

## License

[MIT](LICENSE)
