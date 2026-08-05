# review01 — full preflight per model invocation

Work only on review finding P1 about stale/missing preflight. Use Red/Green TDD: add tests proving every independent warmup/measure performs the complete AGENTS.md gate immediately before launch (macOS 26+, Swift 6.2+, disk, memory, completed model, release CLI, Ollama model, and no loaded/model-owning process), then implement a reusable full gate. Keep tests fully mocked: no model, corpus, or Ollama inference. Use uv scripts only. Do not commit. Report exact files/tests.
