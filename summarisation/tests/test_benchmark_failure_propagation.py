"""Focused tests for benchmark failure propagation with complete audit output."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "benchmark_run.py"


class BenchmarkFailurePropagationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.temp = Path(self.tempdir.name)
        self.prepared = self.temp / "prepared"
        self.prepared.mkdir()
        chunks = []
        for number in range(3):
            path = self.prepared / f"benchmark{number:02d}.md"
            path.write_text(f"fixture transcript {number}", encoding="utf-8")
            chunks.append({"path": path.name})
        (self.prepared / "manifest.json").write_text(
            json.dumps({"chunks": chunks}) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_backend(self, body: str) -> Path:
        backend = self.temp / "fake_backend.py"
        backend.write_text(
            "#!/usr/bin/env -S uv run --script\n"
            "# /// script\n"
            "# requires-python = \">=3.11\"\n"
            "# dependencies = []\n"
            "# ///\n"
            + body,
            encoding="utf-8",
        )
        backend.chmod(0o755)
        return backend

    def run_benchmark(self, backend: Path, results_name: str) -> tuple[subprocess.CompletedProcess[str], Path]:
        results = self.temp / results_name
        completed = subprocess.run(
            [
                str(RUN),
                "--manifest",
                str(self.prepared / "manifest.json"),
                "--results",
                str(results),
                "--backend",
                "fake",
                "--backend-command",
                f"{backend} {{input}} {{output}}",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return completed, results

    def assert_complete_audit(self, results: Path) -> dict:
        manifest_path = results / "run-manifest.json"
        self.assertTrue(manifest_path.is_file())
        record = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(len(record["chunks"]), 3)
        for chunk in record["chunks"]:
            self.assertTrue((results / chunk["stdout_path"]).is_file())
            self.assertTrue((results / chunk["stderr_path"]).is_file())
        return record

    def test_returns_nonzero_after_recording_all_chunks_when_backend_fails(self) -> None:
        backend = self.write_backend(
            "import pathlib, sys\n"
            "source, output = map(pathlib.Path, sys.argv[1:3])\n"
            "output.parent.mkdir(parents=True, exist_ok=True)\n"
            "output.write_text('summary:' + source.name, encoding='utf-8')\n"
            "raise SystemExit(7 if source.name == 'benchmark01.md' else 0)\n"
        )

        completed, results = self.run_benchmark(backend, "backend-failed")

        self.assertNotEqual(completed.returncode, 0)
        record = self.assert_complete_audit(results)
        self.assertEqual([chunk["exit_status"] for chunk in record["chunks"]], [0, 7, 0])
        self.assertTrue(all(chunk["output_sha256"] for chunk in record["chunks"]))

    def test_returns_nonzero_after_recording_all_chunks_when_output_is_missing(self) -> None:
        backend = self.write_backend(
            "import pathlib, sys\n"
            "source, output = map(pathlib.Path, sys.argv[1:3])\n"
            "if source.name != 'benchmark01.md':\n"
            "    output.parent.mkdir(parents=True, exist_ok=True)\n"
            "    output.write_text('summary:' + source.name, encoding='utf-8')\n"
        )

        completed, results = self.run_benchmark(backend, "output-missing")

        self.assertNotEqual(completed.returncode, 0)
        record = self.assert_complete_audit(results)
        missing = record["chunks"][1]
        self.assertEqual(missing["exit_status"], 0)
        self.assertEqual(missing["output_bytes"], 0)
        self.assertIsNone(missing["output_sha256"])

    def test_returns_zero_when_every_backend_and_output_succeeds(self) -> None:
        backend = self.write_backend(
            "import pathlib, sys\n"
            "source, output = map(pathlib.Path, sys.argv[1:3])\n"
            "output.parent.mkdir(parents=True, exist_ok=True)\n"
            "output.write_text('summary:' + source.name, encoding='utf-8')\n"
        )

        completed, results = self.run_benchmark(backend, "success")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        record = self.assert_complete_audit(results)
        self.assertTrue(all(chunk["exit_status"] == 0 for chunk in record["chunks"]))
        self.assertTrue(all(chunk["output_sha256"] for chunk in record["chunks"]))


if __name__ == "__main__":
    unittest.main()
