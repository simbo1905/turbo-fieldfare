#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Discover one eligible local transcript corpus without printing its path."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCAN_ROOTS = [Path("/Users/Shared"), Path("/Users/consensussolutions/Documents")]
CHUNK_SIZE = 11_000
CHUNK_STEP = 10_000


def estimated_chunks(paths: list[Path]) -> int:
    total = sum(path.stat().st_size for path in paths) + max(0, len(paths) - 1) * 2
    return 0 if total < CHUNK_SIZE else 1 + (total - CHUNK_SIZE) // CHUNK_STEP


def files_under(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*_video_*.md") if path.is_file())


def candidates(scan_roots: list[Path]) -> list[tuple[Path, list[Path], int]]:
    found: list[tuple[Path, list[Path], int]] = []
    explicit = os.environ.get("SUMMARISATION_COURSE_ROOT")
    roots = [Path(explicit)] if explicit else scan_roots
    for root in roots:
        if not root.is_dir():
            continue
        children = [root] if explicit else [path for path in root.iterdir() if path.is_dir() and not path.name.startswith(".")]
        for child in children:
            paths = files_under(child)
            chunks = estimated_chunks(paths)
            if len(paths) >= 3 and chunks >= 12:
                found.append((child, paths, chunks))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-root", action="append", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / ".tmp" / "showboat-private-config.json")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    try:
        output.relative_to((ROOT / ".tmp").resolve())
    except ValueError:
        parser.error("output must be inside this checkout's .tmp")
    matches = candidates(args.scan_root or DEFAULT_SCAN_ROOTS)
    if len(matches) != 1:
        print(f"bootstrap unresolved eligible_candidates={len(matches)}", file=sys.stderr)
        return 2
    course, paths, chunks = matches[0]
    if output.exists():
        print("bootstrap refused existing_config", file=sys.stderr)
        return 2
    config = {
        "course_root": str(course.resolve()),
        "model_dir": "scratch/gemma4.gturbo",
        "results_root": ".tmp/confidential-gemma4-comparison",
        "summary_prompt": "Summarise the following instructional transcript faithfully and concisely. Preserve substantive facts, figures, and recommendations.",
        "timeout_seconds": 1800,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"bootstrap ok videos={len(paths)} estimated_chunks={chunks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
