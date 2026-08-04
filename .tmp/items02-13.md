# Items 02–13 — one TurboFieldfare measured chunk per task

Invoke this prompt with the assigned item number and chunk number: item 02 is
chunk 00, item 03 is chunk 01, through item 13 for chunk 11. Run exactly one
command: append a concise Showboat note, check memory/process state, then use
one `showboat exec` to run `private_benchmark.py measure turbofieldfare CHUNK`.
Do not run another chunk, warmup, context setting, loop, or background job.
The private runner enforces a finite timeout and records elapsed time, sampled
peak RSS, and before/after free-memory percentage. If it fails, pop the failed
entry and stop. On success stage only `.tmp/gemma4-comparison.showboat.md` with
`git add -f` and report public-safe Showboat output plus the exact item number.
