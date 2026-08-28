import unittest

from tools.worker.git_credentials import (
    PrivilegedCredentialMissing,
    is_privileged_workflow_change,
    select_push_token,
)


class GitCredentialSelectionTests(unittest.TestCase):
    def test_normal_change_uses_bot_token(self):
        token, privileged = select_push_token(
            ["tools/worker/agent_worker_v73.py"],
            bot_token="bot",
            workflow_token=None,
        )
        self.assertEqual(token, "bot")
        self.assertFalse(privileged)

    def test_workflow_change_requires_dedicated_token(self):
        with self.assertRaises(PrivilegedCredentialMissing):
            select_push_token(
                [".github/workflows/agent-worker-v7.yml"],
                bot_token="bot",
                workflow_token=None,
            )

    def test_workflow_change_uses_dedicated_token(self):
        token, privileged = select_push_token(
            ["README.md", ".github/workflows/agent-worker-v7.yml"],
            bot_token="bot",
            workflow_token="workflow",
        )
        self.assertEqual(token, "workflow")
        self.assertTrue(privileged)

    def test_windows_style_path_is_privileged(self):
        self.assertTrue(is_privileged_workflow_change([r".github\workflows\x.yml"]))


if __name__ == "__main__":
    unittest.main()
