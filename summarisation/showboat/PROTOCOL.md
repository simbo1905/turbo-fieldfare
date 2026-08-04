# Privacy-preserving, Showboat-recorded Gemma 4 comparison

This protocol compares stock local `gemma4:26b` in Ollama with local
TurboFieldfare. It is designed for confidential instructional transcripts.
Nothing copied to the public Gist may contain a source path, filename, title,
topic, transcript, summary, raw backend log, model directory, or private
configuration.

The private configuration lives only at `.tmp/showboat-private-config.json`.
Create it from `private-config.template.json`, set the confidential course root
and local model directory, and keep `results_root` under `.tmp/`. The wrapper
will reject every other result location.

## Method

- The corpus contains sorted `*_video_*.md` files, concatenated with `\n\n`,
  chunked to 11,000 characters at 10,000-character starts, then reduced to 12
  evenly-spaced chunks. All chunks and summaries remain private under `.tmp/`.
- The public table labels sources `Video A`, `Video B`, and so on. It reports
  the largest timestamp rounded to the nearest minute. Each reported KiB size
  is independently jittered once by a uniform random factor between -3% and
  +3%; this is a privacy redaction, not an analytic value.
- TurboFieldfare uses the official Gemma generation configuration: temperature
  1.0, Top-K 64, Top-P 0.95, and repetition penalty 1.0. Context is 4K for
  the primary comparison. Ollama receives no sampling/context options, so the
  report calls it a native-default real-user-path comparison, not a
  sampler-normalized benchmark.
- A one-chunk discarded warmup is performed for each backend. Each subsequent
  measurement is one manual command with a timeout, not a loop.
- Peak apparent RSS is sampled every 250 ms from the launched backend and its
  descendants; the Ollama measurement also samples its local server. This is
  not a device-memory profiler. Memory free percentage is captured before and
  after every command.
- The context sweep uses only the largest selected chunk and only changes
  context (4K, 8K, 16K, 32K, 64K). It does not tune temperature or sampling.

## Showboat notebook commands

Run these exactly from the repository root after `bash
summarisation/showboat/install_showboat.sh`. Each command is intentionally
path-safe: it never contains a confidential value. If any `showboat exec`
entry fails, inspect only its private artifact, run `showboat pop` to remove
the failed entry, correct the local condition, and repeat that one command.

```bash
export PATH="$PWD/.bin:$PATH"
showboat init .tmp/gemma4-comparison.showboat.md "Confidential-material Gemma 4 comparison"
showboat note .tmp/gemma4-comparison.showboat.md "This executable notebook records a local-only comparison. Source text, source paths, topics, summaries, and raw logs remain in ignored private storage."
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py preflight"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py prepare"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py warmup turbofieldfare 0"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py warmup ollama 0"
```

Measure TurboFieldfare one chunk at a time:

```bash
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 0"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 1"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 2"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 3"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 4"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 5"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 6"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 7"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 8"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 9"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 10"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 11"
```

Measure Ollama one chunk at a time:

```bash
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure ollama 0"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure ollama 1"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure ollama 2"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure ollama 3"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure ollama 4"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure ollama 5"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure ollama 6"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure ollama 7"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure ollama 8"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure ollama 9"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure ollama 10"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure ollama 11"
```

Run the compactness sweep on the largest chunk, identified only after private
preparation. Add the five commands one at a time, replacing `N` with that
private chunk number:

```bash
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare N --context 4096"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare N --context 8192"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare N --context 16384"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare N --context 32768"
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare N --context 65536"
```

Finally generate and append the public-safe table:

```bash
showboat exec .tmp/gemma4-comparison.showboat.md bash "uv run --script summarisation/showboat/private_benchmark.py public-report --output .tmp/gemma4-public-report.md"
showboat exec .tmp/gemma4-comparison.showboat.md bash "cat .tmp/gemma4-public-report.md"
```

## Quality scoring boundary

Do not use `pairwise_grade.py` with a remote endpoint for confidential material:
that would transmit the source and summaries. Generate blinded pairs locally
and have an authorized human assess them locally, or use a separately approved
local-only judge. Score paired comparisons without revealing backend labels,
record ties, and report that this is a small local quality signal rather than a
general quality claim.
