# Items 15–26 — one Ollama measured chunk per task

Invoke this prompt with the assigned item number and chunk number: item 15 is
chunk 00 through item 26 for chunk 11. Run exactly one command: append a
Showboat note, check memory/process state, then use one `showboat exec` to run
`private_benchmark.py measure ollama CHUNK`. Do not run another chunk, context
setting, loop, or background job. Ollama receives native defaults only and the
private runner applies a finite timeout while sampling apparent RSS. Pop a
failed entry and stop. On success stage the growing Showboat notebook with
`git add -f`, and report only public-safe output and the item number.
