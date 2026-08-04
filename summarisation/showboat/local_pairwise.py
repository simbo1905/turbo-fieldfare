#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Prepare and score local-only blinded pairs without publishing text."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import secrets
import sys


def private_path(path: Path) -> Path:
    resolved = path.resolve()
    root = (Path(__file__).resolve().parents[2] / ".tmp").resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("all blind-pair artifacts must stay inside .tmp") from error
    return resolved


def prepare(args: argparse.Namespace) -> int:
    output = private_path(args.output)
    if output.exists():
        raise ValueError("blind-pair output already exists")
    candidate_a = private_path(args.candidate_a)
    candidate_b = private_path(args.candidate_b)
    pairs = []
    for index in args.chunks:
        filename = f"chunk-{index:02d}.json"
        a = (candidate_a / f"chunk-{index:02d}" / "summary.md").read_text(encoding="utf-8")
        b = (candidate_b / f"chunk-{index:02d}" / "summary.md").read_text(encoding="utf-8")
        if secrets.randbits(1):
            left, right, answer = a, b, "A"
        else:
            left, right, answer = b, a, "B"
        pairs.append({"pair": index, "left": left, "right": right, "answer": answer})
        output.mkdir(parents=True, exist_ok=False) if not output.exists() else None
        (output / filename).write_text(json.dumps(pairs[-1]), encoding="utf-8")
    (output / "instructions.md").write_text("For each pair, choose LEFT, RIGHT, or TIE for faithfulness and usefulness. Record only the choice in ratings.json. Do not copy text outside this private directory.\n", encoding="utf-8")
    print(f"blind pairs prepared={len(pairs)}")
    return 0


def score(args: argparse.Namespace) -> int:
    pairs = private_path(args.pairs)
    ratings = json.loads(private_path(args.ratings).read_text(encoding="utf-8"))
    if not isinstance(ratings, dict):
        raise ValueError("ratings must be an object mapping pair numbers to LEFT, RIGHT, or TIE")
    aggregate = {"baseline_wins": 0, "candidate_wins": 0, "ties": 0, "invalid": 0}
    for path in sorted(pairs.glob("chunk-*.json")):
        pair = json.loads(path.read_text(encoding="utf-8"))
        rating = ratings.get(str(pair["pair"]), "")
        if rating == "TIE":
            aggregate["ties"] += 1
        elif rating in {"LEFT", "RIGHT"}:
            winner = pair["answer"] if rating == "LEFT" else ("B" if pair["answer"] == "A" else "A")
            aggregate["candidate_wins" if winner == "A" else "baseline_wins"] += 1
        else:
            aggregate["invalid"] += 1
    output = private_path(args.output)
    output.write_text(json.dumps(aggregate, indent=2) + "\n", encoding="utf-8")
    print("pairwise score baseline_wins={baseline_wins} candidate_wins={candidate_wins} ties={ties} invalid={invalid}".format(**aggregate))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--candidate-a", type=Path, required=True)
    prep.add_argument("--candidate-b", type=Path, required=True)
    prep.add_argument("--output", type=Path, required=True)
    prep.add_argument("--chunks", type=int, nargs="+", required=True)
    scored = sub.add_parser("score")
    scored.add_argument("--pairs", type=Path, required=True)
    scored.add_argument("--ratings", type=Path, required=True)
    scored.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    return prepare(args) if args.action == "prepare" else score(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
