#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Token-count prepared chunks without loading the TurboFieldfare model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile

PROMPT = (
    "Summarise the following instructional transcript faithfully and concisely. "
    "Preserve substantive facts, figures, and recommendations."
)
TOKEN_COUNT = re.compile(r"context overflow: prompt (\d+) reaches maxContext 1")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cli", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--max-context", type=int, default=4096)
    args = parser.parse_args(argv)

    if args.max_context <= 1:
        parser.error("--max-context must exceed the one-token probe context")
    if args.output.exists():
        parser.error("output already exists")
    rows = []
    for chunk in sorted(args.input.glob("chunk*.md")):
        messages = [{
            "role": "user",
            "content": PROMPT + "\n\n" + chunk.read_text(encoding="utf-8"),
        }]
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json") as message_file:
            json.dump(messages, message_file)
            message_file.flush()
            completed = subprocess.run(
                [
                    str(args.cli), "--model", str(args.model),
                    "--messages-file", message_file.name,
                    "--max-context", "1", "--quiet",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        match = TOKEN_COUNT.search(completed.stderr)
        if completed.returncode != 2 or not match:
            raise RuntimeError(f"token probe failed for {chunk.name}: {completed.stderr.strip()}")
        tokens = int(match.group(1))
        rows.append({
            "chunk": chunk.name,
            "prompt_tokens": tokens,
            "eligible": tokens < args.max_context,
        })
    result = {
        "max_context": args.max_context,
        "eligible": [row["chunk"] for row in rows if row["eligible"]],
        "blacklisted": [row["chunk"] for row in rows if not row["eligible"]],
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"eligible={len(result['eligible'])} blacklisted={len(result['blacklisted'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
