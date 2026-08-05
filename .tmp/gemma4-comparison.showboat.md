# Gemma 4 confidential-material comparison

*2026-08-05T00:02:19Z by Showboat 0.6.1*
<!-- showboat-id: 731ee4b8-1780-42c4-936a-a7cfc8447a1b -->

Privacy boundary: this public-safe notebook records only aggregate checks and measurements. It excludes source text, summaries, source paths, filenames, topics, private configuration values, raw logs, and commands containing confidential values.

```bash
uv run --script summarisation/showboat/private_benchmark.py preflight
```

```output
preflight ok memory_free_percent=38
```

Item 01: prepare the confidential corpus once. The runner suppresses all private paths and source material; it has a 120-second internal preparation timeout.

```bash
uv run --script summarisation/showboat/private_benchmark.py prepare
```

```output
prepared chunks=12 videos=58
```

Item 01: run exactly one discarded TurboFieldfare warmup on chunk 00. Immediately before launch, the runner repeats the complete AGENTS.md model gate, including free-memory and model-owner checks; the configured finite timeout owns and terminates the process group if needed.

```bash
uv run --script summarisation/showboat/private_benchmark.py warmup turbofieldfare 0 --context 4096
```

```output
turbofieldfare chunk=00 context=4096 status=ok wall_seconds=70.484 peak_rss_mib=1564.8 memory_free_before=42 memory_free_after=41
```

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 0 --context 4096
```

```output
turbofieldfare chunk=00 context=4096 status=ok wall_seconds=66.121 peak_rss_mib=1577.7 memory_free_before=54 memory_free_after=41
```

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 1 --context 4096
```

```output
turbofieldfare chunk=01 context=4096 status=ok wall_seconds=73.654 peak_rss_mib=1563.2 memory_free_before=50 memory_free_after=40
```

Item 03: one measured TurboFieldfare run on anonymous chunk 01 at context 4096. The runner performs the complete AGENTS.md preflight immediately before this sole backend invocation and owns a finite timeout.

Item 04: one measured TurboFieldfare run on anonymous chunk 02 at context 4096. The runner repeats the complete AGENTS.md preflight immediately before the sole backend invocation and has a finite owned-process timeout.

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 2 --context 4096
```

```output
turbofieldfare chunk=02 context=4096 status=ok wall_seconds=66.358 peak_rss_mib=1572.9 memory_free_before=48 memory_free_after=39
```

Item 05: one measured TurboFieldfare run on anonymous chunk 03 at context 4096. The runner repeats the complete AGENTS.md preflight immediately before the sole backend invocation and owns a finite process-group timeout.

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 3 --context 4096
```

```output
turbofieldfare chunk=03 context=4096 status=ok wall_seconds=78.506 peak_rss_mib=1538.7 memory_free_before=47 memory_free_after=39
```

Item 06: one measured TurboFieldfare run on anonymous chunk 04 at context 4096. The runner repeats the complete AGENTS.md preflight immediately before the sole backend invocation and owns a finite process-group timeout.

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 4 --context 4096
```

```output
turbofieldfare chunk=04 context=4096 status=ok wall_seconds=79.090 peak_rss_mib=1552.6 memory_free_before=46 memory_free_after=41
```

Item 07: one measured TurboFieldfare run on anonymous chunk 05 at context 4096. The runner repeats the full AGENTS.md preflight immediately before this sole backend invocation and owns a finite process-group timeout.

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 5 --context 4096
```

```output
turbofieldfare chunk=05 context=4096 status=ok wall_seconds=71.497 peak_rss_mib=1578.4 memory_free_before=48 memory_free_after=41
```

Item 08: one measured TurboFieldfare run on anonymous chunk 06 at context 4096. The runner repeats the complete AGENTS.md preflight immediately before this sole backend invocation, checks model ownership and resources, and owns a finite process-group timeout.

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 6 --context 4096
```

```output
turbofieldfare chunk=06 context=4096 status=ok wall_seconds=73.594 peak_rss_mib=1584.7 memory_free_before=48 memory_free_after=43
```

Item 08 record: the sole TurboFieldfare invocation completed before the runner returned its measurement artifact. This public-safe verification reads only non-confidential measurement fields and does not start another model workload.

```bash
task_root=$(jq -r .results_root .tmp/showboat-private-config.json); rg '^[[:space:]]*"(backend|chunk|context|exit_code|wall_seconds|peak_rss_mib|memory_free_before_percent|memory_free_after_percent)":' "$task_root/measured/turbofieldfare/context-4096/chunk-06/measurement.json"
```

```output
  "backend": "turbofieldfare",
    "context": 4096,
  "chunk": 6,
  "context": 4096,
  "exit_code": 0,
  "memory_free_after_percent": 43,
  "memory_free_before_percent": 48,
  "peak_rss_mib": 1584.671875,
  "wall_seconds": 73.5944699998945,
```

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 7
```

```output
turbofieldfare chunk=07 context=4096 status=ok wall_seconds=75.639 peak_rss_mib=1587.5 memory_free_before=48 memory_free_after=43
```

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 8 --context 4096
```

```output
turbofieldfare chunk=08 context=4096 status=ok wall_seconds=73.131 peak_rss_mib=1584.6 memory_free_before=46 memory_free_after=42
```

Item 10 completed: TurboFieldfare anonymous chunk 08 at context 4096 exited 0; wall time 73.131 seconds; peak apparent RSS 1584.6 MiB; free memory 46% to 42%. The model-owner check is clear after completion. The one model invocation was preflight-gated and had an owned finite process-group timeout.

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 9 --context 4096
```

```output
turbofieldfare chunk=09 context=4096 status=ok wall_seconds=77.759 peak_rss_mib=1585.9 memory_free_before=47 memory_free_after=42
```

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 10 --context 4096
```

```output
turbofieldfare chunk=10 context=4096 status=ok wall_seconds=76.280 peak_rss_mib=1582.5 memory_free_before=47 memory_free_after=40
```

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare 11 --context 4096
```

```output
turbofieldfare chunk=11 context=4096 status=ok wall_seconds=80.644 peak_rss_mib=1570.0 memory_free_before=46 memory_free_after=41
```
