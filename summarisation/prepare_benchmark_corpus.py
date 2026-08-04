#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Prepare an immutable, local benchmark corpus from an external course tree."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

TOOL_VERSION = "1"
CHUNK_SIZE = 11_000
CHUNK_STEP = 10_000
BENCHMARK_COUNT = 12


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def select_evenly(count: int) -> list[int]:
    if count < BENCHMARK_COUNT:
        raise ValueError("the course corpus must produce at least 12 chunks")
    # Integer arithmetic makes selection stable across Python versions.
    return [number * (count - 1) // (BENCHMARK_COUNT - 1) for number in range(BENCHMARK_COUNT)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("course_root", type=Path)
    parser.add_argument("output_root", type=Path)
    args = parser.parse_args(argv)
    course = args.course_root.resolve()
    output = args.output_root.resolve()
    if not course.is_dir():
        parser.error("course root must be an existing directory")
    if is_within(output, course):
        parser.error("output root must not be the course root or beneath the course tree")

    sources = sorted(path for path in course.rglob("*_video_*.md") if path.is_file())
    if not sources:
        parser.error("course contains no *_video_*.md transcripts")
    source_bytes = [path.read_bytes() for path in sources]
    try:
        source_text = [item.decode("utf-8") for item in source_bytes]
    except UnicodeDecodeError as error:
        parser.error("course transcript is not UTF-8: %s" % error)
    combined = "\n\n".join(source_text)
    all_chunks = [combined[offset : offset + CHUNK_SIZE] for offset in range(0, len(combined) - CHUNK_SIZE + 1, CHUNK_STEP)]
    try:
        selected = select_evenly(len(all_chunks))
    except ValueError as error:
        parser.error(str(error))

    # Validate every condition before creating any output directory.
    output.mkdir(parents=True, exist_ok=True)
    chunks = []
    for benchmark_number, source_index in enumerate(selected):
        name = "benchmark%02d.md" % benchmark_number
        text = all_chunks[source_index]
        encoded = text.encode("utf-8")
        (output / name).write_bytes(encoded)
        chunks.append({
            "path": name,
            "source_chunk_index": source_index,
            "offset_chars": source_index * CHUNK_STEP,
            "sha256": digest_bytes(encoded),
            "bytes": len(encoded),
        })
    manifest = {
        "format": "turbofieldfare-summarisation-benchmark-v1",
        "tool_version": TOOL_VERSION,
        "chunk_size_chars": CHUNK_SIZE,
        "chunk_step_chars": CHUNK_STEP,
        "sources": [
            {"path": str(path.relative_to(course)), "sha256": digest_bytes(data), "bytes": len(data)}
            for path, data in zip(sources, source_bytes)
        ],
        "selected_indices": selected,
        "chunks": chunks,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(1)
