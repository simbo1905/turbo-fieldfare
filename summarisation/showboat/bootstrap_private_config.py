#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Discover one eligible local transcript corpus without printing its path."""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import os.path
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCAN_ROOTS = [Path("/Users/Shared"), Path("/Users/consensussolutions/Documents")]
CHUNK_SIZE = 11_000
CHUNK_STEP = 10_000
SPOTLIGHT_TIMEOUT_SECONDS = 30
MAX_SPOTLIGHT_FILES = 10_000
MAX_ANCESTORS_PER_FILE = 24
MIN_SAFE_ANCESTOR_PARTS = 4
LSE_TOKEN = re.compile(r"(?:^|[^a-z0-9])lse(?:$|[^a-z0-9])", re.IGNORECASE)
FORBIDDEN_COALESCE_NAMES = {"users", "documents", "shared", "library", "cloudstorage"}


def estimated_chunks(paths: list[Path]) -> int:
    total = sum(path.stat().st_size for path in paths) + max(0, len(paths) - 1) * 2
    return 0 if total < CHUNK_SIZE else 1 + (total - CHUNK_SIZE) // CHUNK_STEP


def files_under(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*_video_*.md") if path.is_file())


def coalesce_candidates(
    matches: list[tuple[Path, list[Path], int]],
    all_paths: set[Path],
    scan_roots: list[Path],
) -> list[tuple[Path, list[Path], int]]:
    if len(matches) <= 1:
        return matches
    common = Path(os.path.commonpath([str(match[0].resolve()) for match in matches]))
    if common == Path("/") or common.name.casefold() in FORBIDDEN_COALESCE_NAMES:
        return matches
    boundaries = [root.resolve() for root in scan_roots]
    if len(common.parts) >= 3 and common.parts[1].casefold() == "users":
        boundaries.append(Path(*common.parts[:3]))
    if not any(common != boundary and common.is_relative_to(boundary) for boundary in boundaries):
        return matches
    if not any(LSE_TOKEN.search(component) for component in common.parts):
        return matches
    union = {path.resolve() for _, paths, _ in matches for path in paths}
    contained = {path.resolve() for path in all_paths if path.resolve().is_relative_to(common)}
    if contained != union:
        return matches
    try:
        chunks = estimated_chunks(sorted(union))
    except OSError:
        return matches
    return [(common, sorted(union), chunks)]


def spotlight_candidates() -> list[tuple[Path, list[Path], int]]:
    """Find eligible parent directories without exposing discovered paths."""
    try:
        result = subprocess.run(
            ["mdfind", "kMDItemFSName == '*video*.md'cd"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=SPOTLIGHT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []

    real_paths: set[Path] = set()
    for raw_path in result.stdout.splitlines()[:MAX_SPOTLIGHT_FILES]:
        path = Path(raw_path)
        if not fnmatch.fnmatchcase(path.name, "*_video_*.md") or not path.is_file():
            continue
        try:
            real_path = path.resolve(strict=True)
        except OSError:
            continue
        real_paths.add(real_path)

    grouped: dict[Path, set[Path]] = {}
    for real_path in sorted(real_paths):
        ancestor = real_path.parent
        for _ in range(MAX_ANCESTORS_PER_FILE):
            if len(ancestor.parts) < MIN_SAFE_ANCESTOR_PARTS:
                break
            grouped.setdefault(ancestor, set()).add(real_path)
            if ancestor.parent == ancestor:
                break
            ancestor = ancestor.parent

    eligible: list[tuple[Path, list[Path], int]] = []
    for parent, unique_paths in grouped.items():
        paths = sorted(unique_paths)
        if len(paths) < 3:
            continue
        try:
            chunks = estimated_chunks(paths)
        except OSError:
            continue
        if chunks >= 12:
            eligible.append((parent, paths, chunks))

    leaf_most = [
        match
        for match in eligible
        if not any(
            other[0] != match[0] and other[0].is_relative_to(match[0])
            for other in eligible
        )
    ]
    leaf_most = sorted(leaf_most, key=lambda match: str(match[0]))
    return coalesce_candidates(leaf_most, real_paths, DEFAULT_SCAN_ROOTS)


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
    if found or explicit:
        return found
    return spotlight_candidates()


def disambiguate_lse(
    matches: list[tuple[Path, list[Path], int]],
) -> list[tuple[Path, list[Path], int]]:
    if len(matches) <= 1:
        return matches
    lse_matches = [
        match for match in matches if any(LSE_TOKEN.search(component) for component in match[0].parts)
    ]
    return lse_matches if len(lse_matches) == 1 else matches


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
    matches = disambiguate_lse(candidates(args.scan_root or DEFAULT_SCAN_ROOTS))
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
