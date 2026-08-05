"""Focused fake-HTTP contract test for the one-shot spot-check script."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "pairwise_compare.py"


class PairwiseCompareTests(unittest.TestCase):
    def test_http_error_body_is_private_and_public_surfaces_are_sanitized(self):
        secret_body = '{"error":{"message":"PRIVATE GATEWAY DIAGNOSIS"}}'

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                size = int(self.headers["Content-Length"])
                self.rfile.read(size)
                body = secret_body.encode()
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        private_log = ROOT.parent / ".tmp" / "test-pairwise-http-error-private.jsonl"
        private_log.unlink(missing_ok=True)
        try:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source, a, b, output = root / "source.md", root / "a.md", root / "b.md", root / "out.json"
                source.write_text("SOURCE FIXTURE")
                a.write_text("A FIXTURE")
                b.write_text("B FIXTURE")
                completed = subprocess.run(
                    [sys.executable, str(TOOL), "--source", str(source), "--summary-a", str(a), "--summary-b", str(b), "--output", str(output), "--private-log", str(private_log), "--zen-base-url", f"http://127.0.0.1:{server.server_port}/v1"],
                    cwd=ROOT,
                    env={"OPENCODE_API_KEY": "fixture-secret"},
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(completed.returncode, 1)
                public_result = output.read_text()
                private_audit = private_log.read_text()
        finally:
            private_log.unlink(missing_ok=True)
            server.shutdown()
            thread.join()
            server.server_close()
        private_rows = [json.loads(line) for line in private_audit.splitlines()]
        self.assertEqual([row["raw_response"] for row in private_rows], [secret_body] * 3)
        self.assertNotIn("PRIVATE GATEWAY DIAGNOSIS", public_result)
        self.assertNotIn("PRIVATE GATEWAY DIAGNOSIS", completed.stdout)
        self.assertNotIn("PRIVATE GATEWAY DIAGNOSIS", completed.stderr)

    def test_three_judges_use_documented_provider_paths_and_scores_are_aggregated(self):
        received: list[tuple[str, dict, dict[str, str]]] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                size = int(self.headers["Content-Length"])
                request = json.loads(self.rfile.read(size))
                received.append((self.path, request, dict(self.headers)))
                if request["model"] == "gpt-5.6-terra":
                    response = {"choices": [{"message": {"content": "A"}}]}
                elif request["model"] == "claude-sonnet-5":
                    response = {"choices": [{"message": {"content": "TIE"}}]}
                else:
                    response = {"choices": [{"message": {"content": "B"}}]}
                body = json.dumps(response).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source, a, b, output = root / "source.md", root / "a.md", root / "b.md", root / "out.json"
                source.write_text("SOURCE FIXTURE")
                a.write_text("A FIXTURE")
                b.write_text("B FIXTURE")
                completed = subprocess.run([sys.executable, str(TOOL), "--source", str(source), "--summary-a", str(a), "--summary-b", str(b), "--output", str(output), "--zen-base-url", f"http://127.0.0.1:{server.server_port}/v1"], cwd=ROOT, env={"OPENCODE_API_KEY": "fixture-secret"}, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                output_text = output.read_text()
                result = json.loads(output_text)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
        self.assertEqual([path for path, _request, _headers in received], ["/v1/chat/completions"] * 3)
        self.assertEqual([request["model"] for _path, request, _headers in received], ["gpt-5.6-terra", "claude-sonnet-5", "deepseek-v4-pro"])
        prompts = [request.get("input") or request["messages"][0]["content"] for _path, request, _headers in received]
        self.assertTrue(all("SOURCE FIXTURE" in prompt and "A FIXTURE" in prompt and "B FIXTURE" in prompt for prompt in prompts))
        self.assertTrue(all("non-inferiority test" in prompt for prompt in prompts))
        self.assertTrue(all("Default to TIE" in prompt for prompt in prompts))
        self.assertTrue(all("nuisance variables" in prompt for prompt in prompts))
        self.assertTrue(all("deployment-relevant material defect" in prompt for prompt in prompts))
        self.assertTrue(all("unsupported factual claim or hallucination" in prompt for prompt in prompts))
        self.assertTrue(all("Evaluate silently" in prompt for prompt in prompts))
        self.assertTrue(all("Anthropic-Version" not in headers for _path, _request, headers in received))
        self.assertTrue(all(headers.get("User-Agent") == "TurboFieldfare-Summarisation-Benchmark/1.0" for _path, _request, headers in received))
        self.assertEqual(result["aggregate"], {"score_a": 3, "score_b": 3, "verdict": "TIE"})
        self.assertNotIn("SOURCE FIXTURE", output_text)


if __name__ == "__main__":
    unittest.main()
