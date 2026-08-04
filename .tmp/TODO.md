# Serial Showboat execution ledger

No model run has occurred. Every item must be executed independently, through
Showboat, with its own task/subagent, finite timeout, resource check, and
`git add -f .tmp/gemma4-comparison.showboat.md` after a successful append.

00. Bootstrap private config, privacy-safe preflight, initialize notebook.
01. Prepare corpus; TurboFieldfare discarded warmup on chunk 00.
02. TurboFieldfare measured chunk 00.
03. TurboFieldfare measured chunk 01.
04. TurboFieldfare measured chunk 02.
05. TurboFieldfare measured chunk 03.
06. TurboFieldfare measured chunk 04.
07. TurboFieldfare measured chunk 05.
08. TurboFieldfare measured chunk 06.
09. TurboFieldfare measured chunk 07.
10. TurboFieldfare measured chunk 08.
11. TurboFieldfare measured chunk 09.
12. TurboFieldfare measured chunk 10.
13. TurboFieldfare measured chunk 11.
14. Ollama discarded warmup on chunk 00.
15. Ollama measured chunk 00.
16. Ollama measured chunk 01.
17. Ollama measured chunk 02.
18. Ollama measured chunk 03.
19. Ollama measured chunk 04.
20. Ollama measured chunk 05.
21. Ollama measured chunk 06.
22. Ollama measured chunk 07.
23. Ollama measured chunk 08.
24. Ollama measured chunk 09.
25. Ollama measured chunk 10.
26. Ollama measured chunk 11.
27. Largest private chunk, TurboFieldfare context 4096.
28. Largest private chunk, TurboFieldfare context 8192.
29. Largest private chunk, TurboFieldfare context 16384.
30. Largest private chunk, TurboFieldfare context 32768.
31. Largest private chunk, TurboFieldfare context 65536.
32. Prepare local blinded pairs: 4K baseline versus each context candidate.
33. Record authorized local blind-pair ratings and aggregate wins/ties.
34. Produce public report, privacy audit, append final notebook, stage, publish,
    and revision-verify the sanitized Gist.

Prompt mapping: `item00.md`, `item01.md`, `items02-13.md`, `item14.md`,
`items15-26.md`, `items27-31.md`, `item32.md`, `item33.md`, `item34.md`.
