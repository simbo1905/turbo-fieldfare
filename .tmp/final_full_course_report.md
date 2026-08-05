# Full-course comparison final report

## Code and publication

- Experimental branch final commit before this report: `8e24c53`.
- Clean upstream CLI commit: `93b944d`.
- Upstream issue: https://github.com/drumih/turbo-fieldfare/issues/92
- Upstream PR: https://github.com/drumih/turbo-fieldfare/pull/93
- PR 93 is ready for review.
- Experimental high-water tag before the rebase:
  `summarisation-cli-high-water-2026-08-05`.
- Published measurement Gist:
  https://gist.github.com/simbo1905/6ec2912e544cf7a7f361ba0b5de90935

## Environment

- Hardware: Mac17,2, arm64, 32 GiB RAM.
- macOS: 26.5.2.
- Swift: 6.2.1.
- Model: completed local `scratch/gemma4.gturbo` installation.
- Corpus: 111 Markdown files, 617,063 bytes.
- Chunking: 11,000-character windows, 10,000-character step.
- Generated chunks: 61.

## Protocol

- Ollama used native local defaults with no warmup and no generation/context
  options. All 61 chunks completed.
- Before TF measurement, `ollama ps` confirmed no loaded Ollama model. The idle
  service daemon remained running, as allowed by the corrected repository rule.
- TF used the submitted CLI with stock 4K context, shipped generation defaults,
  and shipped runtime-control defaults. No new runtime option was supplied.
- Exact token preflight used the CLI tokenizer with `--max-context 1`, which
  fails before model loading and exposes the true prompt-token count.
- The preflight blacklisted chunks 48, 49, 50, 51, and 54 from both sides.
- An attempted 16K retry at chunk48 was aborted after one output and is excluded
  from all comparison and panel calculations.

## Comparable 4K results

| Backend | Eligible runs | Successful | Total wall time | Median wall time | Output bytes | Sampled peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TurboFieldfare | 56 | 56 | 4,144.53 s | 72.16 s | 141,540 B | 1,500.5-1,834.2 MiB |
| Ollama | 56 | 56 | 2,774.15 s | 50.32 s | 149,813 B | Not sampled in this series |

TF took 49.4% longer than Ollama over the 56 comparable chunks. The earlier
twelve-chunk baseline measured Ollama sampled peak RSS at 18,480.08-18,569.41
MiB; that baseline is the available like-machine memory reference, not a
full-course Ollama RSS measurement.

## Quality panel

- Eligible inputs: 56.
- Deterministic panel indices: 00, 05, 10, 15, 20, 25, 30, 35, 40, 45, 55, 60.
- Presentation orders: AB and BA.
- Judges: 3 per order.
- Calls: 72; all returned valid verdicts.
- Normalized results: 64 ties, 7 Ollama preferences, 1 TF preference.

There is no panel-wide evidence of systematic catastrophic TF degradation.
One selected chunk received all six normalized preferences for Ollama; this is
a localized material concern and prevents a blanket equivalence claim.

## Privacy

Private source text, source filenames, raw summaries, exact private paths, raw
judge requests/responses, and logs remain beneath `.tmp`. Public reports include
only aggregate counts, timings, sampled RSS, and the sanitized conclusion.
