import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.loop import loop


class ParseTaskTests(unittest.TestCase):
    def test_frontmatter_execution_class_wins(self):
        text = """---
id: EXT-1
execution_class: A
priority: high
---
# Task
Execution Class: B
"""
        task = loop.parse_task(text, "EXT-1.md", "C")
        self.assertEqual(task["execution_class"], "A")
        self.assertEqual(task["priority"], "high")

    def test_legacy_execution_class_is_supported(self):
        task = loop.parse_task("# Task\nExecution Class: B\n", "task.md", "C")
        self.assertEqual(task["execution_class"], "B")

    def test_invalid_execution_class_falls_back_conservatively(self):
        task = loop.parse_task("# Task\nExecution Class: Z\n", "task.md", "C")
        self.assertEqual(task["execution_class"], "C")


class PreflightTests(unittest.TestCase):
    def _queue_file(self, observed_sha="abc"):
        tmp = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
        json.dump({"queue": [{"filename": "task.md", "repository": "owner/repo", "observed_head_sha": observed_sha}]}, tmp)
        tmp.close()
        self.addCleanup(lambda: os.unlink(tmp.name))
        return Path(tmp.name)

    @patch.object(loop, "token", return_value="test-token")
    @patch.object(loop, "repo_state")
    def test_preflight_allows_only_identical_nonempty_sha(self, repo_state, _token):
        repo_state.return_value = {"state": "ok", "head_sha": "abc"}
        result = loop.preflight(self._queue_file("abc"), 0)
        self.assertTrue(result["fresh"])
        self.assertEqual(result["action"], "eligible_for_dispatch")

    @patch.object(loop, "token", return_value="test-token")
    @patch.object(loop, "repo_state")
    def test_preflight_rejects_changed_sha(self, repo_state, _token):
        repo_state.return_value = {"state": "ok", "head_sha": "def"}
        result = loop.preflight(self._queue_file("abc"), 0)
        self.assertFalse(result["fresh"])
        self.assertEqual(result["action"], "rescan_and_replan")

    @patch.object(loop, "token", return_value="test-token")
    @patch.object(loop, "repo_state")
    def test_preflight_rejects_unreachable_or_missing_head(self, repo_state, _token):
        repo_state.return_value = {"state": "unreachable", "head_sha": None}
        result = loop.preflight(self._queue_file("abc"), 0)
        self.assertFalse(result["fresh"])
        self.assertEqual(result["action"], "rescan_and_replan")


if __name__ == "__main__":
    unittest.main()
