# Summarisation CLI TDD handoff

## Boundary

This work creates a reproducible, real-user-path comparison toolkit for TurboFieldfare and native-default Ollama. It does not run a course corpus, start a model, perform Ollama inference, request a paid judge, or make a quality or performance claim while implementing or testing the tools.

The LSE course root is read-only, external input. Chunks, prompts, manifests, summaries, logs, metadata, and votes are written only to caller-selected output directories outside that course tree. Never copy, rename, alter, or delete a course file. Do not download a checkpoint, duplicate the installed model, or terminate another model owner.

Before either later model pass, apply `AGENTS.md` model-run checks: macOS 26+, Swift 6.2+, adequate disk, acceptable `memory_pressure -Q`, completed `scratch/gemma4.gturbo`, and no matching TurboFieldfare/Ollama model owner. The benchmark must wait for an existing Mac/decode-service owner to close; it must not stop or replace it. Execute only one model-owning workload at a time.

## Deliverables and provenance

Create branch `simbo1905/summarisation-cli` while preserving concurrent `.gitignore` changes, then add only the `.tmp/` ignore entry. The imported toolkit lives in `summarisation/`; all generated artifacts remain outside the course and repository unless a caller deliberately chooses another safe output directory. Record the exact imported Gist URL and revision in the local import provenance file.

Repair Gist `053b48269b1e95800500b85190adf427` only after tool tests pass:

- `prepare_benchmark_corpus.py`
- `benchmark_run.py`
- source-faithful `pairwise_grade.py`
- Apache-2.0 `LICENSE`
- README inventory and exact prepare -> TurboFieldfare -> Ollama -> vote flow

Use `gh api` to verify the published revision and each raw file before import. Do not call a judge, run a benchmark, or access the course as part of that publication verification.

## Corpus contract

`prepare_benchmark_corpus.py COURSE_ROOT OUTPUT_ROOT` accepts separate roots and rejects an output root equal to or beneath the resolved course root. It:

1. selects only lexicographically sorted `*_video_*.md` files;
2. concatenates their contents with exactly `\n\n` between files;
3. creates 11,000-character chunks at a 10,000-character step;
4. requires at least 12 chunks and chooses 12 evenly distributed chunk indices; and
5. writes `benchmark00.md` through `benchmark11.md` and a reproducible manifest.

The manifest records format/tool version, chunk size and step, selected source indices, relative source paths, offsets, source and chunk SHA-256 values, and the selected benchmark order. Repeating preparation on unchanged input must produce byte-identical chunks and manifest. Fixtures, not the course, prove this behavior.

## Measurement contract

`benchmark_run.py` takes a manifest, result directory, backend identity and a caller-supplied backend command template. It invokes one chunk at a time and records, per chunk: argv, wall time, exit status, output byte count and hash, and stdout/stderr paths. It also captures host/OS/tool versions and backend configuration. It measures output only and never grades it.

The shared summary prompt and immutable twelve-chunk manifest are inputs to both passes. A failed chunk stays recorded as failed; it is not silently retried, replaced, or counted as output.

### TurboFieldfare pass

Use the one-shot CLI with the Gemma summary profile: 4,096-token context, temperature 1.0, top-p 0.95, top-k 64, repetition penalty 1.1, and a response limit clamped to context remaining after prompt formatting. Record the model directory, TurboFieldfare commit, CLI help/configuration, and context-memory estimate.

CLI red tests specify these public behaviors:

- defaults are the Gemma summary profile;
- accepted context lengths are exactly 4,096, 8,192, 16,384, 32,768, and 65,536;
- `--prompt` and `--messages-file` conflict, while each works alone;
- `--max-new` accepts a positive requested token limit and runtime clamps it to remaining context; no parser-level context-length restriction belongs on `--max-new`.

No undocumented Ollama option or alias belongs in the TurboFieldfare CLI. Ollama identifiers/aliases are an external backend configuration concern and must be recorded verbatim by the comparison toolkit.

### Ollama pass

Use imported processor support for `gemma4:26b` with no sampling or context flags, retaining the user's native Ollama behavior. Capture before and after: `ollama --version`, `ollama show gemma4:26b --modelfile`, `ollama ps`, model identifier, and digest. This documents version/hardware-dependent effective defaults; it does not claim sampler normalization.

The final report calls this a real-user-path comparison, not a normalized performance or quality comparison.

## Blind voting contract

`pairwise_grade.py` reads every original chunk and exactly two candidate summaries from result directories named by the manifest. It assigns blind A/B labels and submits both candidate orders for every chunk: 24 planned comparisons per judge. Planned judge models are `gpt-5.6-terra`, `claude-sonnet-5`, and `kimi-k3`, for 72 planned requests.

Load the credential from ignored `.env` or the current environment. Never print, persist, or add it to a manifest. For every attempt save raw response, parsed verdict, A/B order, judge model, request timestamp, and error state. Aggregate candidate and per-judge wins/losses/ties; invalid/failed responses remain auditable but count as no vote. The command is opt-in and test coverage uses a fake HTTP endpoint only.

## Red/green sequence

1. Add failing, isolated Swift parser/configuration tests for the CLI contract above. Do not invoke `run(args:)`, load a tokenizer, or allocate Metal.
2. Add fixture tests for transcript selection, deterministic chunking and selection, manifest reproducibility, output-root rejection, backend measurement, native-Ollama metadata capture, and A/B order reversal.
3. Add fake-HTTP tests for streaming summaries and all three judge request records.
4. Implement the minimum behavior to make each preceding red test green, staging the intended files after each approved stage.
5. Run `Scripts/test.sh` serially. A green test suite is tool behavior proof, not corpus/model/judge/deployment evidence.

Report every command, exit status, timing footer or error, commit, hardware and RAM, macOS, Swift version, and any protocol deviation when later model work is explicitly authorized.
