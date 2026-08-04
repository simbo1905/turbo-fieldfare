# Item 33 — local blind-pair scoring

Run only after an authorized local human has supplied ratings in the private
ratings file. Use `local_pairwise.py score` once per comparison or aggregate as
the local sheet requires. No remote judge is allowed. Append only aggregate
wins/losses/ties to Showboat, never any pair text. Pop failures and stage the
notebook after success.
