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

```bash
uv run --script summarisation/showboat/private_benchmark.py measure ollama 1
```

```output
ollama chunk=01 context=4096 status=ok wall_seconds=57.924 peak_rss_mib=18559.1 memory_free_before=77 memory_free_after=9
```

```bash
uv run --script summarisation/showboat/private_benchmark.py measure ollama 2
```

```output
ollama chunk=02 context=4096 status=ok wall_seconds=73.082 peak_rss_mib=18549.4 memory_free_before=77 memory_free_after=9
```

```bash
measurement=$(find .tmp -type f -path "*/measured/ollama/context-4096/chunk-02/measurement.json" -print -quit); test -n "$measurement"; jq -er "if (.backend == \"ollama\" and .chunk == 2 and .context == 4096 and (.exit_code | type) == \"number\" and (.wall_seconds | type) == \"number\" and (.peak_rss_mib | type) == \"number\" and (.memory_free_before_percent | type) == \"number\" and (.memory_free_after_percent | type) == \"number\") then \"ollama chunk=02 context=\\(.context) exit=\\(.exit_code) wall_seconds=\\(.wall_seconds|floor) peak_rss_mib=\\(.peak_rss_mib|floor) memory_free_before=\\(.memory_free_before_percent) memory_free_after=\\(.memory_free_after_percent)\" else error(\"aggregate measurement validation failed\") end" "$measurement"
```

```output
ollama chunk=02 context=4096 exit=0 wall_seconds=73 peak_rss_mib=18549 memory_free_before=77 memory_free_after=9
```

```bash
uv run --script summarisation/showboat/private_benchmark.py measure ollama 3
```

```output
ollama chunk=03 context=4096 status=ok wall_seconds=65.837 peak_rss_mib=18508.8 memory_free_before=75 memory_free_after=8
```

```bash
uv run --script summarisation/showboat/private_benchmark.py measure ollama 4
```

```output
ollama chunk=04 context=4096 status=ok wall_seconds=66.068 peak_rss_mib=18556.0 memory_free_before=75 memory_free_after=8
```

```bash
uv run --script summarisation/showboat/private_benchmark.py measure ollama 5
```

```output
ollama chunk=05 context=4096 status=ok wall_seconds=54.926 peak_rss_mib=18555.1 memory_free_before=72 memory_free_after=10
```

```bash
uv run --script summarisation/showboat/private_benchmark.py measure ollama 6
```

```output
ollama chunk=06 context=4096 status=ok wall_seconds=60.125 peak_rss_mib=18561.4 memory_free_before=75 memory_free_after=9
```

```bash
uv run --script summarisation/showboat/private_benchmark.py measure ollama 7
```

```output
ollama chunk=07 context=4096 status=ok wall_seconds=57.349 peak_rss_mib=18555.9 memory_free_before=73 memory_free_after=9
```

```bash
uv run --script summarisation/showboat/private_benchmark.py measure ollama 8
```

```output
ollama chunk=08 context=4096 status=ok wall_seconds=59.244 peak_rss_mib=18480.1 memory_free_before=72 memory_free_after=70
```
