# Gemma 4 26B-A4B local summarisation measurement

## Headline

The completed twelve-chunk baseline shows a clear space-for-speed tradeoff on
this machine. TurboFieldfare averaged **74.36 s** per chunk with **1,538.72 to
1,587.53 MiB** sampled peak RSS. Ollama averaged **60.59 s** with **18,480.08
to 18,569.41 MiB** sampled peak RSS. In that series, TurboFieldfare was **22.7%
slower** while using about **17 GiB less** sampled process RSS.

RSS is sampled process footprint, not complete unified-memory accounting or a
device-memory profiler. These figures are measurements from one Mac, not
performance ceilings.

## Scope

This is a one-time, local, real-user-path measurement on twelve fixed confidential transcript chunks.  The inputs, prompts, summaries, source names, paths, raw logs, keys, and output hashes are intentionally excluded.  `Chunk 00` through `Chunk 11` are stable anonymous identifiers only.

Both backends received the same summary instruction and the same immutable chunk set.  Each measured run was serial, after a full preflight, with a finite timeout and process-tree cleanup.  A discarded warmup preceded each backend series.  The baseline figures are wall-clock measurements, not performance ceilings or a sampler-normalised comparison.

## Twelve-chunk baseline

| Backend | Runs | Successful | Mean wall time | Range | Total output | Peak sampled RSS range |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TurboFieldfare, 4K context | 12 | 12 | 74.36 s | 66.12–80.64 s | 36,565 B | 1,538.72–1,587.53 MiB |
| Ollama `gemma4:26b`, native defaults | 12 | 12 | 60.59 s | 48.35–73.08 s | 36,109 B | 18,480.08–18,569.41 MiB |

Ollama used its ordinary local defaults: no sampling or context options were supplied. TurboFieldfare used context 4096, temperature 1.0, top-p 0.95, top-k 64, repetition penalty 1.0, and a response limit equal to remaining context.  The different runtime paths and native defaults are material; this report makes no quality or sampler-normalised performance claim.

## TurboFieldfare context sweep

The largest anonymous selected chunk was measured once per listed context, with the TurboFieldfare sampling settings held unchanged.  Wall time and sampled RSS varied modestly across this sample; no quality result is claimed from the sweep.

| Context | Wall time | Output | Peak sampled RSS |
| ---: | ---: | ---: | ---: |
| 4,096 | 58.18 s | 3,357 B | 1,660.09 MiB |
| 8,192 | 58.03 s | 3,225 B | 1,666.98 MiB |
| 16,384 | 59.48 s | 3,243 B | 1,648.36 MiB |
| 32,768 | 53.81 s | 2,632 B | 1,710.05 MiB |
| 65,536 | 59.23 s | 3,179 B | 1,632.64 MiB |

## Current full-course run

A stock Ollama pass over all 61 deterministic 11K/10K chunks completed with no
warmup and no option overrides: **61/61 successful**, **3,034.54 s total**
(50m 34.54s), **50.32 s median** per chunk, and **161,682 B** visible output.
The matching stock TurboFieldfare pass is still in progress and will be added
as a separate measured series.

## Provenance and limitations

All measurements ran on `Mac17,2`, arm64, 32 GiB RAM, macOS 26.5.2, Swift 6.2.1. The per-run repository commits, exact sanitized measurement values, and exit status are in `metrics.csv` and `metrics.json`.

This report intentionally omits confidential material and raw evidence. Its scope is one repeatable local procedure, not a general model benchmark. Output byte size is only an observable size. RSS is a sampled process footprint, not a complete memory-accounting claim.
