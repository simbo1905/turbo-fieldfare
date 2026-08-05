# item18 - Complete 61-chunk stock comparison

## Status

In progress. The user resumed execution after the rebased branch was pushed to
the fork at `b4d86d6`; comparison uses the original stock 4K context.

## Objective

Run all Course 2 Markdown material through stock Ollama first and then through
the exact stock TurboFieldfare CLI submitted in PR 93. This is a quality and
catastrophic-regression check, not another tuning exercise or speed gate.

Do not tune resource controls to chase speed. The observed space-for-speed
tradeoff is too large for small knob changes to make TurboFieldfare
competitively fast, and aggressive tuning could damage large-prompt output.

## Corpus

- Include every `.md` source file in Course 2, not only `*_video_*.md` files.
- Previously measured combined size: 617,063 bytes.
- Build deterministic chunks with an 11,000-character window and a
  10,000-character step.
- Expected count: 61 chunks.
- Write the chunker and generated corpus only under `.tmp`.
- Record ordered source filenames and byte ranges privately for reproducibility.
- Do not publish source text, source filenames, or private paths.

Before the full run, verify that the largest generated chunk fits the stock
TurboFieldfare context budget. Stop and report if it does not fit; do not alter
the submitted defaults silently.

## Recorded blocker

- Corpus preparation completed: 111 Markdown files, 617,063 source bytes, and
  61 deterministic 11K/10K chunks.
- Stock Ollama completed 61/61 chunks without errors.
- Stock TurboFieldfare completed chunks 00 through 47, then rejected chunk48
  before generation with exit code 2: prompt 4,673 tokens reaches stock
  `maxContext` 4,096.
- Chunk48 is 11,020 bytes, so byte-window size is not a reliable proxy for its
  tokenizer length.
- Ollama was unloaded before the TF pass; `ollama ps` was empty.

Exact no-model token preflight used the CLI's tokenizer with a one-token context
probe. It blacklisted chunks 48, 49, 50, 51, and 54 from both output sets
because their prompts are at least 4,096 tokens. A 16K retry was started only
to confirm the setting works, then aborted after its first output; it is not
part of the comparison. Resume only eligible chunks at the original 4K setting.
Keep temperature, Top-K, Top-P, repetition penalty, max-new, and all five
runtime controls at shipped defaults.

## Required machine preflight

Record all results before starting either backend:

1. Git commit and branch.
2. Mac hardware model and RAM.
3. macOS version; require macOS 26 or later.
4. Swift version; require Swift 6.2 or later.
5. Available disk space.
6. `memory_pressure -Q`; stop if pressure is unacceptable.
7. Confirm `scratch/gemma4.gturbo` is complete.
8. Confirm no process matches `TurboFieldfareServer`, `TurboFieldfareMac`,
   `TurboFieldfareDecodeService`, `TurboFieldfareCLI`, package-test helpers,
   `mlx_lm`, or `mlx-lm`.
9. Run `swift build -c release` once and record its exit code.

Do not terminate an existing TurboFieldfare/model process. If one exists, stop
and inform the user.

## Ollama pass

1. Do not run a discarded warmup; this is a workload-quality pass.
2. Use the installed stock `gemma4:26b` configuration without sampling or
   context overrides.
3. Process chunks 00 through 60 once, in order.
4. Capture the visible response and any separate Ollama `thinking` field rather
   than silently discarding either.
5. Record per chunk: start/end time, wall time, input bytes, response bytes,
   thinking bytes, token counts returned by Ollama, stop reason, and errors.
6. Preserve each chunk's output and one machine-readable manifest under a new
   confidential `.tmp` result directory.
7. After chunk 60, unload `gemma4:26b` and verify `ollama ps` lists no loaded
   model before measuring TurboFieldfare. An idle `ollama serve` daemon is
   acceptable.

## TurboFieldfare pass

1. Use `.build/release/TurboFieldfareCLI` built from the rebased branch.
2. Retain the stock 4K context. Blacklist chunks that do not fit rather than
   changing the comparison settings. Do not pass any of the five new runtime
   options or override generation settings.
3. Process the same chunks 00 through 60 once, in the same order.
4. Run one CLI process at a time and never overlap model processes.
5. Record per chunk: exact command shape with private paths redacted, exit code,
   start/end time, wall time, output bytes, and complete timing footer.
6. Preserve each output and one machine-readable manifest under `.tmp`.

## Sanity checks

After both passes, generate a private comparison table containing:

- Missing or failed outputs.
- Empty outputs.
- Stop reason and truncation indicators.
- Visible output byte and token ratios.
- Obvious repetition, encoding corruption, or gibberish indicators.
- Backend totals and per-chunk timing distributions as descriptive data only.

Stop before the judge panel if any output is missing, empty, corrupt, or clearly
truncated by an avoidable runner error. Preserve evidence and report the exact
failure rather than rerunning with changed settings.

## Pass criteria

- [ ] Exactly 61 deterministic chunks are generated from all Markdown files.
- [ ] Preflight passes without protocol deviations.
- [ ] Ollama completes all 61 chunks with stock settings and no warmup.
- [ ] Ollama has no loaded model before TurboFieldfare starts; an idle daemon is acceptable.
- [ ] The submitted CLI completes the 56 matching chunks at stock 4K; chunks
      48, 49, 50, 51, and 54 are excluded from both sides because they do not fit.
- [ ] Every response, timing record, and error record is preserved privately.
- [ ] Sanity checks find no catastrophic runner/output failure.
