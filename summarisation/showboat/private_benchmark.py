#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run one privacy-preserving benchmark action at a time.

The private config and every source-derived artifact remain under .tmp. Stdout
is intentionally public-safe: it never contains source text, paths, names,
topics, summaries, raw errors, or commands with confidential values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import secrets
import shutil
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE if (HERE / "prepare_benchmark_corpus.py").is_file() else HERE.parents[1]
PREPARE = ROOT / "summarisation" / "prepare_benchmark_corpus.py"
TF = ROOT / "summarisation" / "process_chunks_turbofieldfare.py"
OLLAMA = ROOT / "summarisation" / "process_chunks_ollama.py"
DEFAULT_CONFIG = ROOT / ".tmp" / "showboat-private-config.json"
OWNER_PATTERN = "TurboFieldfareServer|TurboFieldfareMac|TurboFieldfareDecodeService|TurboFieldfareCLI|TurboFieldfarePackageTests|swiftpm-testing-helper|mlx_lm|mlx-lm"
STAMP = re.compile(r"(?<!\d)(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?!\d)")


def load_config(path: Path) -> dict:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("private configuration is unavailable or invalid") from error
    required = {"course_root", "model_dir", "results_root", "summary_prompt", "timeout_seconds"}
    if not required.issubset(config) or not isinstance(config["timeout_seconds"], int):
        raise ValueError("private configuration is missing required values")
    return config


def root_for(config: dict) -> Path:
    root = Path(config["results_root"])
    root = (ROOT / root if not root.is_absolute() else root).resolve()
    try:
        root.relative_to((ROOT / ".tmp").resolve())
    except ValueError as error:
        raise ValueError("results_root must be inside .tmp") from error
    return root


def text(argv: list[str]) -> str:
    try:
        return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False, timeout=30).stdout
    except subprocess.TimeoutExpired:
        return ""


def free_memory() -> int | None:
    match = re.search(r"memory free percentage:\s*(\d+)%", text(["memory_pressure", "-Q"]))
    return int(match.group(1)) if match else None


def model_owner_present() -> bool:
    return bool(text(["pgrep", "-fl", OWNER_PATTERN]).strip())


def ollama_loaded() -> bool:
    return len(text(["ollama", "ps"]).splitlines()) > 1


def timestamp_duration(text_value: str) -> int:
    maximum = 0
    for hour, minute, second in STAMP.findall(text_value):
        maximum = max(maximum, int(hour or 0) * 3600 + int(minute) * 60 + int(second))
    return maximum


def video_inventory(config: dict, destination: Path) -> int:
    course = Path(config["course_root"]).resolve()
    rows = []
    for index, source in enumerate(sorted(path for path in course.rglob("*_video_*.md") if path.is_file())):
        body = source.read_text(encoding="utf-8")
        factor = 0.97 + secrets.randbelow(60_001) / 1_000_000
        label = "Video " + chr(65 + index) if index < 26 else f"Video {index + 1}"
        rows.append({"video": label, "duration_minutes": round(timestamp_duration(body) / 60), "reported_kib": max(1, round(source.stat().st_size * factor / 1024))})
    destination.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return len(rows)


def prepare(config: dict, root: Path) -> None:
    if model_owner_present():
        raise RuntimeError("a model-owning process is already active")
    corpus = root / "corpus"
    if corpus.exists():
        raise RuntimeError("private corpus already exists")
    try:
        completed = subprocess.run([str(PREPARE), config["course_root"], str(corpus)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=120)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("corpus preparation timed out") from error
    if completed.returncode:
        raise RuntimeError("corpus preparation failed")
    videos = video_inventory(config, root / "public-video-table.json")
    manifest = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
    print(f"prepared chunks={len(manifest['chunks'])} videos={videos}")


def child_pids(pid: int) -> set[int]:
    result, pending = {pid}, [pid]
    while pending:
        for token in text(["pgrep", "-P", str(pending.pop())]).split():
            child = int(token)
            if child not in result:
                result.add(child)
                pending.append(child)
    return result


def rss_mib(pids: set[int]) -> float:
    if not pids:
        return 0.0
    values = text(["ps", "-o", "rss=", "-p", ",".join(map(str, sorted(pids)))]).split()
    return sum(int(value) for value in values if value.isdigit()) / 1024


def launch(command: list[str], stdout: Path, stderr: Path, timeout_seconds: int, sample_ollama: bool) -> tuple[int, float, float]:
    with stdout.open("wb") as out, stderr.open("wb") as err:
        process = subprocess.Popen(command, stdout=out, stderr=err)
        started, peak = time.monotonic(), 0.0
        while process.poll() is None:
            if time.monotonic() - started > timeout_seconds:
                process.terminate()
                process.wait(timeout=15)
                raise RuntimeError("command timed out")
            pids = child_pids(process.pid)
            if sample_ollama:
                pids.update(int(value) for value in text(["pgrep", "-f", "Ollama.app|ollama serve"]).split() if value.isdigit())
            peak = max(peak, rss_mib(pids))
            time.sleep(0.25)
        return process.returncode, time.monotonic() - started, peak


def run_one(config: dict, root: Path, backend: str, chunk: int, context: int, warmup: bool) -> None:
    if context not in {4096, 8192, 16384, 32768, 65536}:
        raise ValueError("unsupported context")
    if model_owner_present():
        raise RuntimeError("a TurboFieldfare model-owning process is already active")
    manifest = json.loads((root / "corpus" / "manifest.json").read_text(encoding="utf-8"))
    if not 0 <= chunk < len(manifest["chunks"]):
        raise ValueError("invalid chunk index")
    run_root = root / ("warmup" if warmup else "measured") / backend / f"context-{context}" / f"chunk-{chunk:02d}"
    if run_root.exists():
        raise RuntimeError("result already exists")
    run_root.mkdir(parents=True)
    source, output = root / "corpus" / f"benchmark{chunk:02d}.md", run_root / "summary.md"
    before = free_memory()
    if backend == "turbofieldfare":
        command = [str(TF), "--input", str(source), "--output", str(output), "--cli", str(ROOT / ".build" / "release" / "TurboFieldfareCLI"), "--model", config["model_dir"], "--prompt", config["summary_prompt"], "--max-context", str(context), "--temperature", "1.0", "--top-k", "64", "--top-p", "0.95", "--repetition-penalty", "1.0"]
        sample_ollama = False
    else:
        command = [str(OLLAMA), "--input", str(source), "--output", str(output)]
        sample_ollama = True
    exit_code, wall, peak = launch(command, run_root / "stdout.bin", run_root / "stderr.bin", config["timeout_seconds"], sample_ollama)
    item = {"backend": backend, "chunk": chunk, "context": context, "warmup": warmup, "exit_code": exit_code, "wall_seconds": wall, "peak_rss_mib": peak, "memory_free_before_percent": before, "memory_free_after_percent": free_memory(), "output_bytes": output.stat().st_size if output.exists() else 0, "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest() if output.exists() else None}
    (run_root / "measurement.json").write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ok = exit_code == 0 and output.exists()
    print(f"{backend} chunk={chunk:02d} context={context} status={'ok' if ok else 'failed'} wall_seconds={wall:.3f} peak_rss_mib={peak:.1f} memory_free_before={before} memory_free_after={item['memory_free_after_percent']}")
    if not ok:
        raise RuntimeError("backend failed; inspect private artifacts")


def report(root: Path, destination: Path) -> None:
    videos = json.loads((root / "public-video-table.json").read_text(encoding="utf-8"))
    records = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((root / "measured").rglob("measurement.json"))]
    lines = ["# Confidential-material Gemma 4 comparison", "", "This Showboat notebook excludes source text, summaries, source paths, filenames, topics, commands containing confidential values, and raw backend logs.", "", "## Anonymized input inventory", "", "Reported sizes are independently jittered once by a uniform random factor in [-3%, +3%] and rounded to KiB. This is a publication redaction, not an exact measurement.", "", "| Input | Duration (nearest minute) | Reported size (KiB, jittered) |", "| --- | ---: | ---: |"]
    lines += [f"| {row['video']} | {row['duration_minutes']} | {row['reported_kib']} |" for row in videos]
    lines += ["", "## Per-chunk measurements", "", "| Backend | Chunk | Context | Wall seconds | Peak apparent RSS (MiB) | Exit |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    lines += [f"| {row['backend']} | {row['chunk']:02d} | {row['context']} | {row['wall_seconds']:.3f} | {row['peak_rss_mib']:.1f} | {row['exit_code']} |" for row in records]
    lines += ["", "Peak RSS is sampled every 250 ms from the launched backend and descendants; Ollama additionally samples its local server. It is an apparent process-level maximum, not a device-memory profiler.", "", "TurboFieldfare uses temperature 1.0, top-k 64, top-p 0.95, and repetition penalty 1.0. Ollama uses its local native defaults. This is a real-user-path comparison, not sampler-normalized evidence."]
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"public report rows={len(records)} videos={len(videos)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("preflight")
    sub.add_parser("prepare")
    for name in ("warmup", "measure"):
        action = sub.add_parser(name)
        action.add_argument("backend", choices=["turbofieldfare", "ollama"])
        action.add_argument("chunk", type=int)
        action.add_argument("--context", type=int, default=4096)
    public = sub.add_parser("public-report")
    public.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    config, root = load_config(args.config), None
    root = root_for(config)
    if args.action == "preflight":
        free = free_memory()
        course = Path(config["course_root"])
        has_transcripts = course.is_dir() and any(course.rglob("*_video_*.md"))
        ollama_model = subprocess.run(["ollama", "show", "gemma4:26b"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=30).returncode == 0 if shutil.which("ollama") else False
        good = platform.mac_ver()[0].startswith("26.") and has_transcripts and (Path(config["model_dir"]) / "manifest.json").is_file() and (ROOT / ".build" / "release" / "TurboFieldfareCLI").is_file() and ollama_model and free is not None and free >= 20 and not model_owner_present() and not ollama_loaded()
        if not good:
            raise RuntimeError("preflight checks failed")
        print(f"preflight ok memory_free_percent={free}")
    elif args.action == "prepare":
        prepare(config, root)
    elif args.action in {"warmup", "measure"}:
        run_one(config, root, args.backend, args.chunk, args.context, args.action == "warmup")
    else:
        report(root, args.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
