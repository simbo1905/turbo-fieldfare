# Serial Showboat execution ledger

TurboFieldfare items 01–13 are recorded in `.tmp/gemma4-comparison.showboat.md`.
Every remaining item must be executed independently, with its own fresh agent,
finite timeout, resource check, and a staged Showboat notebook append.

Review remediation gates (complete with Red/Green tests before item 00):

review00. [done] Give Ollama the exact same summary instruction as TurboFieldfare.
review01. [done] Run the complete AGENTS.md preflight immediately before every model invocation.
review02. [done] On timeout, terminate the entire owned backend process group with a kill fallback.
review03. [done] Redact filesystem failures at the public Showboat boundary while retaining private diagnostics.
review04. [done] Refuse a reused/non-empty generic benchmark result directory and stale outputs.
review05. [done] Preserve the generic run manifest but return nonzero if any backend chunk fails.
review06. [done] Require an explicit multi-provider-compatible endpoint for GPT, Claude, and Kimi judges.
review07. [done] Resolve tool siblings correctly in both repository and flat-Gist layouts.
review08. [done] Record complete private measurement provenance and publish only sanitized provenance.

00. [done] Bootstrap private config, privacy-safe preflight, initialize notebook.
01. [done] Prepare corpus; TurboFieldfare discarded warmup on chunk 00.
02. [done] TurboFieldfare measured chunk 00.
03. [done] TurboFieldfare measured chunk 01.
04. [done] TurboFieldfare measured chunk 02.
05. [done] TurboFieldfare measured chunk 03.
06. [done] TurboFieldfare measured chunk 04.
07. [done] TurboFieldfare measured chunk 05.
08. [done] TurboFieldfare measured chunk 06.
09. [done] TurboFieldfare measured chunk 07.
10. [done] TurboFieldfare measured chunk 08.
11. [done] TurboFieldfare measured chunk 09.
12. [done] TurboFieldfare measured chunk 10.
13. [done] TurboFieldfare measured chunk 11.
14. [done] Ollama discarded warmup on chunk 00.
15. [done] Ollama measured chunk 00.
16. [done] Ollama measured chunk 01.
17. [done] Ollama measured chunk 02.
18. [done] Ollama measured chunk 03.
19. [x] Ollama measured chunk 04.
20. [done] Ollama measured chunk 05.
21. [done] Ollama measured chunk 06.
22. [done] Ollama measured chunk 07.
23. [done] Ollama measured chunk 08.
24. [done] Ollama measured chunk 09.
25. [done] Ollama measured chunk 10.
26. [done] Ollama measured chunk 11.
27w. [done] Discarded TurboFieldfare context-sweep warmup on the largest private chunk at 4096.
27. [done] Largest private chunk, TurboFieldfare context 4096.
28. [done] Largest private chunk, TurboFieldfare context 8192.
29. [done] Largest private chunk, TurboFieldfare context 16384.
30. [done] Largest private chunk, TurboFieldfare context 32768.
31. [done] Largest private chunk, TurboFieldfare context 65536.
32. [done] Prepare the ten private context-pairwise choices and the one-shot three-judge spot-check command.
33. [blocked] The authorized 4K-vs-64K three-judge spot check reached the documented Zen endpoints, but all three returned HTTP 403 before any verdict; no aggregate is claimed.
34. [done] Produced a privacy-scanned aggregate report, published and raw-content-verified
    secret Gist revision `ad29164514073f30aaba93c740cffcd30d144d2f`.

Review prompt mapping: `review00.md` through `review08.md`.

Execution prompt mapping: `item00.md`, `item01.md`, `items02-13.md`, `item14.md`,
`items15-26.md`, `items27-31.md`, `item32.md`, `item33.md`, `item34.md`.
