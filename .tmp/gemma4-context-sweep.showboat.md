# TurboFieldfare context sweep

*2026-08-05T01:58:31Z by Showboat 0.6.1*
<!-- showboat-id: 066c811c-3d59-4172-9bab-705c3c15863b -->

Privacy boundary: this public-safe notebook records only anonymous chunk indices and aggregate resource/timing measurements. It excludes source text, summaries, source paths, filenames, topics, private configuration values, exact commands containing confidential values, and raw logs. This notebook starts the separately stored TurboFieldfare context sweep with one discarded 4K warmup; later variations change context only.

Sweep warmup: one discarded TurboFieldfare run on the largest selected chunk at context 4096. Immediately before its launch, the private runner repeats the full AGENTS.md gate and requires no active TurboFieldfare or Ollama model owner. Temperature 1.0, Top-K 64, Top-P 0.95, and repetition penalty 1.0 are fixed; the runner owns a finite process-group timeout.

```bash
uv run --script summarisation/showboat/private_benchmark.py warmup turbofieldfare --largest --context 4096 --series sweep
```

```output
turbofieldfare chunk=06 context=4096 status=ok wall_seconds=55.752 peak_rss_mib=1656.4 memory_free_before=71 memory_free_after=69
```

Warmup completed exactly once on anonymous largest chunk 06: exit 0; wall time 55.752 seconds; peak apparent RSS 1656.4 MiB; free memory 71% to 69%. The discarded output is stored only in the private sweep result directory. The post-run gate is clear, so no model owner remains.

Sweep measurement item 27: run the same anonymous largest chunk once at context 4096 after the discarded warmup. This is a measured result in the separate sweep series; all sampling controls remain fixed (temperature 1.0, Top-K 64, Top-P 0.95, repetition penalty 1.0). The private runner repeats the complete AGENTS.md preflight immediately before launch and has a finite owned-process-group timeout.

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare --largest --context 4096 --series sweep
```

```output
turbofieldfare chunk=06 context=4096 status=ok wall_seconds=58.183 peak_rss_mib=1660.1 memory_free_before=69 memory_free_after=68
```

Item 27 completed once. The private measurement artifact records an exit-0 measured sweep result at 4096 on anonymous chunk 06. To avoid duplicating a completed model invocation, the following Showboat entry inspects only the public-safe aggregate fields from that artifact.

```bash
jq '{backend, chunk, context, series, warmup, exit_code, wall_seconds, peak_rss_mib, memory_free_before_percent, memory_free_after_percent, output_bytes, runner_error}' .tmp/confidential-gemma4-comparison/sweep/measured/turbofieldfare/context-4096/chunk-06/measurement.json
```

```output
{
  "backend": "turbofieldfare",
  "chunk": 6,
  "context": 4096,
  "series": "sweep",
  "warmup": false,
  "exit_code": 0,
  "wall_seconds": 58.18332841596566,
  "peak_rss_mib": 1660.09375,
  "memory_free_before_percent": 69,
  "memory_free_after_percent": 68,
  "output_bytes": 3357,
  "runner_error": null
}
```

Item 28: one TurboFieldfare context sweep measurement of the private largest chunk at 8192 context. Sampling configuration remains unchanged; the action repeats the complete model gate and owns a finite process-group timeout.

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare --largest --context 8192 --series sweep
```

```output
turbofieldfare chunk=06 context=8192 status=ok wall_seconds=58.032 peak_rss_mib=1667.0 memory_free_before=68 memory_free_after=66
```

Item 29 reconciliation: the private sweep artifact already contains one valid completed TurboFieldfare measurement for anonymous largest chunk 06 at context 16384. No duplicate model invocation is permitted. The following command prints only an allowlisted aggregate; it excludes paths, source material, summaries, argv, logs, hashes, and private provenance.

```bash
./.tmp/item29_record.py
```

```output
{"backend": "turbofieldfare", "chunk": 6, "context": 16384, "exit_code": 0, "memory_free_after_percent": 62, "memory_free_before_percent": 68, "output_bytes": 3243, "peak_rss_mib": 1648.359375, "runner_error": null, "series": "sweep", "wall_seconds": 59.47545083286241, "warmup": false}
```

Item 30: one TurboFieldfare context-sweep measurement of the private largest chunk at context 32768. Sampling configuration remains fixed (temperature 1.0, Top-K 64, Top-P 0.95, repetition penalty 1.0); no other model workload is active. Immediately before launch the private runner repeats the complete AGENTS.md model gate and owns a finite process-group timeout.

```bash
uv run --script summarisation/showboat/private_benchmark.py measure turbofieldfare --largest --context 32768 --series sweep
```

```output
turbofieldfare chunk=06 context=32768 status=ok wall_seconds=53.812 peak_rss_mib=1710.0 memory_free_before=67 memory_free_after=61
```

Item 31: one TurboFieldfare context-sweep measurement of the private largest chunk at context 65536. Sampling configuration remains fixed (temperature 1.0, Top-K 64, Top-P 0.95, repetition penalty 1.0); no other model workload is active. Immediately before launch the private runner repeats the complete AGENTS.md model gate and owns a finite process-group timeout.

```bash
jq '{backend, chunk, context, series, warmup, exit_code, wall_seconds, peak_rss_mib, memory_free_before_percent, memory_free_after_percent, output_bytes, runner_error}' .tmp/confidential-gemma4-comparison/sweep/measured/turbofieldfare/context-65536/chunk-06/measurement.json
```

```output
{
  "backend": "turbofieldfare",
  "chunk": 6,
  "context": 65536,
  "series": "sweep",
  "warmup": false,
  "exit_code": 0,
  "wall_seconds": 59.226463166065514,
  "peak_rss_mib": 1632.640625,
  "memory_free_before_percent": 61,
  "memory_free_after_percent": 61,
  "output_bytes": 3179,
  "runner_error": null
}
```
