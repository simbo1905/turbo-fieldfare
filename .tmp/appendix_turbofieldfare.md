# Appendix: Gemma 4 via Ollama and TurboFieldfare

This follow-up compares the same Gemma 4 26B-A4B instruction model through
local Ollama and [TurboFieldfare](https://github.com/drumih/turbo-fieldfare), a
custom Swift and Metal runtime for Apple Silicon that keeps a small resident
core and streams routed experts through a bounded cache. It is an interesting
project for local-first users who value memory headroom and on-device data
handling, not just maximum tokens per second.

The CLI controls used in this follow-up are proposed upstream in
[TurboFieldfare PR #93](https://github.com/drumih/turbo-fieldfare/pull/93),
from clean commit
[`93b944d`](https://github.com/simbo1905/turbo-fieldfare/commit/93b944d9e1afec919060dd5dca35810fad12c8de).
The feature exposes the existing expert-cache, prefill, and RDADVISE controls
for reproducible CLI batch work while preserving shipped defaults.

## Workload and limits

The course workload contained 617,063 bytes across 111 Markdown files. It was
split into 61 overlapping 11,000-character windows with a 10,000-character
step. Exact token preflight found that five windows did not fit the shipped 4K
TurboFieldfare context, so they were excluded from both backends before the
comparison. The resulting like-for-like set contains 56 chunks. This matters:
character count is not a reliable context-budget proxy for token-dense source
material.

## Speed and sampled memory

| Runtime | Comparable chunks | Total wall time | Median per chunk | Sampled peak RSS |
| --- | ---: | ---: | ---: | ---: |
| Ollama `gemma4:26b`, native defaults | 56 | 2,774.15 s | 50.32 s | Not sampled in this full-course series |
| TurboFieldfare, shipped 4K defaults | 56 | 4,144.53 s | 72.16 s | 1,500.5-1,834.2 MiB |

Ollama was **49.4% faster** on the 56 comparable chunks. The full-course
Ollama run did not collect process RSS, so it should not be presented as a
direct memory measurement. The earlier twelve-chunk same-machine baseline used
the same process-RSS sampling method and measured Ollama at
18,480.08-18,569.41 MiB, versus 1,538.72-1,587.53 MiB for TurboFieldfare.
That is roughly 17 GiB less sampled process footprint for TurboFieldfare in the
baseline, with the usual caveat that RSS is not complete Apple unified-memory or
GPU-memory accounting.

TurboFieldfare therefore does not win this batch-speed comparison, but it has a
material memory-headroom advantage on this Mac. That makes it worth watching
for constrained Apple Silicon systems and for workflows where keeping the
local-model footprint modest matters more than minimizing elapsed time.

## Why this transcript workload is hard

Each independent 11K-character summary window needs a substantial prompt
prefill before generation. That prefill-heavy pattern is a disadvantage for
TurboFieldfare here: it pays the prompt/KV setup cost on every overlapping
window, then generates a relatively short summary. It is not a representative
single long interactive session with prompt reuse, and it should not be read as
a general inference-speed ranking.

It does preserve the principal local benefit from the earlier benchmark: no
source material leaves the machine and there is no per-request inference bill.
For scale, Ollama reported 169,678 prompt tokens and 87,650 generated tokens
over all 61 windows. At the earlier benchmark's OpenRouter Gemma 4 rates of
$0.06/M input and $0.33/M output tokens, the rough cloud-equivalent estimate is
about **$0.039** for this larger course run. This is an estimate from local
response metadata, not a cloud invoice; generated-token accounting may include
provider-specific reasoning behavior.

## Quality check

Twelve evenly spaced eligible chunks were judged in both A/B orders by three
independent large models under a conservative, source-grounded non-inferiority
rubric. All 72 calls were valid: 64 ties, 7 Ollama preferences, and 1
TurboFieldfare preference after normalizing presentation order. There was no
panel-wide evidence of systematic catastrophic degradation, but one selected
chunk received all six normalized preferences for Ollama. The result is not a
blanket equivalence claim.

## Reproducibility

The complete sanitized measurement summary is published at
https://gist.github.com/simbo1905/6ec2912e544cf7a7f361ba0b5de90935. Private
source material, paths, raw summaries, and judge responses are excluded.
