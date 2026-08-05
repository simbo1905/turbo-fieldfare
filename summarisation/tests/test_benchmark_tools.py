"""Black-box red tests for the imported summarisation benchmark toolkit.

These fixtures deliberately use only generated local text, executables, and an
in-process HTTP server.  They must never access a course checkout or a model.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "prepare_benchmark_corpus.py"
OLLAMA = ROOT / "process_chunks_ollama.py"
TURBOFIELDFAR = ROOT / "process_chunks_turbofieldfare.py"
GRADE = ROOT / "pairwise_grade.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FakeHTTP:
    """A tiny OpenAI-compatible endpoint that records every JSON request."""

    def __init__(self, response_for):
        self.requests = []
        self.response_for = response_for
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler API
                size = int(self.headers["Content-Length"])
                request = json.loads(self.rfile.read(size))
                parent.requests.append(request)
                status, response = parent.response_for(request)
                encoded = json.dumps(response).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def log_message(self, *_args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever)

    @property
    def url(self) -> str:
        return "http://127.0.0.1:%d" % self.server.server_port

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()


class BenchmarkToolsTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.temp = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def command(self, script: Path, *args: str, check: bool = True, env=None):
        return subprocess.run(
            [sys.executable, str(script), *map(str, args)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
            env=env,
        )

    def make_course(self) -> Path:
        course = self.temp / "course"
        course.mkdir()
        # Deliberately unsorted creation order and one non-video distractor.
        (course / "z_video_2.md").write_text("Z" * 45_000)
        (course / "ignore.md").write_text("not part of the corpus")
        (course / "a_video_1.md").write_text("A" * 45_000)
        (course / "m_video_3.md").write_text("M" * 45_000)
        return course

    def prepare(self, course: Path, output: Path):
        return self.command(PREPARE, course, output)

    def test_prepare_selects_sorted_video_transcripts_and_reproducible_manifest(self):
        course = self.make_course()
        first = self.temp / "prepared-first"
        second = self.temp / "prepared-second"
        self.prepare(course, first)
        self.prepare(course, second)

        manifest = json.loads((first / "manifest.json").read_text())
        self.assertEqual(manifest["format"], "turbofieldfare-summarisation-benchmark-v1")
        self.assertIn("tool_version", manifest)
        self.assertEqual(manifest["chunk_size_chars"], 11_000)
        self.assertEqual(manifest["chunk_step_chars"], 10_000)
        self.assertEqual(
            [source["path"] for source in manifest["sources"]],
            ["a_video_1.md", "m_video_3.md", "z_video_2.md"],
        )
        self.assertEqual(len(manifest["chunks"]), 12)
        self.assertEqual(manifest["selected_indices"], sorted(manifest["selected_indices"]))
        self.assertEqual(manifest["selected_indices"][0], 0)
        self.assertEqual(manifest["selected_indices"][-1], 12)
        self.assertEqual((first / "benchmark00.md").read_text(), "A" * 11_000)
        separator_chunk = next(
            chunk for chunk in manifest["chunks"] if chunk["source_chunk_index"] == 4
        )
        separator_text = (first / separator_chunk["path"]).read_text()
        self.assertEqual(separator_text[5_000:5_002], "\n\n")
        self.assertEqual(sha256(first / "manifest.json"), sha256(second / "manifest.json"))
        for number, chunk in enumerate(manifest["chunks"]):
            path = first / ("benchmark%02d.md" % number)
            self.assertEqual(chunk["path"], path.name)
            self.assertEqual(chunk["sha256"], sha256(path))
            self.assertEqual(chunk["offset_chars"], chunk["source_chunk_index"] * 10_000)

    def test_prepare_rejects_an_output_root_inside_the_external_course(self):
        course = self.make_course()
        result = self.command(PREPARE, course, course / "generated", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("course", result.stderr.lower())
        self.assertFalse((course / "generated").exists())

    def prepared_fixture(self) -> tuple[Path, Path]:
        course = self.make_course()
        prepared = self.temp / "prepared"
        self.prepare(course, prepared)
        return course, prepared

    def write_executable(self, name: str, body: str) -> Path:
        path = self.temp / name
        path.write_text("#!/usr/bin/env python3\n" + body)
        path.chmod(0o755)
        return path

    def test_ollama_chunk_processor_accepts_aliases_and_streamed_responses(self):
        chunks = self.temp / "chunks"
        chunks.mkdir()
        (chunks / "benchmark00.md").write_text("first source")
        (chunks / "benchmark01.md").write_text("second source")

        # The processor must support Ollama NDJSON streams, not merely a
        # one-object response.  This server writes the stream itself.
        class StreamServer(FakeHTTP):
            def __init__(server_self):
                server_self.requests = []
                outer = server_self

                class Handler(BaseHTTPRequestHandler):
                    def do_POST(handler_self):  # noqa: N802
                        size = int(handler_self.headers["Content-Length"])
                        outer.requests.append(json.loads(handler_self.rfile.read(size)))
                        payload = b'{"response":"brief ","done":false}\n{"response":"summary","done":true}\n'
                        handler_self.send_response(200)
                        handler_self.send_header("Content-Type", "application/x-ndjson")
                        handler_self.send_header("Content-Length", str(len(payload)))
                        handler_self.end_headers()
                        handler_self.wfile.write(payload)

                    def log_message(handler_self, *_args):
                        pass

                server_self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
                server_self.thread = threading.Thread(target=server_self.server.serve_forever)

        output = self.temp / "ollama-results"
        with StreamServer() as server:
            self.command(
                OLLAMA,
                "--input", chunks,
                "--output", output,
                "--base-url", server.url,
                "--model", "gemma4:26b",
                "--prompt", "Summarise faithfully.",
            )
            self.assertEqual(len(server.requests), 2)
            self.assertEqual(
                [request["prompt"] for request in server.requests],
                [
                    "Summarise faithfully.\n\nfirst source",
                    "Summarise faithfully.\n\nsecond source",
                ],
            )
            self.assertTrue(
                all(set(request) == {"model", "prompt", "stream"} for request in server.requests)
            )
        self.assertEqual((output / "benchmark00.md").read_text(), "brief summary")
        self.assertEqual((output / "benchmark01.md").read_text(), "brief summary")

    def test_ollama_chunk_processor_accepts_one_input_and_one_output_file_for_benchmark_run(self):
        """The per-chunk command template must not require directory inputs."""
        source = self.temp / "benchmark07.md"
        source.write_text("single benchmark source", encoding="utf-8")
        output = self.temp / "nested" / "result.md"

        # The adapter must continue to consume Ollama's NDJSON stream and send
        # no sampler or context overrides: native model defaults are the point
        # of this comparison path.
        class StreamServer(FakeHTTP):
            def __init__(server_self):
                server_self.requests = []
                outer = server_self

                class Handler(BaseHTTPRequestHandler):
                    def do_POST(handler_self):  # noqa: N802
                        size = int(handler_self.headers["Content-Length"])
                        outer.requests.append(json.loads(handler_self.rfile.read(size)))
                        payload = b'{"response":"one ","done":false}\n{"response":"summary","done":true}\n'
                        handler_self.send_response(200)
                        handler_self.send_header("Content-Type", "application/x-ndjson")
                        handler_self.send_header("Content-Length", str(len(payload)))
                        handler_self.end_headers()
                        handler_self.wfile.write(payload)

                    def log_message(handler_self, *_args):
                        pass

                server_self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
                server_self.thread = threading.Thread(target=server_self.server.serve_forever)

        with StreamServer() as server:
            completed = self.command(
                OLLAMA,
                "--input", source,
                "--output", output,
                "--base-url", server.url,
                "--model", "gemma4:26b",
                "--prompt", "Summarise faithfully.",
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(len(server.requests), 1)
            self.assertEqual(
                server.requests[0],
                {
                    "model": "gemma4:26b",
                    "prompt": "Summarise faithfully.\n\nsingle benchmark source",
                    "stream": True,
                },
            )
        self.assertEqual(output.read_text(encoding="utf-8"), "one summary")

    def test_turbofieldfare_chunk_adapter_uses_messages_and_gemma_profile_defaults(self):
        """The adapter is a one-chunk backend: it never starts a real model in tests."""
        source = self.temp / "benchmark00.md"
        source.write_text("source transcript", encoding="utf-8")
        result = self.temp / "results" / "benchmark00.md"
        invocation = self.temp / "fake-cli-record.json"
        fake_cli = self.write_executable(
            "fake-turbofieldfare-cli.py",
            "import json, os, pathlib, sys\n"
            "argv = sys.argv[1:]\n"
            "messages_path = pathlib.Path(argv[argv.index('--messages-file') + 1])\n"
            "pathlib.Path(os.environ['FAKE_CLI_RECORD']).write_text(json.dumps({\n"
            "    'argv': argv, 'messages_path': str(messages_path),\n"
            "    'messages': json.loads(messages_path.read_text())\n"
            "}))\n"
            "print('faithful fake summary')\n",
        )
        completed = subprocess.run(
            [
                sys.executable, str(TURBOFIELDFAR),
                "--input", str(source), "--output", str(result),
                "--cli", str(fake_cli), "--model", "/models/gemma4.gturbo",
                "--prompt", "Summarise faithfully.",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**__import__("os").environ, "FAKE_CLI_RECORD": str(invocation)},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(result.read_text(encoding="utf-8"), "faithful fake summary\n")
        recorded = json.loads(invocation.read_text(encoding="utf-8"))
        self.assertEqual(
            recorded["argv"],
            ["--model", "/models/gemma4.gturbo", "--messages-file", recorded["messages_path"]],
        )
        self.assertFalse(Path(recorded["messages_path"]).is_relative_to(result.parent))
        self.assertEqual(
            recorded["messages"],
            [{"role": "user", "content": "Summarise faithfully.\n\nsource transcript"}],
        )

    def test_pairwise_grading_reverses_blind_labels_records_three_judges_and_excludes_invalid(self):
        _course, prepared = self.prepared_fixture()
        turbo = self.temp / "turbo"
        ollama = self.temp / "ollama"
        turbo.mkdir()
        ollama.mkdir()
        for number in range(12):
            (turbo / ("benchmark%02d.md" % number)).write_text("turbo summary")
            (ollama / ("benchmark%02d.md" % number)).write_text("ollama summary")

        def judge_response(request):
            if request["model"] == "kimi-k3":
                return 200, {"choices": [{"message": {"content": "not a verdict"}}]}
            return 200, {"choices": [{"message": {"content": "A"}}]}

        votes = self.temp / "votes"
        with FakeHTTP(judge_response) as server:
            self.command(
                GRADE,
                "--manifest", prepared / "manifest.json",
                "--candidate-a", turbo,
                "--candidate-b", ollama,
                "--output", votes,
                "--endpoint", server.url,
                "--judge-model", "gpt-5.6-terra",
                "--judge-model", "claude-sonnet-5",
                "--judge-model", "kimi-k3",
                env={**os.environ, "OPENCODE_API_KEY": "test-secret-must-not-be-recorded"},
            )
            self.assertEqual(len(server.requests), 72)
            self.assertEqual(
                {request["model"] for request in server.requests},
                {"gpt-5.6-terra", "claude-sonnet-5", "kimi-k3"},
            )

        record = json.loads((votes / "votes.json").read_text())
        self.assertNotIn("test-secret-must-not-be-recorded", (votes / "votes.json").read_text())
        self.assertEqual(len(record["requests"]), 72)
        self.assertEqual(record["summary"]["valid_votes"], 48)
        self.assertEqual(record["summary"]["invalid_or_failed"], 24)
        self.assertEqual(record["summary"]["candidates"]["candidate-a"]["wins"], 24)
        self.assertEqual(record["summary"]["candidates"]["candidate-b"]["wins"], 24)
        orders = {(item["chunk"], item["order"]) for item in record["requests"]}
        for number in range(12):
            self.assertIn(("benchmark%02d" % number, "candidate-a-as-A"), orders)
            self.assertIn(("benchmark%02d" % number, "candidate-b-as-A"), orders)
        invalid = [item for item in record["requests"] if item["judge_model"] == "kimi-k3"]
        self.assertTrue(all(item["verdict"] is None and item["error"] for item in invalid))
        valid = [item for item in record["requests"] if item["judge_model"] == "gpt-5.6-terra"]
        self.assertTrue(all(item["raw_response"] and item["requested_at"] for item in valid))

    def test_pairwise_grading_requires_an_explicit_compatible_gateway(self):
        _course, prepared = self.prepared_fixture()
        candidates = self.temp / "candidates"
        candidates.mkdir()
        for number in range(12):
            (candidates / ("benchmark%02d.md" % number)).write_text("summary")

        completed = self.command(
            GRADE,
            "--manifest", prepared / "manifest.json",
            "--candidate-a", candidates,
            "--candidate-b", candidates,
            "--output", self.temp / "votes",
            "--judge-model", "gpt-5.6-terra",
            "--judge-model", "claude-sonnet-5",
            "--judge-model", "kimi-k3",
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("--endpoint", completed.stderr)
        self.assertFalse((self.temp / "votes").exists())


if __name__ == "__main__":
    unittest.main()
