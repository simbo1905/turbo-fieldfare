# item19 - Twelve-chunk AB/BA quality panel

## Status

Completed on 2026-08-05.

## Objective

Look only for evidence that TurboFieldfare is systematically and materially
worse than Ollama. This is not powered to rank small stylistic differences.
Judges must return TIE unless one output is clearly wrong or catastrophically
inferior on the supplied source.

## Sample

- Exclude chunks 48, 49, 50, 51, and 54, which do not fit stock 4K
  TurboFieldfare, from both backend sets before selection.
- Select exactly 12 chunks evenly across the remaining ordered comparable
  indices.
- Compute and record the selection algorithm before judging.
- Reuse the original 11K-window chunks and full outputs from item18.
- Do not substitute the earlier 1K speed-test blocks.

A suitable deterministic rule is to select 12 equally spaced positions from the
ordered 60 eligible indices, then verify it produces 12 unique indices
including both ends. Store the resulting indices in the panel manifest before
making judge calls.

## Calls

For each selected chunk:

1. Send source plus output A and output B to each of three large judge models.
2. Repeat with the outputs swapped, producing AB and BA presentations.
3. Require all three judges to return valid structured verdicts in both orders.

Total expected judge calls: 12 chunks x 2 orders x 3 judges = 72.

## Rubric

- Default to `TIE`.
- Ignore style, phrasing, formatting preference, and minor omission differences.
- Prefer an output only for a clear material factual or semantic advantage.
- Treat unsupported claims, contradictions of source, severe omissions, or
  unusable corruption as material failures.
- The question is whether there is evidence of catastrophic/systematic TF
  degradation, not which summary is marginally nicer.

## Scoring and validity

- Score preferred = 2, tie = 1, dispreferred = 0.
- Keep backend identity blinded until all verdicts are stored.
- Reverse BA labels before aggregation.
- If any judge response is invalid, stop the panel and preserve evidence. Do
  not silently drop judges or change the denominator.
- Report per-judge, per-order, per-chunk, and aggregate results.
- Inspect AB/BA disagreement as a position-bias diagnostic.

## Confidentiality

Source text and raw summaries remain under `.tmp`. Public reporting may include
only methodology, aggregate verdict counts, anonymized chunk indices, and
sanitized failure descriptions.

## Pass criteria

- [x] Twelve unique, evenly spaced eligible indices were selected: 00, 05, 10,
      15, 20, 25, 30, 35, 40, 45, 55, 60.
- [x] All 72 calls returned valid structured verdicts.
- [x] AB/BA labels were normalized correctly.
- [x] Default-TIE rubric was used unchanged for every call.
- [x] Results: 64 ties, 7 Ollama preferences, 1 TF preference. There is no
      panel-wide evidence of systematic catastrophic TF degradation, but one
      selected chunk received all six normalized preferences for Ollama and is
      reported as a material localized concern rather than diluted.
