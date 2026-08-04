# Privacy-preserving Gemma 4 comparison notebook

This Gist contains a reproducible local protocol for comparing stock Ollama
`gemma4:26b` and TurboFieldfare on confidential instructional transcripts.
It intentionally contains no confidential source path, source filename, title,
topic, transcript, summary, raw backend log, model directory, API key, or
private configuration.

`private_benchmark.py` executes exactly one requested action. It does not loop
over the twelve chunks. It rejects result directories outside `.tmp`, captures
only public-safe status to stdout, applies a finite timeout to the actual
backend command, and stores all source-derived artifacts privately.

Install Showboat v0.6.1 on Darwin arm64 with checksum verification:

```bash
bash install_showboat.sh
export PATH="$PWD/.bin:$PATH"
```

Copy `private-config.template.json` to
`.tmp/showboat-private-config.json`, supply only local confidential paths in
that ignored file, and run the `SHOWBOAT_PROTOCOL.md` commands one at a time.
The published notebook is built by Showboat, so it mixes explanatory notes,
the exact path-safe commands, and captured public-safe output. If an entry is
wrong or fails, inspect only local private artifacts then remove the entry with
`showboat pop notebook.md` before retrying that one command.

The private wrapper imports the sibling corpus and backend scripts in this
Gist. TurboFieldfare uses the Gemma generation configuration (temperature 1.0,
Top-K 64, Top-P 0.95; repetition penalty 1.0). Ollama intentionally retains
its native local defaults, so results are reported as a real-user-path
comparison, not sampler-normalized throughput or quality evidence.

The final notebook provides an anonymized Video A/Video B table with duration
rounded to the nearest minute and independently one-time ±3% jittered sizes.
It also reports elapsed time and sampled apparent RSS. The private table must
never be joined with public source metadata.

Remote pairwise judging is forbidden for these confidential materials. If
quality is assessed, use an authorized human locally or a separately approved
local-only judge with blind labels; report it as a small local signal, not a
general quality claim.

`local_pairwise.py` prepares and scores those blind pairs strictly inside
`.tmp/`. It prints only pair counts and aggregate wins/ties, never summary
text. Use it only after the context sweep, comparing each context candidate to
the 4K baseline on the largest block.
