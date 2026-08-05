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
    def test_three_judges_receive_the_same_two_candidates_and_scores_are_aggregated(self):
        received: list[dict] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                size = int(self.headers["Content-Length"])
                received.append(json.loads(self.rfile.read(size)))
                body = json.dumps({"choices": [{"message": {"content": "A"}}]}).encode()
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
                completed = subprocess.run([sys.executable, str(TOOL), "--source", str(source), "--summary-a", str(a), "--summary-b", str(b), "--output", str(output), "--endpoint", f"http://127.0.0.1:{server.server_port}/v1/chat/completions"], cwd=ROOT, env={"OPENCODE_API_KEY": "fixture-secret"}, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                output_text = output.read_text()
                result = json.loads(output_text)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
        self.assertEqual([request["model"] for request in received], ["gpt-5.6-terra", "claude-sonnet-5", "kimi-k3"])
        self.assertTrue(all("SOURCE FIXTURE" in request["messages"][0]["content"] and "A FIXTURE" in request["messages"][0]["content"] and "B FIXTURE" in request["messages"][0]["content"] for request in received))
        self.assertEqual(result["aggregate"], {"score_a": 6, "score_b": 0, "verdict": "A"})
        self.assertNotIn("SOURCE FIXTURE", output_text)


if __name__ == "__main__":
    unittest.main()
