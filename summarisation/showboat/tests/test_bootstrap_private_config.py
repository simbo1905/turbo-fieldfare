from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "summarisation" / "showboat" / "bootstrap_private_config.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("bootstrap_private_config", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    def test_spotlight_fallback_groups_real_files_by_parent(self) -> None:
        module = load_tool()
        unrelated = Path(self.temp.name) / "unrelated"
        unrelated.mkdir()
        spotlight_output = "\n".join(
            [str(path) for path in self.course.glob("*_video_*.md")]
            + [str(self.course / "missing_video_file.md"), str(unrelated / "not-a-video.md")]
        )
        with mock.patch.object(
            module.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0, spotlight_output, ""),
        ) as run:
            matches = module.spotlight_candidates()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], self.course.resolve())
        self.assertEqual(len(matches[0][1]), 3)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], ["mdfind", "kMDItemFSName == '*video*.md'cd"])
        self.assertEqual(run.call_args.kwargs["timeout"], module.SPOTLIGHT_TIMEOUT_SECONDS)

    def test_explicit_environment_root_never_uses_spotlight(self) -> None:
        module = load_tool()
        missing = Path(self.temp.name) / "missing"
        with mock.patch.dict(module.os.environ, {"SUMMARISATION_COURSE_ROOT": str(missing)}), mock.patch.object(
            module, "spotlight_candidates", side_effect=AssertionError("must not run")
        ):
            self.assertEqual(module.candidates([]), [])

    def test_spotlight_selects_leaf_most_eligible_nested_ancestor(self) -> None:
        module = load_tool()
        nested_course = Path(self.temp.name) / "catalog" / "course"
        paths = []
        for index, lesson in enumerate(("lesson-a", "lesson-b", "lesson-c")):
            directory = nested_course / lesson
            directory.mkdir(parents=True)
            path = directory / f"unit_{index}_video_fixture.md"
            path.write_text("z" * 45_000, encoding="utf-8")
            paths.append(path)
        with mock.patch.object(
            module.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0, "\n".join(map(str, paths)), ""),
        ):
            matches = module.spotlight_candidates()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], nested_course.resolve())
        self.assertEqual(matches[0][1], sorted(path.resolve() for path in paths))

    def test_unique_lse_token_disambiguates_candidates(self) -> None:
        module = load_tool()
        candidates = [
            (Path("/Users/example/LSE-course"), [], 12),
            (Path("/Users/example/another-course"), [], 12),
        ]
        self.assertEqual(module.disambiguate_lse(candidates), [candidates[0]])

    def test_missing_lse_token_preserves_ambiguity(self) -> None:
        module = load_tool()
        candidates = [
            (Path("/Users/example/falsecourse"), [], 12),
            (Path("/Users/example/another-course"), [], 12),
        ]
        self.assertEqual(module.disambiguate_lse(candidates), candidates)

    def test_multiple_lse_tokens_preserve_ambiguity(self) -> None:
        module = load_tool()
        candidates = [
            (Path("/Users/example/lse_course"), [], 12),
            (Path("/Users/example/catalog/LSE/course"), [], 12),
        ]
        self.assertEqual(module.disambiguate_lse(candidates), candidates)

    def test_coalesces_sections_under_specific_lse_course(self) -> None:
        module = load_tool()
        scan_root = Path(self.temp.name) / "catalog"
        common = scan_root / "LSE-course"
        paths = [common / "section-a" / "a_video_1.md", common / "section-b" / "b_video_2.md"]
        for path in paths:
            path.parent.mkdir(parents=True)
            path.write_text("x" * 70_000, encoding="utf-8")
        candidates = [(path.parent, [path], 12) for path in paths]
        result = module.coalesce_candidates(candidates, set(paths), [scan_root])
        self.assertEqual(result, [(common.resolve(), sorted(path.resolve() for path in paths), 13)])

    def test_refuses_coalescing_at_broad_scan_root(self) -> None:
        module = load_tool()
        scan_root = Path(self.temp.name) / "LSE-catalog"
        paths = [scan_root / "a" / "a_video_1.md", scan_root / "b" / "b_video_2.md"]
        candidates = [(path.parent, [path], 12) for path in paths]
        self.assertEqual(module.coalesce_candidates(candidates, set(paths), [scan_root]), candidates)

    def test_refuses_coalescing_with_unrelated_matching_file(self) -> None:
        module = load_tool()
        scan_root = Path(self.temp.name) / "catalog"
        common = scan_root / "LSE-course"
        paths = [common / "a" / "a_video_1.md", common / "b" / "b_video_2.md"]
        unrelated = common / "other" / "other_video_3.md"
        candidates = [(path.parent, [path], 12) for path in paths]
        self.assertEqual(
            module.coalesce_candidates(candidates, set(paths + [unrelated]), [scan_root]),
            candidates,
        )


if __name__ == "__main__":
    unittest.main()
