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
