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
import os
from pathlib import Path
import platform
import re
import secrets
import signal
import shutil
import subprocess
import sys
import time
import traceback


HERE = Path(__file__).resolve().parent
ROOT = HERE if (HERE / "prepare_benchmark_corpus.py").is_file() else HERE.parents[1]
TOOL_DIR = HERE if ROOT == HERE else ROOT / "summarisation"
PREPARE = TOOL_DIR / "prepare_benchmark_corpus.py"
TF = TOOL_DIR / "process_chunks_turbofieldfare.py"
OLLAMA = TOOL_DIR / "process_chunks_ollama.py"
DEFAULT_CONFIG = ROOT / ".tmp" / "showboat-private-config.json"
OWNER_PATTERN = "TurboFieldfareServer|TurboFieldfareMac|TurboFieldfareDecodeService|TurboFieldfareCLI|TurboFieldfarePackageTests|swiftpm-testing-helper|mlx_lm|mlx-lm"
STAMP = re.compile(r"(?<!\d)(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?!\d)")
MIN_MEMORY_FREE_PERCENT = 20
MIN_DISK_FREE_BYTES = 1024**3
PROCESS_GROUP_TERM_GRACE_SECONDS = 15.0


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


def private_error_root(argv: list[str]) -> Path | None:
    """Resolve the configured private root without exposing failures publicly."""
    try:
        config_index = argv.index("--config")
        config_path = Path(argv[config_index + 1])
    except (ValueError, IndexError):
        config_path = DEFAULT_CONFIG
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or "results_root" not in raw:
            return None
        return root_for(raw)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def retain_private_filesystem_error(argv: list[str], error: OSError) -> None:
    """Best-effort private diagnostics; this function must never raise."""
    try:
        root = private_error_root(argv)
        if root is None:
            return
        root.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "error_type": type(error).__name__,
            "detail": str(error),
            "traceback": "".join(traceback.format_exception(error)),
        }
        with (root / "private-errors.jsonl").open("a", encoding="utf-8") as destination:
            destination.write(json.dumps(record, sort_keys=True) + "\n")
    except Exception:
        # This is a privacy boundary: a secondary diagnostic failure must not
        # expose its path or replace the original public-safe message.
        return


def text(argv: list[str]) -> str:
    try:
        return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False, timeout=30).stdout
    except subprocess.TimeoutExpired:
        return ""


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def capture_host_provenance() -> dict:
    """Capture private reproducibility data without printing command output."""
    commit = text(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).strip()
    hardware = text(["sysctl", "-n", "hw.model"]).strip()
    ram = text(["sysctl", "-n", "hw.memsize"]).strip()
    swift = text(["swift", "--version"]).strip()
    return {
        "captured_at": utc_timestamp(),
        "commit": commit if re.fullmatch(r"[0-9a-fA-F]{7,64}", commit) else "unknown",
        "hardware": hardware or "unknown",
        "architecture": platform.machine() or "unknown",
        "ram_bytes": int(ram) if ram.isdigit() else None,
        "macos_version": platform.mac_ver()[0] or "unknown",
        "swift_version": swift or "unknown",
    }


def private_log_text(path: Path) -> str:
    try:
        return path.read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return ""


def free_memory() -> int | None:
    match = re.search(r"memory free percentage:\s*(\d+)%", text(["memory_pressure", "-Q"]))
    return int(match.group(1)) if match else None


def model_owner_present() -> bool:
    return bool(text(["pgrep", "-fl", OWNER_PATTERN]).strip())


def ollama_loaded() -> bool:
    return len(text(["ollama", "ps"]).splitlines()) > 1


def macos_supported() -> bool:
    match = re.match(r"(\d+)", platform.mac_ver()[0])
    return bool(match and int(match.group(1)) >= 26)


def swift_supported() -> bool:
    match = re.search(r"Swift version\s+(\d+)\.(\d+)", text(["swift", "--version"]))
    return bool(match and (int(match.group(1)), int(match.group(2))) >= (6, 2))


def disk_supported(root: Path) -> bool:
    probe = root.resolve()
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    try:
        return shutil.disk_usage(probe).free >= MIN_DISK_FREE_BYTES
    except OSError:
        return False


def model_complete(config: dict) -> bool:
    model = Path(config["model_dir"])
    model = model if model.is_absolute() else ROOT / model
    return (model / "manifest.json").is_file()


def release_cli_available() -> bool:
    return (ROOT / ".build" / "release" / "TurboFieldfareCLI").is_file()


def ollama_model_available() -> bool:
    if not shutil.which("ollama"):
        return False
    try:
        return subprocess.run(
            ["ollama", "show", "gemma4:26b"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=30,
        ).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def full_preflight(config: dict, root: Path) -> int:
    """Apply the complete model-run gate and return the checked memory level."""
    course = Path(config["course_root"])
    try:
        has_transcripts = course.is_dir() and any(course.rglob("*_video_*.md"))
    except OSError:
        has_transcripts = False
    free = free_memory()
    good = all(
        (
            macos_supported(),
            swift_supported(),
            disk_supported(root),
            has_transcripts,
            model_complete(config),
            release_cli_available(),
            ollama_model_available(),
            free is not None and free >= MIN_MEMORY_FREE_PERCENT,
            not model_owner_present(),
            not ollama_loaded(),
        )
    )
    if not good:
        raise RuntimeError("preflight checks failed")
    return free


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
        # The adapter and every backend child belong to a new, owned process
        # group. This is the only group launch may signal on timeout.
        process = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        started, peak = time.monotonic(), 0.0
        while process.poll() is None:
            if time.monotonic() - started > timeout_seconds:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=PROCESS_GROUP_TERM_GRACE_SECONDS)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=PROCESS_GROUP_TERM_GRACE_SECONDS)
                else:
                    # The adapter may obey TERM while a descendant ignores it.
                    # A surviving owned group must not escape the timeout.
                    try:
                        os.killpg(process.pid, 0)
                    except ProcessLookupError:
                        pass
                    else:
                        os.killpg(process.pid, signal.SIGKILL)
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
    manifest = json.loads((root / "corpus" / "manifest.json").read_text(encoding="utf-8"))
    if not 0 <= chunk < len(manifest["chunks"]):
        raise ValueError("invalid chunk index")
    run_root = root / ("warmup" if warmup else "measured") / backend / f"context-{context}" / f"chunk-{chunk:02d}"
    if run_root.exists():
        raise RuntimeError("result already exists")
    source, output = root / "corpus" / f"benchmark{chunk:02d}.md", run_root / "summary.md"
    if backend == "turbofieldfare":
        command = [str(TF), "--input", str(source), "--output", str(output), "--cli", str(ROOT / ".build" / "release" / "TurboFieldfareCLI"), "--model", config["model_dir"], "--prompt", config["summary_prompt"], "--max-context", str(context), "--temperature", "1.0", "--top-k", "64", "--top-p", "0.95", "--repetition-penalty", "1.0"]
        sample_ollama = False
        backend_configuration = {
            "model_dir": config["model_dir"],
            "context": context,
            "temperature": 1.0,
            "top_k": 64,
            "top_p": 0.95,
            "repetition_penalty": 1.0,
            "response_limit": "remaining-context",
        }
    else:
        command = [str(OLLAMA), "--input", str(source), "--output", str(output), "--prompt", config["summary_prompt"]]
        sample_ollama = True
        backend_configuration = {
            "model": "gemma4:26b",
            "sampling_and_context": "native-local-defaults",
        }
    before = full_preflight(config, root)
    run_root.mkdir(parents=True)
    stdout_path, stderr_path = run_root / "stdout.bin", run_root / "stderr.bin"
    provenance = capture_host_provenance()
    started_at = provenance["captured_at"]
    launch_error: RuntimeError | None = None
    try:
        exit_code, wall, peak = launch(command, stdout_path, stderr_path, config["timeout_seconds"], sample_ollama)
    except RuntimeError as error:
        exit_code, wall, peak, launch_error = None, None, None, error
    error_text = private_log_text(stderr_path)
    timing_text = private_log_text(stdout_path)
    item = {
        "backend": backend,
        "chunk": chunk,
        "context": context,
        "warmup": warmup,
        "started_at": started_at,
        "finished_at": utc_timestamp(),
        "provenance": provenance,
        "argv": command,
        "backend_configuration": backend_configuration,
        "protocol_deviations": [
            "confidential-input-publication-redaction",
            "real-user-path-samplers-not-normalized",
        ],
        "exit_code": exit_code,
        "wall_seconds": wall,
        "peak_rss_mib": peak,
        "memory_free_before_percent": before,
        "memory_free_after_percent": free_memory(),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "timing_footer_or_error": (
            (error_text or str(launch_error)) if launch_error
            else error_text if exit_code != 0
            else timing_text
        ),
        "runner_error": str(launch_error) if launch_error else None,
        "output_bytes": output.stat().st_size if output.exists() else 0,
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest() if output.exists() else None,
    }
    (run_root / "measurement.json").write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if launch_error:
        raise launch_error
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
    if records:
        provenance = records[0].get("provenance", {})
        raw_commit = provenance.get("commit", "")
        commit = raw_commit if isinstance(raw_commit, str) and re.fullmatch(r"[0-9a-fA-F]{7,64}", raw_commit) else "unknown"
        raw_macos = provenance.get("macos_version", "")
        macos = raw_macos if isinstance(raw_macos, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+){0,2}", raw_macos) else "unknown"
        raw_swift = provenance.get("swift_version", "")
        swift_match = re.search(r"Swift version\s+[0-9.]+", raw_swift if isinstance(raw_swift, str) else "")
        swift = swift_match.group(0) if swift_match else "Swift version unknown"
        raw_architecture = provenance.get("architecture", "")
        architecture = raw_architecture if raw_architecture in {"arm64", "aarch64", "x86_64"} else "unknown architecture"
        ram_bytes = provenance.get("ram_bytes")
        ram = f"{ram_bytes / 1024**3:.0f} GiB" if isinstance(ram_bytes, int) else "unknown RAM"
        lines += ["", "## Sanitized provenance", "", f"Commit `{commit}`; macOS {macos}; {swift}; {architecture}; {ram}. Exact argv, private paths, raw logs, timing footers/errors, and full host provenance remain in private measurement artifacts."]
    lines += ["", "## Protocol deviations", "", "- `confidential-input-publication-redaction`: confidential inputs, summaries, exact paths, argv, and raw logs are retained privately and excluded from publication.", "- `real-user-path-samplers-not-normalized`: Ollama native defaults are intentionally not normalized to TurboFieldfare settings.", "", "Peak RSS is sampled every 250 ms from the launched backend and descendants; Ollama additionally samples its local server. It is an apparent process-level maximum, not a device-memory profiler.", "", "TurboFieldfare uses temperature 1.0, top-k 64, top-p 0.95, and repetition penalty 1.0. Ollama uses its local native defaults. This is a real-user-path comparison, not sampler-normalized evidence."]
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
        free = full_preflight(config, root)
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
    except OSError as error:
        retain_private_filesystem_error(sys.argv[1:], error)
        print("error: private filesystem operation failed; inspect private diagnostics", file=sys.stderr)
        raise SystemExit(2)
    except (RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
