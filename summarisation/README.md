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
For TurboFieldfare, `benchmark_run.py` supplies each chunk path to a serial
backend command. `process_chunks_turbofieldfare.py` reads that chunk, adds the
fixed instruction in a chat message, and writes the CLI response to the
requested output. It relies on the one-shot CLI's Gemma profile defaults: 4K
context, temperature 1.0, top-p 0.95, top-k 64, repetition penalty 1.1, and
remaining-context output limit.

```sh
MODEL_DIR=/absolute/path/to/scratch/gemma4.gturbo
TF_CLI=/absolute/path/to/.build/release/TurboFieldfareCLI
SUMMARY_PROMPT='Summarise the following course transcript faithfully and concisely:'
uv run --script summarisation/benchmark_run.py \
  --manifest "$BENCH_ROOT/corpus/manifest.json" \
  --results "$BENCH_ROOT/turbofieldfare" \
  --backend TurboFieldfare-Gemma4-26B-A4B \
  --config-json '{"model_dir":"'"$MODEL_DIR"'","commit":"'"$(git rev-parse HEAD)"'","max_context":4096,"temperature":1.0,"top_p":0.95,"top_k":64,"repetition_penalty":1.1,"max_new":"remaining-context"}' \
  --backend-command "uv run --script summarisation/process_chunks_turbofieldfare.py --input {input} --output {output} --cli $TF_CLI --model $MODEL_DIR --prompt '$SUMMARY_PROMPT'"
```

Before this pass, retain `TurboFieldfareCLI --help` and the runtime
context-memory estimate beside the run manifest. The adapter sends the source
through a temporary messages file, not shell interpolation.

For Ollama, do not supply sampling or context options: retain native local
defaults. Capture its version, modelfile, loaded-model state, and digest before
and after by passing the metadata flags to the runner.

```sh
uv run --script summarisation/benchmark_run.py \
  --manifest "$BENCH_ROOT/corpus/manifest.json" \
  --results "$BENCH_ROOT/ollama" \
  --backend ollama-native-default \
  --config-json '{"model":"gemma4:26b","sampling":"native-default"}' \
  --ollama-bin ollama --ollama-model gemma4:26b \
  --backend-command "uv run --script summarisation/process_chunks_ollama.py --input {input} --output {output}"
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
  --judge-model gpt-5.6-terra \
  --judge-model claude-sonnet-5 \
  --judge-model kimi-k3
```

That plans 72 requests (12 chunks × 2 orders × 3 judges); it must be run only
with deliberate authority for those requests. No verdict has been produced by
this repository.

## Files

- `prepare_benchmark_corpus.py` — deterministic transcript selection, chunking,
  manifest, and output-root protection.
- `benchmark_run.py` — serial backend measurement, logs, output hashes, host
  metadata, and optional before/after Ollama metadata snapshots.
- `process_chunks_turbofieldfare.py` — one-chunk TurboFieldfare CLI adapter
  using the public CLI profile defaults.
- `process_chunks_ollama.py` — native-default Ollama NDJSON chunk client.
- `pairwise_grade.py` — two-candidate, reversed-order blind voting recorder.

See `GIST_PROVENANCE.md` for the exact imported revision and raw-file hashes.
