from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "summarisation" / "showboat" / "private_benchmark.py"


class PrivateFilesystemErrorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.results = ROOT / ".tmp" / "private-filesystem-error-test"
        shutil.rmtree(self.results, ignore_errors=True)
        self.config = Path(self.temp.name) / "private-config.json"
        self.secret_source = Path(self.temp.name) / "secret-course-name"
        self.config.write_text(
            json.dumps(
                {
                    "course_root": str(self.secret_source),
                    "model_dir": "scratch/gemma4.gturbo",
                    "results_root": str(self.results),
                    "summary_prompt": "secret fixture prompt",
                    "timeout_seconds": 60,
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.results, ignore_errors=True)
        self.temp.cleanup()

    def test_missing_private_file_is_redacted_and_diagnosed_privately(self) -> None:
        public_output = Path(self.temp.name) / "public.md"
        result = subprocess.run(
            [str(RUNNER), "--config", str(self.config), "public-report", "--output", str(public_output)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "error: private filesystem operation failed; inspect private diagnostics\n")
        self.assertNotIn("Traceback", result.stderr)
        self.assertNotIn(str(self.results), result.stderr)
        self.assertNotIn(str(self.secret_source), result.stderr)
        self.assertNotIn("secret fixture prompt", result.stderr)
        self.assertFalse(public_output.exists())

        diagnostic = self.results / "private-errors.jsonl"
        self.assertTrue(diagnostic.is_file())
        record = json.loads(diagnostic.read_text(encoding="utf-8"))
        self.assertEqual(record["error_type"], "FileNotFoundError")
        self.assertIn(str(self.results), record["detail"])
        self.assertIn("public-video-table.json", record["detail"])


if __name__ == "__main__":
    unittest.main()
