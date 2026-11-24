import base64, json, unittest
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


if __name__ == "__main__":
    unittest.main()
