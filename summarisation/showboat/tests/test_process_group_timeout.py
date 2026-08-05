from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "summarisation" / "showboat" / "private_benchmark.py"
SPEC = importlib.util.spec_from_file_location("private_benchmark_process_group", RUNNER)
assert SPEC and SPEC.loader
BENCHMARK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCHMARK)


class ProcessGroupTimeoutTests(unittest.TestCase):
    def test_timeout_leaves_no_running_descendant(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            pid_file = base / "child.pid"
            adapter = base / "adapter.py"
            adapter.write_text(
                """#!/usr/bin/env -S uv run --script
# /// script
# requires-python = \">=3.11\"
# dependencies = []
# ///
import pathlib
import signal
import subprocess
import sys
import time

signal.signal(signal.SIGTERM, signal.SIG_IGN)
child = subprocess.Popen([
    sys.executable,
    "-c",
    "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)",
])
pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding="utf-8")
while True:
    time.sleep(1)
""",
                encoding="utf-8",
            )
            adapter.chmod(0o755)
            stdout, stderr = base / "stdout.bin", base / "stderr.bin"

            with mock.patch.object(BENCHMARK, "PROCESS_GROUP_TERM_GRACE_SECONDS", 0.1):
                with self.assertRaisesRegex(RuntimeError, "command timed out"):
                    BENCHMARK.launch([str(adapter), str(pid_file)], stdout, stderr, 1, False)

            child_pid = int(pid_file.read_text(encoding="utf-8"))
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                state = subprocess.run(
                    ["ps", "-o", "stat=", "-p", str(child_pid)],
                    text=True,
                    stdout=subprocess.PIPE,
                    check=False,
                    timeout=5,
                ).stdout.strip()
                if not state or state.startswith("Z"):
                    break
                time.sleep(0.05)
            else:
                self.fail("timed-out descendant is still running")

    def test_grace_expiry_sends_term_then_kill_to_owned_group(self) -> None:
        process = mock.Mock(pid=43210)
        process.poll.side_effect = [None]
        process.wait.side_effect = [subprocess.TimeoutExpired(["fixture"], 0.1), 0]
        with tempfile.TemporaryDirectory() as temporary, \
             mock.patch.object(BENCHMARK.subprocess, "Popen", return_value=process) as popen, \
             mock.patch.object(BENCHMARK.os, "killpg") as killpg, \
             mock.patch.object(BENCHMARK, "PROCESS_GROUP_TERM_GRACE_SECONDS", 0.1):
            base = Path(temporary)
            with self.assertRaisesRegex(RuntimeError, "command timed out"):
                BENCHMARK.launch(["fixture"], base / "out", base / "err", 0, False)

        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertEqual(
            killpg.call_args_list,
            [mock.call(43210, signal.SIGTERM), mock.call(43210, signal.SIGKILL)],
        )
        self.assertEqual(process.wait.call_count, 2)


if __name__ == "__main__":
    unittest.main()
