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


JUDGES = ("gpt-5.6-terra", "claude-sonnet-5", "deepseek-v4-pro")
ZEN_BASE_URL = "https://opencode.ai/zen/v1"
JUDGE_PROTOCOLS = {
    # Zen accepts the requested cross-provider model identifiers through its
    # OpenAI-compatible chat endpoint. Keep the wire format identical so the
    # blind-comparison request is the same task for every judge.
    "gpt-5.6-terra": ("chat", "/chat/completions"),
    "claude-sonnet-5": ("chat", "/chat/completions"),
    "deepseek-v4-pro": ("chat", "/chat/completions"),
}


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


def response_text(protocol: str, parsed: dict) -> str:
    if protocol == "responses":
        if isinstance(parsed.get("output_text"), str):
            return parsed["output_text"]
        return str(parsed["output"][0]["content"][0]["text"])
    if protocol == "messages":
        return str(parsed["content"][0]["text"])
    return str(parsed["choices"][0]["message"]["content"])


def request_judge(zen_base_url: str, model: str, source: str, a: str, b: str) -> tuple[str | None, str | None, str | None, dict]:
    prompt = (
        "Act as a conservative, source-grounded evaluator performing a non-inferiority test "
        "between two summaries of learning material. The null hypothesis is that the summaries "
        "are equivalent for practical use. Default to TIE unless the source provides clear "
        "evidence that one summary is materially degraded. This is not a preference-ranking "
        "task and you must not select a marginal winner.\n\n"
        "Treat length, verbosity, formatting, section structure, rhetorical polish, and prose "
        "style as nuisance variables. Do not reward a longer answer: higher inference or reasoning "
        "budgets often add prose without adding information and can regress toward generic text. "
        "Compare only source-grounded factual accuracy, coverage of decision-relevant concepts, "
        "precision, and clarity.\n\n"
        "Choose A or B only when the other candidate has a deployment-relevant material defect, "
        "such as: an unsupported factual claim or hallucination; an inference or editorial "
        "interpretation promoted to an explicitly stated source fact; a material distortion, "
        "overstatement, or loss of precision; or omission of a substantive concept that a "
        "reasonable business-English executive summary should retain. A summary need not repeat "
        "every detail. Minor omissions, formatting artifacts, stylistic differences, balanced "
        "trade-offs, and ambiguous advantages require TIE.\n\n"
        "Evaluate silently. Reply with exactly one token: A, B, or TIE.\n\nSOURCE:\n"
        + source + "\n\nA:\n" + a + "\n\nB:\n" + b
    )
    protocol, suffix = JUDGE_PROTOCOLS[model]
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    headers = {
        "Content-Type": "application/json",
        # urllib's default Python signature is rejected by Zen's Cloudflare
        # browser-integrity rule (error 1010), before Zen sees the API key.
        "User-Agent": "TurboFieldfare-Summarisation-Benchmark/1.0",
    }
    token = os.environ.get("OPENCODE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not token:
        return None, None, "no API key is available", payload
    headers["Authorization"] = "Bearer " + token
    try:
        encoded = json.dumps(payload).encode("utf-8")
        endpoint = zen_base_url.rstrip("/") + suffix
        request = urllib.request.Request(endpoint, data=encoded, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
        parsed = json.loads(raw)
        choice = verdict(response_text(protocol, parsed))
        return choice, raw, None if choice else "invalid verdict", payload
    except urllib.error.HTTPError as error:
        # HTTPError is also a readable response object. Preserve its body only
        # in the caller's .tmp-restricted audit; keep public errors sanitized.
        raw = error.read().decode("utf-8", errors="replace")
        return None, raw, f"judge request failed (HTTP {error.code})", payload
    except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError):
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
    parser.add_argument("--zen-base-url", default=ZEN_BASE_URL, help="OpenCode Zen API base URL; provider paths are fixed by model")
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
        choice, raw, error, payload = request_judge(args.zen_base_url, model, source, summary_a, summary_b)
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
