#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Serially measure caller-supplied summary backend commands; never grade output."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
from pathlib import Path
import shlex
import subprocess
import sys
import time


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_capture(argv: list[str]) -> str:
    completed = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return completed.stdout


def ollama_snapshot(binary: str, model: str) -> dict[str, str]:
    version = run_capture([binary, "--version"])
    modelfile = run_capture([binary, "show", model, "--modelfile"])
    ps = run_capture([binary, "ps"])
    digest = ""
    for token in (modelfile + "\n" + ps).replace("@", " ").split():
        if "sha256:" in token:
            digest = token[token.index("sha256:"):]
            break
    if not digest:
        lines = ps.splitlines()
        digest = lines[1].split()[1] if len(lines) > 1 and len(lines[1].split()) > 1 else ""
    return {"model": model, "version": version, "modelfile": modelfile, "ps": ps, "digest": digest}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--backend", required=True)
    parser.add_argument("--backend-command", required=True, help="shell-style argv template containing {input} and {output}")
    parser.add_argument("--config-json", default="{}")
    parser.add_argument("--ollama-bin")
    parser.add_argument("--ollama-model")
    args = parser.parse_args(argv)
    try:
        configuration = json.loads(args.config_json)
    except json.JSONDecodeError as error:
        parser.error("invalid --config-json: %s" % error)
    if not isinstance(configuration, dict):
        parser.error("--config-json must contain an object")
    if bool(args.ollama_bin) != bool(args.ollama_model):
        parser.error("--ollama-bin and --ollama-model must be supplied together")

    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    results = args.results.resolve()
    results.mkdir(parents=True, exist_ok=True)
    (results / "outputs").mkdir(exist_ok=True)
    (results / "logs").mkdir(exist_ok=True)
    template = shlex.split(args.backend_command)
    if not template or not any("{input}" in item for item in template) or not any("{output}" in item for item in template):
        parser.error("--backend-command must contain {input} and {output}")
    record: dict = {
        "format": "turbofieldfare-summarisation-run-v1",
        "manifest_sha256": sha256(manifest_path),
        "backend": {"identity": args.backend, "configuration": configuration},
        "host": {"platform": platform.platform(), "python": sys.version, "machine": platform.machine()},
        "chunks": [],
    }
    if args.ollama_bin:
        record["ollama_metadata"] = {"before": ollama_snapshot(args.ollama_bin, args.ollama_model)}
    for chunk in manifest["chunks"]:
        source = manifest_path.parent / chunk["path"]
        output_relative = "outputs/" + chunk["path"]
        stdout_relative = "logs/" + chunk["path"] + ".stdout"
        stderr_relative = "logs/" + chunk["path"] + ".stderr"
        output = results / output_relative
        command = [part.replace("{input}", str(source)).replace("{output}", str(output)) for part in template]
        started = now()
        started_clock = time.monotonic()
        completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        wall = time.monotonic() - started_clock
        finished = now()
        (results / stdout_relative).write_text(completed.stdout, encoding="utf-8")
        (results / stderr_relative).write_text(completed.stderr, encoding="utf-8")
        item = {"chunk": chunk["path"], "argv": command, "started_at": started, "finished_at": finished,
                "wall_seconds": wall, "exit_status": completed.returncode, "output_path": output_relative,
                "stdout_path": stdout_relative, "stderr_path": stderr_relative}
        if output.is_file():
            item.update({"output_bytes": output.stat().st_size, "output_sha256": sha256(output)})
        else:
            item.update({"output_bytes": 0, "output_sha256": None})
        record["chunks"].append(item)
    if args.ollama_bin:
        record["ollama_metadata"]["after"] = ollama_snapshot(args.ollama_bin, args.ollama_model)
    (results / "run-manifest.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
