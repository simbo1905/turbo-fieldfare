from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "summarisation" / "showboat" / "local_pairwise.py"
PRIVATE = ROOT / ".tmp" / "pairwise-test"


class LocalPairwiseTests(unittest.TestCase):
    def setUp(self) -> None:
        shutil.rmtree(PRIVATE, ignore_errors=True)
        for candidate, text in [("candidate", "candidate"), ("baseline", "baseline")]:
            for index in (0, 1):
                output = PRIVATE / candidate / f"chunk-{index:02d}"
                output.mkdir(parents=True, exist_ok=True)
                (output / "summary.md").write_text(text, encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(PRIVATE, ignore_errors=True)

    def invoke(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(TOOL), *map(str, args)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30)

    def test_private_blind_pairs_and_aggregate_have_no_summary_text_on_stdout(self) -> None:
        pairs = PRIVATE / "pairs"
        prepared = self.invoke("prepare", "--candidate-a", PRIVATE / "candidate", "--candidate-b", PRIVATE / "baseline", "--output", pairs, "--chunks", 0, 1)
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        self.assertEqual(prepared.stdout.strip(), "blind pairs prepared=2")
        self.assertNotIn("candidate", prepared.stdout)
        content = json.loads((pairs / "chunk-00.json").read_text())
        rating = "LEFT" if content["answer"] == "A" else "RIGHT"
        ratings = PRIVATE / "ratings.json"
        ratings.write_text(json.dumps({"0": rating, "1": "TIE"}), encoding="utf-8")
        output = PRIVATE / "score.json"
        scored = self.invoke("score", "--pairs", pairs, "--ratings", ratings, "--output", output)
        self.assertEqual(scored.returncode, 0, scored.stderr)
        summary = json.loads(output.read_text())
        self.assertEqual(summary["candidate_wins"], 1)
        self.assertEqual(summary["ties"], 1)

    def test_rejects_non_private_artifacts(self) -> None:
        result = self.invoke("prepare", "--candidate-a", "/tmp", "--candidate-b", "/tmp", "--output", PRIVATE / "pairs", "--chunks", 0)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
