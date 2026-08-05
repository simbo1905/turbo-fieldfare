#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Score two local summaries with explicitly configured compatible judges."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request


JUDGES = ("gpt-5.6-terra", "claude-sonnet-5", "kimi-k3")


def load_dotenv() -> None:
    """Fill only absent environment variables without exposing credentials."""
    for dotenv in (Path.cwd() / ".env", Path(__file__).resolve().parents[1] / ".env"):
        if not dotenv.is_file():
            continue
        try:
            lines = dotenv.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"").strip("'"))


def verdict(text: str) -> str | None:
    normalized = text.strip().upper().strip(".!")
    if normalized in {"A", "B"}:
        return normalized
    if normalized in {"TIE", "EQUAL", "EQUIVALENT"}:
        return "TIE"
    return None


def request_judge(endpoint: str, model: str, source: str, a: str, b: str) -> tuple[str | None, str | None, str | None, dict]:
    prompt = (
        "Assess faithfulness and usefulness against the source. Choose the materially "
        "better summary. Reply exactly A, B, or TIE. TIE means no material loss; do not "
        "split hairs over style.\n\nSOURCE:\n" + source + "\n\nA:\n" + a + "\n\nB:\n" + b
    )
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("OPENCODE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not token:
        return None, None, "no API key is available", payload
    headers["Authorization"] = "Bearer " + token
    try:
        encoded = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(endpoint, data=encoded, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
        parsed = json.loads(raw)
        choice = verdict(str(parsed["choices"][0]["message"]["content"]))
        return choice, raw, None if choice else "invalid verdict", payload
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError, KeyError, IndexError) as error:
        return None, None, "judge request failed", payload


def private_log(path: Path, item: dict) -> None:
    root = (Path(__file__).resolve().parents[1] / ".tmp").resolve()
    try:
        path.resolve().relative_to(root)
    except ValueError as error:
        raise ValueError("private log must be inside .tmp") from error
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--summary-a", type=Path, required=True)
    parser.add_argument("--summary-b", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--endpoint", required=True, help="explicit OpenAI-compatible gateway serving all three judge models")
    parser.add_argument("--private-log", type=Path, help="optional .tmp-only JSONL raw request/response audit")
    args = parser.parse_args(argv)
    load_dotenv()
    try:
        source = args.source.read_text(encoding="utf-8")
        summary_a = args.summary_a.read_text(encoding="utf-8")
        summary_b = args.summary_b.read_text(encoding="utf-8")
    except OSError:
        print("error: pairwise inputs are unavailable", file=sys.stderr)
        return 2
    rows: list[dict] = []
    score_a = score_b = 0
    for model in JUDGES:
        choice, raw, error, payload = request_judge(args.endpoint, model, source, summary_a, summary_b)
        if choice == "A":
            points_a, points_b = 2, 0
        elif choice == "B":
            points_a, points_b = 0, 2
        elif choice == "TIE":
            points_a = points_b = 1
        else:
            points_a = points_b = 0
        score_a += points_a
        score_b += points_b
        requested_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        rows.append({"judge_model": model, "verdict": choice, "points_a": points_a, "points_b": points_b, "error": error, "requested_at": requested_at})
        if args.private_log:
            private_log(args.private_log, {"judge_model": model, "requested_at": requested_at, "request": payload, "raw_response": raw, "error": error})
    aggregate = {"score_a": score_a, "score_b": score_b, "verdict": "A" if score_a > score_b else "B" if score_b > score_a else "TIE"}
    result = {"format": "turbofieldfare-pairwise-spot-check-v1", "judges": rows, "aggregate": aggregate}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"pairwise judges={len(rows)} valid={sum(row['verdict'] is not None for row in rows)} verdict={aggregate['verdict']}")
    return 0 if all(row["verdict"] is not None for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
