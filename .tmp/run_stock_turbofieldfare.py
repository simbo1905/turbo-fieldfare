#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run prepared chunks through stock TurboFieldfare and retain private evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

PROMPT = (
    "Summarise the following instructional transcript faithfully and concisely. "
    "Preserve substantive facts, figures, and recommendations."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def process_tree(root_pid: int) -> set[int]:
    pending = [root_pid]
    result = {root_pid}
    while pending:
        completed = subprocess.run(
            ["pgrep", "-P", str(pending.pop())], capture_output=True, text=True, check=False
        )
        for token in completed.stdout.split():
            child = int(token)
            if child not in result:
                result.add(child)
                pending.append(child)
    return result


def rss_mib(pids: set[int]) -> float:
    if not pids:
        return 0.0
    completed = subprocess.run(
        ["ps", "-o", "rss=", "-p", ",".join(map(str, sorted(pids)))],
        capture_output=True,
        text=True,
        check=False,
    )
    return sum(int(value) for value in completed.stdout.split() if value.isdigit()) / 1024


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cli", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=1800)
    args = parser.parse_args(argv)

    chunks = sorted(args.input.glob("chunk*.md"))
    if not chunks:
        parser.error("input contains no chunk files")
    if args.output.exists():
        parser.error("output already exists")
    args.output.mkdir(parents=True)
    records = []
    for index, chunk in enumerate(chunks):
        output_dir = args.output / f"chunk{index:02d}"
        output_dir.mkdir()
        source = chunk.read_text(encoding="utf-8")
        messages = [{"role": "user", "content": PROMPT + "\n\n" + source}]
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json") as message_file:
            json.dump(messages, message_file)
            message_file.flush()
            command = [str(args.cli), "--model", str(args.model), "--messages-file", message_file.name]
            started_at = utc_now()
            started = time.monotonic()
            with (output_dir / "response.md").open("wb") as stdout, (output_dir / "stderr.txt").open("wb") as stderr:
                process = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
                peak_rss = 0.0
                while process.poll() is None:
                    if time.monotonic() - started > args.timeout:
                        process.kill()
                        process.wait()
                        break
                    peak_rss = max(peak_rss, rss_mib(process_tree(process.pid)))
                    time.sleep(0.25)
                exit_code = process.returncode
        elapsed = time.monotonic() - started
        ended_at = utc_now()
        response_path = output_dir / "response.md"
        stderr_path = output_dir / "stderr.txt"
        response = response_path.read_bytes()
        record = {
            "chunk": chunk.name,
            "started_at": started_at,
            "ended_at": ended_at,
            "wall_seconds": elapsed,
            "input_bytes": chunk.stat().st_size,
            "response_bytes": len(response),
            "peak_rss_mib": peak_rss,
            "exit_code": exit_code,
            "timing_footer_or_error": stderr_path.read_text(encoding="utf-8", errors="replace"),
        }
        (output_dir / "record.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        records.append(record)
        print(
            f"turbofieldfare chunk={index + 1}/{len(chunks)} wall={elapsed:.2f}s "
            f"peak_rss_mib={peak_rss:.1f} exit={exit_code}",
            flush=True,
        )
        if exit_code != 0:
            break
    (args.output / "manifest.json").write_text(
        json.dumps({"stock_options": True, "records": records}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if len(records) == len(chunks) and all(row["exit_code"] == 0 for row in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
