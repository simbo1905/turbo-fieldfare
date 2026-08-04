from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "summarisation" / "showboat" / "bootstrap_private_config.py"


class BootstrapPrivateConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "scan"
        self.course = self.root / "candidate"
        self.course.mkdir(parents=True)
        for index in range(3):
            (self.course / f"video_{index}_video_fixture.md").write_text("x" * 45_000, encoding="utf-8")
        self.output = ROOT / ".tmp" / "bootstrap-private-config-test.json"
        self.output.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.output.unlink(missing_ok=True)
        self.temp.cleanup()

    def test_writes_ignored_config_without_printing_course_path(self) -> None:
        result = subprocess.run([sys.executable, str(TOOL), "--scan-root", str(self.root), "--output", str(self.output)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("bootstrap ok videos=3 estimated_chunks=13", result.stdout)
        self.assertNotIn(str(self.course), result.stdout)
        config = json.loads(self.output.read_text())
        self.assertEqual(Path(config["course_root"]), self.course.resolve())

    def test_refuses_ambiguous_matches_without_printing_paths(self) -> None:
        duplicate = self.root / "other"
        duplicate.mkdir()
        for index in range(3):
            (duplicate / f"video_{index}_video_fixture.md").write_text("y" * 45_000, encoding="utf-8")
        result = subprocess.run([sys.executable, str(TOOL), "--scan-root", str(self.root), "--output", str(self.output)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr.strip(), "bootstrap unresolved eligible_candidates=2")


if __name__ == "__main__":
    unittest.main()
