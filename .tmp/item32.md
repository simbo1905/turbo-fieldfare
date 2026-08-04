# Item 32 — prepare local blind context pairs

Run only after all context items succeed. Use `local_pairwise.py prepare` to
create one or more blind local pairs between the 4K baseline and each context
candidate for the largest chunk. Keep every pair inside `.tmp`; do not send any
text or summary to a remote API. Append only the public-safe pair count to
Showboat, pop any failed entry, and stage the notebook.
