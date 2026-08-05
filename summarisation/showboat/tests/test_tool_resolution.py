#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tool-path resolution tests for checkout and flat-Gist layouts."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPOSITORY_ROOT / "summarisation" / "showboat" / "private_benchmark.py"
TOOL_NAMES = (
    "prepare_benchmark_corpus.py",
    "process_chunks_turbofieldfare.py",
    "process_chunks_ollama.py",
)


def load_runner(path: Path):
    spec = importlib.util.spec_from_file_location(f"private_benchmark_{path.parent.name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ToolResolutionTests(unittest.TestCase):
    def test_checkout_layout_resolves_repository_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            runner = root / "summarisation" / "showboat" / "private_benchmark.py"
            runner.parent.mkdir(parents=True)
            shutil.copyfile(RUNNER, runner)
            for name in TOOL_NAMES:
                (root / "summarisation" / name).touch()

            module = load_runner(runner)

            self.assertEqual(root / "summarisation" / TOOL_NAMES[0], module.PREPARE)
            self.assertEqual(root / "summarisation" / TOOL_NAMES[1], module.TF)
            self.assertEqual(root / "summarisation" / TOOL_NAMES[2], module.OLLAMA)
            self.assertEqual(root / ".tmp" / "showboat-private-config.json", module.DEFAULT_CONFIG)

    def test_flat_gist_layout_resolves_direct_sibling_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            runner = root / "private_benchmark.py"
            shutil.copyfile(RUNNER, runner)
            for name in TOOL_NAMES:
                (root / name).touch()

            module = load_runner(runner)

            self.assertEqual(root / TOOL_NAMES[0], module.PREPARE)
            self.assertEqual(root / TOOL_NAMES[1], module.TF)
            self.assertEqual(root / TOOL_NAMES[2], module.OLLAMA)
            self.assertEqual(root / ".tmp" / "showboat-private-config.json", module.DEFAULT_CONFIG)


if __name__ == "__main__":
    unittest.main()
