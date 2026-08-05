from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "summarisation" / "showboat" / "private_benchmark.py"
SPEC = importlib.util.spec_from_file_location("private_benchmark_preflight", RUNNER)
assert SPEC and SPEC.loader
BENCHMARK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCHMARK)


class FullPreflightPerInvocationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.course = self.base / "course"
        self.course.mkdir()
        (self.course / "fixture_video_01.md").write_text("fixture", encoding="utf-8")
        self.model = self.base / "model"
        self.model.mkdir()
        (self.model / "manifest.json").write_text("{}\n", encoding="utf-8")
        self.root = self.base / "results"
        corpus = self.root / "corpus"
        corpus.mkdir(parents=True)
        (corpus / "manifest.json").write_text(
            json.dumps({"chunks": [{"filename": "benchmark00.md"}]}), encoding="utf-8"
        )
        (corpus / "benchmark00.md").write_text("fixture", encoding="utf-8")
        self.config = {
            "course_root": str(self.course),
            "model_dir": str(self.model),
            "results_root": str(self.root),
            "summary_prompt": "summarize",
            "timeout_seconds": 10,
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def passing_gate(self):
        return mock.patch.multiple(
            BENCHMARK,
            macos_supported=mock.Mock(return_value=True),
            swift_supported=mock.Mock(return_value=True),
            disk_supported=mock.Mock(return_value=True),
            free_memory=mock.Mock(return_value=50),
            model_complete=mock.Mock(return_value=True),
            release_cli_available=mock.Mock(return_value=True),
            ollama_model_available=mock.Mock(return_value=True),
            model_owner_present=mock.Mock(return_value=False),
            ollama_loaded=mock.Mock(return_value=False),
        )

    def test_every_warmup_and_measure_runs_full_gate_before_launch(self) -> None:
        for warmup in (True, False):
            for backend in ("turbofieldfare", "ollama"):
                with self.subTest(warmup=warmup, backend=backend), self.passing_gate(), \
                     mock.patch.object(BENCHMARK, "full_preflight") as gate, \
                     mock.patch.object(BENCHMARK, "launch", return_value=(0, 1.0, 2.0)) as launch:
                    events = []
                    gate.side_effect = lambda *_args: events.append("gate") or 50
                    output = self.root / ("warmup" if warmup else "measured") / backend / "context-4096" / "chunk-00" / "summary.md"

                    def successful_launch(*_args, **_kwargs):
                        events.append("launch")
                        output.write_text("summary", encoding="utf-8")
                        return 0, 1.0, 2.0

                    launch.side_effect = successful_launch
                    BENCHMARK.run_one(self.config, self.root, backend, 0, 4096, warmup)
                    gate.assert_called_once_with(self.config, self.root)
                    launch.assert_called_once()
                    self.assertEqual(events, ["gate", "launch"])

    def test_each_required_gate_failure_prevents_launch(self) -> None:
        failures = {
            "macos_supported": False,
            "swift_supported": False,
            "disk_supported": False,
            "free_memory": 19,
            "model_complete": False,
            "release_cli_available": False,
            "ollama_model_available": False,
            "model_owner_present": True,
            "ollama_loaded": True,
        }
        for helper, failure in failures.items():
            with self.subTest(helper=helper), self.passing_gate(), \
                 mock.patch.object(BENCHMARK, helper, return_value=failure), \
                 mock.patch.object(BENCHMARK, "launch") as launch:
                with self.assertRaisesRegex(RuntimeError, "preflight checks failed"):
                    BENCHMARK.run_one(self.config, self.root, "turbofieldfare", 0, 4096, False)
                launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
