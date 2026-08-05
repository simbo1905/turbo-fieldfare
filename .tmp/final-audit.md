# Final evidence audit — 2026-08-05

## Scope and safety

This is a read-only audit of the committed execution ledger, local private
measurement metadata, committed Showboat notebooks, test results, and the
published sanitized secret Gist. It contains no source material, prompts,
summaries, local filesystem locations, raw logs, output hashes, or credentials.
No model invocation or Gist write was made for this audit.

## Requirement audit

| Requirement | Status | Evidence |
| --- | --- | --- |
| Numbered review gates 00–08 | Partially verified | The ledger records all nine as done. The dedicated Showboat/tooling tests pass (24 tests), including identical Ollama task, per-invocation preflight, owned process-group timeout cleanup, redacted filesystem errors, explicit judge gateway, flat-Gist resolution, and private provenance. The generic benchmark-runner regression tests do not pass; see failed gate below. |
| Fixed corpus and serial baseline | Verified | The private manifest exists; measurement metadata contains 12 TurboFieldfare and 12 Ollama records, all exit code 0, positive wall time and output size, and present output hashes. |
| Same task for both backends | Verified by adapter tests | The Ollama adapter test passes and the review-gate test covers the shared instruction. |
| Discarded warmup before each baseline | Verified | The ledger and the two baseline notebooks record one warmup per backend. |
| Single-owner/preflight/timeout discipline | Verified by tests and artifacts | The per-invocation, timeout process-group, and privacy-boundary test set passes. Each private measurement has before/after memory fields and a timing/error field. |
| Provenance per measurement | Verified | Every baseline and sweep measurement has a non-empty repository commit plus hardware, architecture, RAM, macOS, Swift, and capture-time fields. |
| TurboFieldfare context sweep | Verified | Five successful private measurements exist at 4K, 8K, 16K, 32K, and 64K; each has exit code 0 and positive wall time, output size, and sampled RSS. Sampling settings were held fixed according to the sanitized report. |
| Showboat records | Verified | Three committed notebooks exist: TurboFieldfare baseline (16 command blocks), Ollama baseline (15), and context sweep (7). The Ollama notebook records a pop/retry marker. |
| Public-safe report and private Gist | Verified | Secret Gist `6ec2912e544cf7a7f361ba0b5de90935`, revision `ad29164514073f30aaba93c740cffcd30d144d2f`, is live with only `README.md`, `metrics.csv`, and `metrics.json`. Each remote raw file SHA-256 matches its local sanitized source. A targeted scan found no path, credential, model-token, or source-root markers in the published files. |
| Three-judge qualitative spot check | Not achieved | All three judge models returned HTTP 403 on the authorized 4K-vs-64K spot check. There are zero valid verdicts and no quality score may be inferred. The aggregate artifact's zero-point placeholder must not be interpreted as a tie; the published report correctly makes no score claim. |
| Complete generic toolkit regression suite | Failed gate | Six tests fail because committed tests invoke `summarisation/benchmark_run.py`, but that executable was deleted in commit `412e181`. This does not alter the already recorded private measurements, which used the private one-action runner, but it means the review04/05 generic-tool claims are not currently reproducible. |

## Current test evidence

- `uv run --no-project python -m unittest discover -s summarisation/showboat/tests -v`: pass, 24 tests.
- `Scripts/test.sh`: pass.
- `uv run --no-project python -m unittest discover -s summarisation/tests -v`: fail, 6 of 14 tests (all failures are attributable to the missing generic benchmark runner; the remaining 8 pass).

## Definitive conclusion

The local measurement portion is complete and the published aggregate is
privacy-safe and provenance-backed. It supports a real-user-path timing and
sampled-RSS comparison only; it does **not** support a quality conclusion.

Completion remains blocked by two concrete items: restore or deliberately
retire the obsolete generic benchmark-runner tests/tool coherently, and obtain
an authorized multi-provider judge gateway capable of returning verdicts for
the three named judge models. The latter requires an external authorization
change; no source or summary should be sent until that boundary succeeds.
