# item16 - Upstream CLI runtime controls

## Status

Completed on 2026-08-05.

## Objective

Contribute the five existing runtime controls to `TurboFieldfareCLI` as a
focused upstream change suitable for scripted batch processing and reproducible
testing. Preserve all existing generation defaults and validation behavior.

## Delivered scope

- `--expert-cache-slots`: 8, 16, 24, or 32; default 16.
- `--expert-cache-policy`: `lfu` or `lru`; default `lfu`.
- `--prefill`: `on` or `off`; default `on`.
- `--prefill-chunk-tokens`: 32, 64, or 128; default 128.
- `--rdadvise`: `off`, `default`, `bounded`, or `adaptive`; default `off`.

The following existing behavior was deliberately left unchanged:

- `--max-new` defaults to 1024.
- `--max-context` defaults to 4096 and accepts any positive integer.
- Temperature defaults to 0.2.
- Top-K defaults to 64.
- Top-P defaults to 0.95.
- Repetition penalty defaults to 1.0.

## Upstream records

- Issue: https://github.com/drumih/turbo-fieldfare/issues/92
- Branch: `issue-92-cli-runtime-controls`
- Clean commit: `93b944d` (`Expose runtime controls in CLI`)
- Draft PR: https://github.com/drumih/turbo-fieldfare/pull/93
- Base: `upstream/main` at `3249be4`

The PR remains draft until the exact submitted CLI has completed the real-model
batch validation in item18.

## Files in the clean commit

- `Sources/TurboFieldfareCLI/Args.swift`
- `Sources/TurboFieldfareCLI/Run.swift`
- `Tests/TurboFieldfare/Core/CLI/CLIArgumentsTests.swift`

No course names, source-material paths, private filenames, benchmark artifacts,
credentials, or model data were included.

## Validation

- `Scripts/test.sh`: 646 tests passed.
- `swift build -c release`: passed.
- `.build/release/TurboFieldfareCLI --help`: passed and listed the five options.
- `ruby Scripts/check_markdown_links.rb`: 22 Markdown files passed.
- `git diff --check`: passed.

## Completion criteria

- [x] Issue describes batch and reproducibility need without discussing defaults.
- [x] Branch starts at current upstream main.
- [x] Exactly five runtime options are added.
- [x] Existing generation defaults remain unchanged.
- [x] Focused tests cover defaults, accepted values, and rejected values.
- [x] Branch and commit are pushed to the fork.
- [x] Upstream draft PR closes issue 92 and follows the PR template.
