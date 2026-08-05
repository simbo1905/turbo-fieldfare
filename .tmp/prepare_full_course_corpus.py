#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Prepare all Markdown course material as deterministic 11K/10K chunks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CHUNK_SIZE = 11_000
CHUNK_STEP = 10_000


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("course_root", type=Path)
    parser.add_argument("output_root", type=Path)
    args = parser.parse_args(argv)

    course = args.course_root.resolve()
    output = args.output_root.resolve()
    if not course.is_dir():
        parser.error("course root must be a directory")
    try:
        output.relative_to(course)
    except ValueError:
        pass
    else:
        parser.error("output root must not be inside the course root")
    if output.exists():
        parser.error("output root already exists")

    sources = sorted(path for path in course.rglob("*.md") if path.is_file())
    if not sources:
        parser.error("course contains no Markdown files")
    source_bytes = [path.read_bytes() for path in sources]
    try:
        combined = "\n\n".join(value.decode("utf-8") for value in source_bytes)
    except UnicodeDecodeError as error:
        parser.error(f"course Markdown is not UTF-8: {error}")
    chunks = [
        combined[offset : offset + CHUNK_SIZE]
        for offset in range(0, len(combined) - CHUNK_SIZE + 1, CHUNK_STEP)
    ]
    if not chunks:
        parser.error("course does not contain one complete chunk")

    output.mkdir(parents=True)
    rows = []
    for index, text in enumerate(chunks):
        encoded = text.encode("utf-8")
        name = f"chunk{index:02d}.md"
        (output / name).write_bytes(encoded)
        rows.append({
            "index": index,
            "path": name,
            "offset_chars": index * CHUNK_STEP,
            "bytes": len(encoded),
            "sha256": sha256(encoded),
        })
    manifest = {
        "format": "full-course-corpus-v1",
        "chunk_size_chars": CHUNK_SIZE,
        "chunk_step_chars": CHUNK_STEP,
        "source_count": len(sources),
        "source_bytes": sum(len(value) for value in source_bytes),
        "sources": [
            {
                "path": str(path.relative_to(course)),
                "bytes": len(value),
                "sha256": sha256(value),
            }
            for path, value in zip(sources, source_bytes)
        ],
        "chunks": rows,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"prepared sources={len(sources)} chunks={len(chunks)} bytes={sum(len(value) for value in source_bytes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
