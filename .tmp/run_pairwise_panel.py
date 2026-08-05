#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run a deterministic AB/BA three-judge panel for eligible prepared chunks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


def selected_indices(eligible: list[int], count: int) -> list[int]:
    if len(eligible) < count:
        raise ValueError("not enough eligible chunks for panel")
    return [eligible[index * (len(eligible) - 1) // (count - 1)] for index in range(count)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--eligibility", required=True, type=Path)
    parser.add_argument("--ollama", required=True, type=Path)
    parser.add_argument("--tf-primary", required=True, type=Path)
    parser.add_argument("--tf-late", required=True, type=Path)
    parser.add_argument("--pairwise", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--count", type=int, default=12)
    args = parser.parse_args(argv)

    if args.output.exists():
        parser.error("output already exists")
    eligibility = json.loads(args.eligibility.read_text(encoding="utf-8"))
    eligible = [int(name[5:7]) for name in eligibility["eligible"]]
    selected = selected_indices(eligible, args.count)
    args.output.mkdir(parents=True)
    manifest = {"eligible_indices": eligible, "selected_indices": selected, "orders": []}
    for index in selected:
        source = args.corpus / f"chunk{index:02d}.md"
        ollama = args.ollama / f"chunk{index:02d}" / "response.md"
        tf_root = args.tf_primary if index < 48 else args.tf_late
        turbofieldfare = tf_root / f"chunk{index:02d}" / "response.md"
        for order, first, second in [
            ("AB", turbofieldfare, ollama),
            ("BA", ollama, turbofieldfare),
        ]:
            result = args.output / f"chunk{index:02d}-{order}.json"
            raw_log = args.output / f"chunk{index:02d}-{order}.jsonl"
            completed = subprocess.run(
                [
                    "uv", "run", "--script", str(args.pairwise),
                    "--source", str(source), "--summary-a", str(first), "--summary-b", str(second),
                    "--output", str(result), "--private-log", str(raw_log),
                ],
                check=False,
            )
            manifest["orders"].append({"chunk": index, "order": order, "exit_code": completed.returncode})
            if completed.returncode != 0:
                (args.output / "manifest.json").write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
                return completed.returncode
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"panel chunks={len(selected)} calls={len(manifest['orders']) * 3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
