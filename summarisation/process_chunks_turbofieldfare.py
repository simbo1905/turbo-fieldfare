#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run one TurboFieldfare CLI summary request for a benchmark chunk.

The adapter deliberately relies on the CLI's Gemma summary-profile defaults:
4,096-token context, temperature 1.0, top-p 0.95, top-k 64, repetition
penalty 1.1, and the remaining-context output limit.  Supplying only the
model and messages file keeps that profile in one public place: the CLI.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cli", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--max-context", type=int)
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--top-k", type=int)
    parser.add_argument("--top-p", type=float)
    parser.add_argument("--repetition-penalty", type=float)
    parser.add_argument("--expert-cache-slots", type=int)
    parser.add_argument("--expert-cache-policy")
    parser.add_argument("--prefill", choices=["on", "off"])
    parser.add_argument("--prefill-chunk-tokens", type=int)
    parser.add_argument("--rdadvise")
    args = parser.parse_args(argv)

    source = args.input.read_text(encoding="utf-8")
    messages = [{"role": "user", "content": args.prompt + "\n\n" + source}]

    # The message file contains source text, so never place it in the output
    # tree where benchmark artifacts are retained.  The context manager removes
    # it on both successful and failed CLI invocations.
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".json", delete=True
    ) as message_file:
        json.dump(messages, message_file)
        message_file.flush()
        command = [str(args.cli), "--model", args.model, "--messages-file", message_file.name]
        for flag, value in [
            ("--max-context", args.max_context),
            ("--temperature", args.temperature),
            ("--top-k", args.top_k),
            ("--top-p", args.top_p),
            ("--repetition-penalty", args.repetition_penalty),
            ("--expert-cache-slots", args.expert_cache_slots),
            ("--expert-cache-policy", args.expert_cache_policy),
            ("--prefill", args.prefill),
            ("--prefill-chunk-tokens", args.prefill_chunk_tokens),
            ("--rdadvise", args.rdadvise),
        ]:
            if value is not None:
                command.extend([flag, str(value)])
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(completed.stdout, encoding="utf-8")
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
