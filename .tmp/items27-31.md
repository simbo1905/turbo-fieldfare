# Items 27–31 — one TurboFieldfare context setting per task

Use the largest prepared chunk, determined privately without publishing a
source name. Invoke separately: item 27 context 4096, item 28 context 8192,
item 29 context 16384, item 30 context 32768, item 31 context 65536. For each
item append one Showboat note, check memory/process state, then run exactly one
`showboat exec` with `private_benchmark.py measure turbofieldfare CHUNK
--context CONTEXT`. Do not change temperature, Top-K, Top-P, repetition penalty,
or any other setting. Do not loop. Pop failures and stop; stage the notebook
after every success.
