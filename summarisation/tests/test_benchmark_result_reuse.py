"""Focused tests for fail-closed benchmark result-directory handling."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "benchmark_run.py"


class BenchmarkResultReuseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.temp = Path(self.tempdir.name)
        self.prepared = self.temp / "prepared"
        self.prepared.mkdir()
        chunk = self.prepared / "benchmark00.md"
        chunk.write_text("fixture transcript", encoding="utf-8")
        (self.prepared / "manifest.json").write_text(
            json.dumps({"chunks": [{"path": chunk.name}]}) + "\n",
            encoding="utf-8",
        )
        self.backend_marker = self.temp / "backend-ran"
        self.backend = self.temp / "fake_backend.py"
        self.backend.write_text(
            "#!/usr/bin/env -S uv run --script\n"
            "# /// script\n"
            "# requires-python = \">=3.11\"\n"
            "# dependencies = []\n"
            "# ///\n"
            "import pathlib, sys\n"
            "source, output, marker = map(pathlib.Path, sys.argv[1:4])\n"
            "marker.write_text(source.name, encoding='utf-8')\n"
            "output.parent.mkdir(parents=True, exist_ok=True)\n"
            "output.write_text('fresh summary', encoding='utf-8')\n",
            encoding="utf-8",
        )
        self.backend.chmod(0o755)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_benchmark(self, results: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(RUN),
                "--manifest",
                str(self.prepared / "manifest.json"),
                "--results",
                str(results),
                "--backend",
                "fake",
                "--backend-command",
                f"{self.backend} {{input}} {{output}} {self.backend_marker}",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_accepts_an_existing_empty_result_directory(self) -> None:
        results = self.temp / "empty-results"
        results.mkdir()

        completed = self.run_benchmark(results)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.backend_marker.read_text(encoding="utf-8"), "benchmark00.md")
        record = json.loads((results / "run-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(record["chunks"][0]["output_bytes"], len("fresh summary"))

    def test_rejects_nonempty_results_before_backend_or_stale_hashing(self) -> None:
        results = self.temp / "reused-results"
        stale = results / "outputs" / "benchmark00.md"
        stale.parent.mkdir(parents=True)
        stale.write_text("stale summary", encoding="utf-8")

        completed = self.run_benchmark(results)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("empty", completed.stderr.lower())
        self.assertFalse(self.backend_marker.exists())
        self.assertEqual(stale.read_text(encoding="utf-8"), "stale summary")
        self.assertFalse((results / "run-manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
