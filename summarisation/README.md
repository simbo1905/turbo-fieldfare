# Reproducible TurboFieldfare vs Ollama summarisation benchmark

This directory is an exact local import of the benchmark toolkit published in
the companion Gist. It prepares a fixed, twelve-chunk corpus outside the
course tree, measures a caller-supplied backend serially, and optionally
records blind pairwise votes. It does not claim sampler-normalized performance
or quality: the comparison is a real-user-path comparison.

## Safety and prerequisites

Do not run this workflow while another TurboFieldfare, Ollama, or model-owning
process is active. Before a model pass, follow this repository's `AGENTS.md`:
macOS 26+, Swift 6.2+, sufficient disk, acceptable `memory_pressure -Q`, a
completed `scratch/gemma4.gturbo`, and no matching model owner. The course is
external and read-only. Select output roots outside both the course and this
repository. Do not stop or replace an existing owner, and run one model-owning
workload at a time.

The scripts are intentionally opt-in. Unit tests use local fixtures and a fake
HTTP server; they do not access a course, start a model, request Ollama
inference, or submit a paid judge request.

## Workflow

Set paths to your own external course and output location, then create the
immutable manifest. Only sorted `*_video_*.md` sources participate.

```sh
COURSE_ROOT=/absolute/path/to/read-only-course
BENCH_ROOT=/absolute/path/outside/course-and-repository/tf-ollama-benchmark
uv run --script summarisation/prepare_benchmark_corpus.py "$COURSE_ROOT" "$BENCH_ROOT/corpus"
```

Use the same `manifest.json` and the same summary instruction for both passes.
The one-shot `process_chunks_turbofieldfare.py` adapter reads a chunk, adds the
fixed instruction in a chat message, and writes the CLI response to the
requested output. It relies on the one-shot CLI's production defaults: 4K
context, temperature 0.2, top-p 0.95, top-k 64, repetition penalty 1.0, and
remaining-context output limit.

```sh
MODEL_DIR=/absolute/path/to/scratch/gemma4.gturbo
TF_CLI=/absolute/path/to/.build/release/TurboFieldfareCLI
SUMMARY_PROMPT='Summarise the following course transcript faithfully and concisely:'
uv run --script summarisation/process_chunks_turbofieldfare.py \
  --input "$BENCH_ROOT/corpus/benchmark00.md" \
  --output "$BENCH_ROOT/turbofieldfare/summary.md" \
  --cli "$TF_CLI" --model "$MODEL_DIR" --prompt "$SUMMARY_PROMPT"
```

Before this pass, retain `TurboFieldfareCLI --help` and the runtime
context-memory estimate beside the run manifest. The adapter sends the source
through a temporary messages file, not shell interpolation.

For Ollama, use the one-chunk adapter with native defaults:

```sh
uv run --script summarisation/process_chunks_ollama.py --input "$BENCH_ROOT/corpus/benchmark00.md" --output "$BENCH_ROOT/ollama/summary.md"
```

`process_chunks_ollama.py` accepts both a chunk directory and the one-input,
one-output-file form used by this runner. Do not add generation options. Its
pass is not sampler-matched to TurboFieldfare.

Finally, voting is optional and never automatic. It reads `.env` or the
environment without saving a key, sends two blind label orders per chunk to
each listed judge, and records failures without counting them as votes.

```sh
uv run --script summarisation/pairwise_grade.py \
  --manifest "$BENCH_ROOT/corpus/manifest.json" \
  --candidate-a "$BENCH_ROOT/turbofieldfare/outputs" \
  --candidate-b "$BENCH_ROOT/ollama/outputs" \
  --output "$BENCH_ROOT/votes" \
  --endpoint "$OPENCODE_COMPATIBLE_GATEWAY/v1/chat/completions" \
  --judge-model gpt-5.6-terra \
  --judge-model claude-sonnet-5 \
  --judge-model kimi-k3
```

`--endpoint` is mandatory and must name an OpenAI-compatible gateway capable
of serving all three requested model identifiers; there is deliberately no
OpenAI API default because that endpoint cannot serve the Claude and Kimi
identifiers. This plans 72 requests (12 chunks × 2 orders × 3 judges); it must
be run only with deliberate authority for those requests. No verdict has been
produced by this repository.

## Files

- `prepare_benchmark_corpus.py` — deterministic transcript selection, chunking,
  manifest, and output-root protection.
- `benchmark_run.py` — (removed; replaced by direct adapter invocation)
- `process_chunks_turbofieldfare.py` — one-chunk TurboFieldfare CLI adapter
  with configurable runtime options.
- `process_chunks_ollama.py` — native-default Ollama NDJSON chunk client.
- `pairwise_compare.py` — spot-check pairwise judge; two input summaries, one output score.
- `pairwise_grade.py` — two-candidate, reversed-order blind voting recorder.

See `GIST_PROVENANCE.md` for the exact imported revision and raw-file hashes.
