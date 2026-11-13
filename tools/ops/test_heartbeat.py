"""Tests für tools/ops/heartbeat.sh – lokaler HTTP-Server statt echtem Dienst."""
import http.server
import os
import subprocess
import threading
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "heartbeat.sh")


class _Handler(http.server.BaseHTTPRequestHandler):
    paths = []

    def do_GET(self):  # noqa: N802
        _Handler.paths.append(self.path)
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


def run(args, extra_env=None):
    env = {"PATH": os.environ.get("PATH", "")}
    env.update(extra_env or {})
    return subprocess.run(["bash", SCRIPT, *args], env=env, capture_output=True, text=True, timeout=30)


class HeartbeatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}/hb/abc"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        _Handler.paths.clear()

    def test_missing_variable_is_noop(self):
        r = run(["HEARTBEAT_AGENT"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("übersprungen", r.stdout)
        self.assertEqual(_Handler.paths, [])

    def test_success_ping(self):
        r = run(["HEARTBEAT_AGENT"], {"HEARTBEAT_AGENT": self.base})
        self.assertEqual(r.returncode, 0)
        self.assertEqual(_Handler.paths, ["/hb/abc"])

    def test_fail_ping(self):
        run(["HEARTBEAT_AGENT", "fail"], {"HEARTBEAT_AGENT": self.base + "/"})
        self.assertEqual(_Handler.paths, ["/hb/abc/fail"])

    def test_url_never_printed(self):
        r = run(["HEARTBEAT_AGENT"], {"HEARTBEAT_AGENT": self.base})
        self.assertNotIn("127.0.0.1", r.stdout + r.stderr)

    def test_unreachable_does_not_fail(self):
        r = run(["HEARTBEAT_AGENT"], {"HEARTBEAT_AGENT": "http://127.0.0.1:9/x"})
        self.assertEqual(r.returncode, 0)

    def test_invalid_name_rejected(self):
        r = run(["$(touch /tmp/x)"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("ungültig", r.stderr)


if __name__ == "__main__":
    unittest.main()
