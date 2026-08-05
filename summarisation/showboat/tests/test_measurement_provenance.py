from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "summarisation" / "showboat" / "private_benchmark.py"
SPEC = importlib.util.spec_from_file_location("private_benchmark_provenance", MODULE_PATH)
assert SPEC and SPEC.loader
BENCHMARK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCHMARK)


class MeasurementProvenanceTests(unittest.TestCase):
    def test_private_record_is_complete_and_public_report_is_sanitized(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as temporary:
            private = Path(temporary)
            corpus = private / "corpus"
            corpus.mkdir()
            (corpus / "benchmark00.md").write_text("private transcript", encoding="utf-8")
            (corpus / "manifest.json").write_text(
                json.dumps({"chunks": [{"name": "benchmark00.md"}]}), encoding="utf-8"
            )
            (private / "public-video-table.json").write_text("[]", encoding="utf-8")
            secret_model = str(private / "secret-model-name")
            secret_prompt = "private subject summary instruction"
            config = {
                "course_root": str(private / "secret-course"),
                "model_dir": secret_model,
                "results_root": str(private),
                "summary_prompt": secret_prompt,
                "timeout_seconds": 60,
            }
            captured_command: list[str] = []

            def fake_launch(command, stdout, stderr, timeout_seconds, sample_ollama):
                captured_command.extend(command)
                Path(command[command.index("--output") + 1]).write_text("private summary", encoding="utf-8")
                stdout.write_text("complete timing footer\n", encoding="utf-8")
                stderr.write_text("", encoding="utf-8")
                return 0, 1.25, 321.0

            private_provenance = {
                "commit": "deadbeef",
                "hardware": "Secret Mac Model",
                "ram_bytes": 123456,
                "macos_version": "26.5",
                "swift_version": "Swift version 6.2.1",
                "captured_at": "2026-08-05T12:00:00Z",
            }
            with (
                mock.patch.object(BENCHMARK, "full_preflight", return_value=55),
                mock.patch.object(BENCHMARK, "free_memory", return_value=50),
                mock.patch.object(BENCHMARK, "launch", side_effect=fake_launch),
                mock.patch.object(BENCHMARK, "capture_host_provenance", return_value=private_provenance),
            ):
                BENCHMARK.run_one(config, private, "turbofieldfare", 0, 4096, False)

            measurement_path = private / "measured/turbofieldfare/context-4096/chunk-00/measurement.json"
            record = json.loads(measurement_path.read_text(encoding="utf-8"))
            self.assertEqual(record["provenance"], private_provenance)
            self.assertEqual(record["argv"], captured_command)
            self.assertEqual(record["started_at"], "2026-08-05T12:00:00Z")
            self.assertIn("finished_at", record)
            self.assertEqual(record["exit_code"], 0)
            self.assertEqual(record["stdout_path"], str(measurement_path.parent / "stdout.bin"))
            self.assertEqual(record["stderr_path"], str(measurement_path.parent / "stderr.bin"))
            self.assertEqual(record["timing_footer_or_error"], "complete timing footer\n")
            self.assertEqual(record["backend_configuration"]["temperature"], 1.0)
            self.assertTrue(record["protocol_deviations"])

            report = private / "public.md"
            BENCHMARK.report(private, report)
            public = report.read_text(encoding="utf-8")
            for secret in (str(private), secret_model, secret_prompt, "Secret Mac Model"):
                self.assertNotIn(secret, public)
            self.assertIn("Protocol deviations", public)
            self.assertIn("real-user-path", public)
            self.assertIn("Commit `deadbeef`", public)
            self.assertIn("macOS 26.5", public)

    def test_launch_error_is_preserved_in_private_measurement(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as temporary:
            private = Path(temporary)
            corpus = private / "corpus"
            corpus.mkdir()
            (corpus / "benchmark00.md").write_text("private transcript", encoding="utf-8")
            (corpus / "manifest.json").write_text(json.dumps({"chunks": [{}]}), encoding="utf-8")
            config = {
                "course_root": str(private / "course"),
                "model_dir": str(private / "model"),
                "results_root": str(private),
                "summary_prompt": "private prompt",
                "timeout_seconds": 1,
            }
            provenance = {
                "captured_at": "2026-08-05T12:00:00Z",
                "commit": "deadbeef",
                "hardware": "private hardware",
                "architecture": "arm64",
                "ram_bytes": 16 * 1024**3,
                "macos_version": "26.5",
                "swift_version": "Swift version 6.2.1",
            }
            with (
                mock.patch.object(BENCHMARK, "full_preflight", return_value=55),
                mock.patch.object(BENCHMARK, "free_memory", return_value=50),
                mock.patch.object(BENCHMARK, "launch", side_effect=RuntimeError("command timed out")),
                mock.patch.object(BENCHMARK, "capture_host_provenance", return_value=provenance),
            ):
                with self.assertRaisesRegex(RuntimeError, "command timed out"):
                    BENCHMARK.run_one(config, private, "ollama", 0, 4096, False)
            record = json.loads(
                (private / "measured/ollama/context-4096/chunk-00/measurement.json").read_text()
            )
            self.assertIsNone(record["exit_code"])
            self.assertEqual(record["runner_error"], "command timed out")
            self.assertEqual(record["timing_footer_or_error"], "command timed out")


if __name__ == "__main__":
    unittest.main()
