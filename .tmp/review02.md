# review02 — timeout process-tree cleanup

Work only on review finding P1 about orphaned model children. Use Red/Green TDD with harmless local child processes: prove launch starts an owned process group, sends TERM to the group on timeout, waits a bounded grace period, then sends KILL to the group if needed, leaving no descendant. Do not kill any pre-existing/user process. Use uv scripts only; no model run. Do not commit. Report exact files/tests.
