# review03 — privacy-safe filesystem errors

Work only on review finding P1 about private paths leaking through uncaught filesystem errors. Use Red/Green TDD to trigger missing/unreadable private files and prove the public stderr has a generic message with no configured path, traceback, source name, or content, while detailed diagnostics are retained only in an ignored private artifact under the configured `.tmp` result root where possible. Catch at the CLI privacy boundary. Use uv only; no corpus/model/network. Do not commit. Report exact files/tests.
