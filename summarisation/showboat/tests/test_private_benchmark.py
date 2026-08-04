from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "summarisation" / "showboat" / "private_benchmark.py"


class PrivateBenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.source = Path(self.temp.name) / "confidential-source"
        self.source.mkdir()
        for name, character in [("z_video_one.md", "z"), ("a_video_two.md", "a"), ("m_video_three.md", "m")]:
            (self.source / name).write_text(("00:12:30\\n" + character * 45_000), encoding="utf-8")
        self.private = ROOT / ".tmp" / "private-benchmark-test"
        shutil.rmtree(self.private, ignore_errors=True)
        self.config = Path(self.temp.name) / "config.json"
        self.config.write_text(json.dumps({"course_root": str(self.source), "model_dir": "scratch/gemma4.gturbo", "results_root": str(self.private), "summary_prompt": "fixture prompt", "timeout_seconds": 60}), encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.private, ignore_errors=True)
        self.temp.cleanup()

    def invoke(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(RUNNER), "--config", str(self.config), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30)

    def test_prepare_and_report_hide_source_path_and_exact_sizes(self) -> None:
        prepared = self.invoke("prepare")
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        self.assertNotIn(str(self.source), prepared.stdout)
        self.assertIn("prepared chunks=12 videos=3", prepared.stdout)
        self.assertTrue((self.private / "corpus" / "benchmark00.md").is_file())
        table = json.loads((self.private / "public-video-table.json").read_text())
        self.assertEqual([row["video"] for row in table], ["Video A", "Video B", "Video C"])
        self.assertTrue(all(row["duration_minutes"] == 12 for row in table))
        self.assertTrue(all(abs(row["reported_kib"] - 44) <= 2 for row in table))
        record = {"backend": "fixture", "chunk": 0, "context": 4096, "wall_seconds": 1.234, "peak_rss_mib": 99.0, "exit_code": 0}
        output = self.private / "measured" / "fixture" / "context-4096" / "chunk-00"
        output.mkdir(parents=True)
        (output / "measurement.json").write_text(json.dumps(record), encoding="utf-8")
        report = Path(self.temp.name) / "public.md"
        published = self.invoke("public-report", "--output", str(report))
        self.assertEqual(published.returncode, 0, published.stderr)
        text = report.read_text(encoding="utf-8")
        self.assertNotIn(str(self.source), text)
        self.assertNotIn("a_video_two", text)
        self.assertIn("Video A", text)
        self.assertIn("| fixture | 00 |", text)

    def test_refuses_results_outside_tmp(self) -> None:
        outside = Path(self.temp.name) / "not-private"
        config = json.loads(self.config.read_text())
        config["results_root"] = str(outside)
        self.config.write_text(json.dumps(config), encoding="utf-8")
        result = self.invoke("prepare")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
