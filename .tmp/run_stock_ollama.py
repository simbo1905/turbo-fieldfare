#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run every prepared chunk through stock Ollama and retain private evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import urllib.request

PROMPT = (
    "Summarise the following instructional transcript faithfully and concisely. "
    "Preserve substantive facts, figures, and recommendations."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", default="gemma4:26b")
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=float, default=1800)
    args = parser.parse_args(argv)

    chunks = sorted(args.input.glob("chunk*.md"))
    if not chunks:
        parser.error("input contains no chunk files")
    if args.output.exists():
        parser.error("output already exists")
    args.output.mkdir(parents=True)
    endpoint = args.base_url.rstrip("/") + "/api/generate"
    records = []
    for index, chunk in enumerate(chunks):
        started_at = utc_now()
        started = time.monotonic()
        payload = {
            "model": args.model,
            "prompt": PROMPT + "\n\n" + chunk.read_text(encoding="utf-8"),
            "stream": False,
        }
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=args.timeout) as response:
                result = json.loads(response.read())
            error = None
        except Exception as exception:
            result = {}
            error = f"{type(exception).__name__}: {exception}"
        elapsed = time.monotonic() - started
        ended_at = utc_now()
        output_dir = args.output / f"chunk{index:02d}"
        output_dir.mkdir()
        visible = result.get("response", "")
        thinking = result.get("thinking", "")
        (output_dir / "response.md").write_text(visible, encoding="utf-8")
        (output_dir / "thinking.md").write_text(thinking, encoding="utf-8")
        record = {
            "chunk": chunk.name,
            "started_at": started_at,
            "ended_at": ended_at,
            "wall_seconds": elapsed,
            "input_bytes": chunk.stat().st_size,
            "response_bytes": len(visible.encode("utf-8")),
            "thinking_bytes": len(thinking.encode("utf-8")),
            "done_reason": result.get("done_reason"),
            "prompt_eval_count": result.get("prompt_eval_count"),
            "eval_count": result.get("eval_count"),
            "total_duration_ns": result.get("total_duration"),
            "load_duration_ns": result.get("load_duration"),
            "prompt_eval_duration_ns": result.get("prompt_eval_duration"),
            "eval_duration_ns": result.get("eval_duration"),
            "error": error,
        }
        (output_dir / "record.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        records.append(record)
        print(
            f"ollama chunk={index + 1}/{len(chunks)} wall={elapsed:.2f}s "
            f"response_bytes={record['response_bytes']} error={error is not None}",
            flush=True,
        )
        if error:
            break
    (args.output / "manifest.json").write_text(
        json.dumps({"model": args.model, "stock_options": True, "records": records}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if len(records) == len(chunks) and not any(row["error"] for row in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
