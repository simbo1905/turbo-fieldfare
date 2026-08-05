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
