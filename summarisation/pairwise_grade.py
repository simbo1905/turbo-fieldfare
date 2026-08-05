#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Opt-in blind pairwise judging for exactly two local result directories."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import urllib.error
import urllib.request


def timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def load_dotenv() -> None:
    """Load absent environment values only; never serialize or print secrets."""
    dotenv = Path(".env")
    if not dotenv.is_file():
        return
    for line in dotenv.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def ask(endpoint: str, model: str, source: str, a: str, b: str) -> tuple[str | None, str | None, str | None]:
    payload = {"model": model, "messages": [{"role": "user", "content":
        "Compare the source and two summaries. Reply with exactly A, B, or TIE.\n\nSOURCE:\n%s\n\nA:\n%s\n\nB:\n%s" % (source, a, b)}]}
    encoded = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENCODE_API_KEY")
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        request = urllib.request.Request(endpoint, data=encoded, headers=headers, method="POST")
        with urllib.request.urlopen(request) as response:
            raw = response.read().decode("utf-8")
        parsed = json.loads(raw)
        text = parsed["choices"][0]["message"]["content"].strip().upper()
        return (text if text in {"A", "B", "TIE"} else None), raw, None if text in {"A", "B", "TIE"} else "invalid verdict"
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError, IndexError) as error:
        return None, None, str(error)


def blank_score() -> dict[str, int]:
    return {"wins": 0, "losses": 0, "ties": 0}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--candidate-a", required=True, type=Path)
    parser.add_argument("--candidate-b", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--endpoint",
        required=True,
        help="OpenAI-compatible gateway that can serve every requested judge model",
    )
    parser.add_argument("--judge-model", action="append", required=True)
    args = parser.parse_args(argv)
    load_dotenv()
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    requests: list[dict] = []
    candidates = {"candidate-a": blank_score(), "candidate-b": blank_score()}
    by_judge = {model: {"candidate-a": blank_score(), "candidate-b": blank_score()} for model in args.judge_model}
    valid = invalid = 0
    for chunk in manifest["chunks"]:
        filename = chunk["path"]
        source = (manifest_path.parent / filename).read_text(encoding="utf-8")
        candidate_a = (args.candidate_a / filename).read_text(encoding="utf-8")
        candidate_b = (args.candidate_b / filename).read_text(encoding="utf-8")
        orders = [("candidate-a-as-A", "candidate-a", candidate_a, "candidate-b", candidate_b),
                  ("candidate-b-as-A", "candidate-b", candidate_b, "candidate-a", candidate_a)]
        for order, a_name, a_text, b_name, b_text in orders:
            for model in args.judge_model:
                verdict, raw, error = ask(args.endpoint, model, source, a_text, b_text)
                item = {"chunk": Path(filename).stem, "order": order, "judge_model": model,
                        "requested_at": timestamp(), "raw_response": raw, "verdict": verdict, "error": error}
                requests.append(item)
                if verdict is None:
                    invalid += 1
                    continue
                valid += 1
                if verdict == "TIE":
                    for name in (a_name, b_name):
                        candidates[name]["ties"] += 1
                        by_judge[model][name]["ties"] += 1
                else:
                    winner, loser = (a_name, b_name) if verdict == "A" else (b_name, a_name)
                    candidates[winner]["wins"] += 1
                    candidates[loser]["losses"] += 1
                    by_judge[model][winner]["wins"] += 1
                    by_judge[model][loser]["losses"] += 1
    args.output.mkdir(parents=True, exist_ok=True)
    result = {"format": "turbofieldfare-pairwise-votes-v1", "requests": requests,
              "summary": {"valid_votes": valid, "invalid_or_failed": invalid, "candidates": candidates, "by_judge": by_judge}}
    (args.output / "votes.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
