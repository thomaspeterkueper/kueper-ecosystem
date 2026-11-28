import base64, io, json, unittest, urllib.error
from unittest import mock

import cleanup_outbox as co


def _file(text):
    return {"type": "file", "content": base64.b64encode(text.encode()).decode(), "sha": "x"}


class RoutedFingerprintCacheTest(unittest.TestCase):
    def setUp(self):
        co.default.cache_clear()
        co._routed_fingerprints.cache_clear()

    def test_target_tasks_are_read_once_per_run(self):
        calls = []

        def fake_gh(token, method, path, body=None):
            calls.append((method, path))
            if path == "/repos/o/t":
                return {"default_branch": "main"}
            if "/contents/external-tasks/open?" in path:
                return [{"type": "file", "name": "a.md", "path": "external-tasks/open/a.md"}]
            if "/contents/external-tasks/open/a.md" in path:
                return _file("---\nrouting_fingerprint: abc123\n---\n")
            return None

        target = {"id": "noxia", "repository": "o/t"}
        with mock.patch.object(co, "gh", side_effect=fake_gh):
            for _ in range(5):
                self.assertIn("abc123", co.routed_fingerprints("tok", target))
        task_reads = [c for c in calls if c[1].startswith("/repos/o/t/contents/external-tasks/open/a.md")]
        self.assertEqual(len(task_reads), 1)
        self.assertEqual(len([c for c in calls if c[1] == "/repos/o/t"]), 1)


class RateLimitTest(unittest.TestCase):
    def setUp(self):
        co.default.cache_clear()
        co._routed_fingerprints.cache_clear()

    def _http_error(self, code, payload):
        return urllib.error.HTTPError(
            "https://api.github.com/x", code, "Forbidden", {}, io.BytesIO(payload.encode())
        )

    def test_rate_limit_body_is_classified(self):
        self.assertTrue(co._is_rate_limit(403, '{"message":"API rate limit exceeded for user ID 1."}'))
        self.assertTrue(co._is_rate_limit(429, '{"message":"You have exceeded a secondary rate limit."}'))

    def test_missing_permission_is_not_a_rate_limit(self):
        self.assertFalse(
            co._is_rate_limit(403, '{"message":"Resource not accessible by personal access token"}')
        )
        self.assertFalse(co._is_rate_limit(404, '{"message":"Not Found"}'))

    def test_gh_raises_rate_limited_for_exhausted_limit(self):
        error = self._http_error(403, '{"message":"API rate limit exceeded for user ID 1."}')
        with mock.patch.object(co.urllib.request, "urlopen", side_effect=error):
            with self.assertRaises(co.RateLimited):
                co.gh("tok", "GET", "/repos/o/t")

    def test_gh_keeps_plain_runtime_error_for_other_403(self):
        error = self._http_error(403, '{"message":"Resource not accessible by personal access token"}')
        with mock.patch.object(co.urllib.request, "urlopen", side_effect=error):
            with self.assertRaises(RuntimeError) as caught:
                co.gh("tok", "GET", "/repos/o/t")
        self.assertNotIsInstance(caught.exception, co.RateLimited)

    def test_main_stops_without_failing_and_reports_consumed_envelopes(self):
        deleted = []

        def fake_gh(token, method, path, body=None):
            if method == "DELETE":
                deleted.append(path)
                return None
            if "/contents/" not in path:
                return {"default_branch": "main"}
            if "/contents/.kueper/outbox?" in path:
                return [
                    {"type": "file", "name": "a.json", "path": ".kueper/outbox/a.json"},
                    {"type": "file", "name": "b.json", "path": ".kueper/outbox/b.json"},
                ]
            if "/contents/.kueper/outbox/" in path:
                return _file(json.dumps({"target": "OTA", "title": "t", "requested_change": "c"}))
            return None

        calls = {"n": 0}

        def fake_fingerprints(token, target):
            calls["n"] += 1
            if calls["n"] == 1:
                return frozenset({co.fp("ECO", "OTA", "t", "c")})
            raise co.RateLimited('{"message":"API rate limit exceeded for user ID 1."}')

        printed = []
        with mock.patch.object(co, "gh", side_effect=fake_gh), mock.patch.object(
            co, "routed_fingerprints", side_effect=fake_fingerprints
        ), mock.patch("builtins.print", side_effect=lambda *a, **k: printed.append(a[0])), mock.patch.dict(
            co.os.environ, {"KUEPER_BOT_TOKEN": "tok"}, clear=False
        ):
            self.assertEqual(co.main(), 0)

        report = json.loads(printed[-1])
        self.assertEqual(report["consumed"], 1)
        self.assertEqual(report["stopped"]["reason"], "rate-limit")
        self.assertEqual(len(deleted), 1)


if __name__ == "__main__":
    unittest.main()
