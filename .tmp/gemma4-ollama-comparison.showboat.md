# Gemma 4 confidential-material Ollama comparison

*2026-08-05T01:02:47Z by Showboat 0.6.1*
<!-- showboat-id: 593eb26f-f3d6-4580-be3a-c27ed9cf2f20 -->

Privacy boundary: this public-safe notebook records only aggregate checks and measurements. It excludes source text, summaries, source paths, filenames, topics, private configuration values, raw logs, and commands containing confidential values. This is a one-time discarded warmup using native local Ollama defaults; no sampling or context options are supplied.

```bash
uv run --script summarisation/showboat/private_benchmark.py preflight
```

```output
preflight ok memory_free_percent=46
```

Item 14: run exactly one discarded Ollama warmup on anonymous chunk 00. Immediately before launch, the runner repeats the complete AGENTS.md model gate, including toolchain, disk, free-memory, completed-model, model-owner, and unloaded-Ollama checks. The command supplies no Ollama sampling or context options and has a finite owned-process timeout.

```bash
uv run --script summarisation/showboat/private_benchmark.py warmup ollama 0
```

```output
ollama chunk=00 context=4096 status=ok wall_seconds=55.952 peak_rss_mib=18517.4 memory_free_before=46 memory_free_after=9
```

Item 14 completed: the one discarded native-default Ollama warmup returned exit 0 after 55.952 seconds; sampled peak apparent RSS was 18517.4 MiB. The warmup generated no measured candidate. The local Ollama owner was confirmed clear before this notebook was staged.

Item 15: run exactly one measured native-default Ollama summary for anonymous chunk 00. Immediately before launch, the runner repeats the complete AGENTS.md gate. No Ollama sampling or context options are supplied; the runner owns a finite-timeout process group.

```bash
uv run --script summarisation/showboat/private_benchmark.py measure ollama 0
```

```output
ollama chunk=00 context=4096 status=ok wall_seconds=48.352 peak_rss_mib=18564.3 memory_free_before=76 memory_free_after=9
```
