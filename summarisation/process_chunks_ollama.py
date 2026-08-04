#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Opt-in Ollama chunk processor using Ollama's native default settings."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import urllib.request


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--model", default="gemma4:26b")
    args = parser.parse_args(argv)
    if args.input.is_dir():
        inputs = sorted(path for path in args.input.glob("benchmark*.md") if path.is_file())
        output_paths = [args.output / source.name for source in inputs]
    elif args.input.is_file() and args.input.suffix == ".md":
        inputs = [args.input]
        # A single chunk can be used by benchmark_run's per-chunk command
        # template.  Treat an existing directory, or a path without a Markdown
        # filename, as an output directory; otherwise it is the exact result
        # file requested by the caller.
        if args.output.is_dir() or args.output.suffix != ".md":
            output_paths = [args.output / args.input.name]
        else:
            output_paths = [args.output]
    else:
        parser.error("--input must be a Markdown file or a directory containing benchmark*.md files")

    endpoint = args.base_url.rstrip("/") + "/api/generate"
    for source, destination in zip(inputs, output_paths):
        payload = json.dumps({"model": args.model, "prompt": source.read_text(encoding="utf-8"), "stream": True}).encode()
        request = urllib.request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        pieces: list[str] = []
        with urllib.request.urlopen(request) as response:
            for line in response:
                if line.strip():
                    item = json.loads(line)
                    pieces.append(item.get("response", ""))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("".join(pieces), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
