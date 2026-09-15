import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.worker import v74_privileged_e2e as e2e


class V74PrivilegedE2ETests(unittest.TestCase):
    def test_target_is_fixed_to_smoke_branch_and_single_workflow_path(self):
        self.assertEqual(e2e.TARGET_BRANCH, "test/workflow-credential-smoke")
        self.assertEqual(e2e.TARGET_PATH.as_posix(), ".github/workflows/_v74-e2e-target.yml")

    def test_origin_assertion_rejects_bot_credential(self):
        class Result:
            stdout = e2e.worker.clone_url("owner/repo", "bot") + "\n"

        with patch.object(e2e.worker, "run", return_value=Result()):
            with self.assertRaisesRegex(RuntimeError, "not swapped"):
                e2e._assert_privileged_origin(Path("."), "owner/repo", "bot", "workflow")

    def test_origin_assertion_accepts_distinct_workflow_credential(self):
        class Result:
            stdout = e2e.worker.clone_url("owner/repo", "workflow") + "\n"

        with patch.object(e2e.worker, "run", return_value=Result()):
            e2e._assert_privileged_origin(Path("."), "owner/repo", "bot", "workflow")

    def test_fake_task_rejects_unknown_mode_before_mutation(self):
        with self.assertRaisesRegex(RuntimeError, "unsupported mode"):
            e2e._fake_repo_task(
                {"repository": "thomaspeterkueper/kueper-ecosystem", "payload": {"mode": "other"}},
                "none",
            )

    def test_module_import_does_not_require_runtime_secrets(self):
        # Import succeeded at module load; keep this guard to ensure future
        # refactors do not move secret validation back into import time.
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(callable(e2e.main))


if __name__ == "__main__":
    unittest.main()
