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
