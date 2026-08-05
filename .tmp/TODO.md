# Serial Showboat execution ledger

No model run has occurred. Every item must be executed independently, through
Showboat, with its own task/subagent, finite timeout, resource check, and
`git add -f .tmp/gemma4-comparison.showboat.md` after a successful append.

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

Review prompt mapping: `review00.md` through `review08.md`.

Execution prompt mapping: `item00.md`, `item01.md`, `items02-13.md`, `item14.md`,
`items15-26.md`, `items27-31.md`, `item32.md`, `item33.md`, `item34.md`.
