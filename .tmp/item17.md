# item17 - High-water tag and clean-CLI rebase

## Status

Completed on 2026-08-05.

## Objective

Preserve the pre-rebase experimental history, then make the clean upstream PR
implementation the sole CLI/test implementation used by the experimental
branch.

## Preservation point

- Original experimental head: `148ef65`.
- Annotated tag: `summarisation-cli-high-water-2026-08-05`.
- The tag was pushed to `origin` before rebasing.

## Rebase

- Branch: `simbo1905/summarisation-cli`.
- New base: clean PR branch `issue-92-cli-runtime-controls` at `93b944d`.
- Rebased 49 experimental commits previously based on `7a99f2a`.
- The old mixed CLI commit `81936d3` was not retained as the CLI source.
- Its replacement, `7a753e8` (`Use submitted CLI runtime controls`), keeps the
  private workflow changes while resolving all public CLI and test files to the
  exact clean PR versions.
- Rebased head after completion: `b4d86d6`.

During the rebase, ignored private files were preserved in a local stash and
restored afterward. No reset was used and no private file was deleted.

## Identity check

These files produced no diff against `issue-92-cli-runtime-controls`:

- `Sources/TurboFieldfareCLI/Args.swift`
- `Sources/TurboFieldfareCLI/Run.swift`
- `Tests/TurboFieldfare/Core/CLI/CLIArgumentsTests.swift`

## Validation

- `Scripts/test.sh`: 646 tests passed after the rebase.
- Working tree was clean after private files were restored.

## Remote state

The rewritten experimental branch was force-pushed with lease to `origin` after
the user explicitly authorized it. Its previous history remains safely
available through the pushed high-water tag. The remote branch now ends at
`b4d86d6` and contains clean PR commit `93b944d` in its ancestry.

## Completion criteria

- [x] Original experimental head is tagged and the tag is remote.
- [x] Experimental history is rebased onto the clean PR branch.
- [x] Old CLI/default changes are absent from the final public files.
- [x] Clean PR CLI and tests are byte-for-byte authoritative.
- [x] Full package tests pass after the rebase.
- [x] Rebased branch is pushed to the fork with the high-water tag as recovery.
