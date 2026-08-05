# item20 - Publish validation and finalize PR 93

## Status

Completed on 2026-08-05.

## Objective

Record the real-model validation honestly, sanitize all public material, update
the upstream pull request, and leave a reproducible private audit trail.

## Private report

Write a final report under `.tmp` containing:

- Clean PR commit and rebased experimental commit.
- Hardware, RAM, macOS, Swift, disk, and memory-pressure preflight.
- Corpus construction and exact chunk count.
- Exact command shapes and all protocol deviations.
- Complete Ollama and TurboFieldfare run manifests.
- Sanity-check results.
- Twelve-chunk panel selection, 72 verdict records, and aggregate result.
- A direct conclusion limited to whether TF showed catastrophic/systematic
  quality degradation relative to Ollama.

## PR update

Update https://github.com/drumih/turbo-fieldfare/pull/93 after item18:

1. Replace "real-model validation in progress" with the completed stock CLI
   validation details.
2. Report hardware, RAM, macOS, Swift, prompt/chunk shape, generated token
   totals, complete timing summary, and any protocol deviation required by
   `CONTRIBUTING.md`.
3. State that the submitted defaults were used and the new options were omitted
   for the stock batch pass.
4. Keep source material, private paths, filenames, raw summaries, credentials,
   model weights, and unrelated process details out of the PR.
5. Mark the PR ready only after the public text has passed a sanitization scan.

Removing draft status is mandatory after the submitted code passes item18. Do
not leave PR 93 in draft after successful real-model validation.

The quality panel is supporting confidence evidence and need not be pasted in
full. Include only a concise aggregate statement if it is useful to reviewers.

## Publication checks

- Search all proposed public text for private paths, course/source identifiers,
  credentials, hostnames, raw source, and raw model output.
- Verify the PR diff still contains only the three intended public files.
- Re-run `git diff --check`, `Scripts/test.sh`, `swift build -c release`, and
  `ruby Scripts/check_markdown_links.rb` if the PR branch changes.
- Confirm issue 92 and PR 93 cross-reference each other and the PR closes the
  issue.

## Experimental branch

The rebased experimental branch was force-pushed with lease after explicit user
authorization. The remote now uses the clean submitted CLI. The pre-rebase
state remains preserved by `summarisation-cli-high-water-2026-08-05`.

## Completion criteria

- [x] Private final report is complete and internally consistent.
- [x] PR validation section contains the real-model stock CLI run.
- [x] Public sanitization scan passes.
- [x] Draft status is removed and PR 93 is marked ready for review.
- [x] Final issue/PR/tag/commit URLs and test outcomes are reported to the user.

## Completion record

- Published Gist: `https://gist.github.com/simbo1905/6ec2912e544cf7a7f361ba0b5de90935`.
- README and `metrics.json` content hashes were verified against the published
  revision after update.
- PR: `https://github.com/drumih/turbo-fieldfare/pull/93`.
- Issue: `https://github.com/drumih/turbo-fieldfare/issues/92`.
- PR 93 was marked ready after its validation text was updated.
- Private output, source, raw judge responses, and private paths remain only
  under `.tmp` and were excluded from all public reporting.
