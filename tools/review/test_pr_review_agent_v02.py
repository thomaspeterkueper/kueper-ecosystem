from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("pr_review_agent_v02.py")
spec = importlib.util.spec_from_file_location("pr_review_agent_v02", MODULE_PATH)
assert spec and spec.loader
reviewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reviewer)


class ReviewJsonExtractionTests(unittest.TestCase):
    def test_ignores_leading_diagnostic_json(self):
        text = (
            '[claude-code:unrecognized_model] {"model":"deepseek-v4-pro[1m]","query_source":"sdk"}\n'
            '{"verdict":"PASS","summary":"ok","findings":[]}\n'
        )
        got = reviewer.extract_review_json(text)
        self.assertEqual(got["verdict"], "PASS")

    def test_accepts_trailing_json_and_text(self):
        text = (
            'prefix\n'
            '{"verdict":"CHANGES_REQUIRED","summary":"fix","findings":[{"x":1}]}\n'
            '{"diagnostic":true}\ntrailer'
        )
        got = reviewer.extract_review_json(text)
        self.assertEqual(got["verdict"], "CHANGES_REQUIRED")

    def test_rejects_only_diagnostics(self):
        with self.assertRaises(reviewer.base.worker.WorkerError):
            reviewer.extract_review_json('{"model":"x"}\n{"diagnostic":true}')


if __name__ == "__main__":
    unittest.main()
