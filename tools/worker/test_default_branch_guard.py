import unittest

from tools.worker.default_branch_guard import (
    DefaultBranchMutationBlocked,
    assert_no_merge_substitute,
    assert_non_default_branch,
)


class DefaultBranchGuardTests(unittest.TestCase):
    def test_agent_branch_is_allowed(self):
        assert_non_default_branch("ecosystem/task-12345678", "main", context="publish")

    def test_default_branch_write_is_blocked(self):
        with self.assertRaises(DefaultBranchMutationBlocked):
            assert_non_default_branch("main", "main", context="publish")

    def test_draft_pr_ready_unavailable_cannot_fall_back_to_main(self):
        with self.assertRaisesRegex(DefaultBranchMutationBlocked, "keep the PR open"):
            assert_no_merge_substitute(
                pr_state="OPEN",
                is_draft=True,
                ready_or_merge_available=False,
                target_branch="main",
                default_branch="main",
                context="review lifecycle",
            )

    def test_blocked_ready_still_allows_pr_head_update(self):
        assert_no_merge_substitute(
            pr_state="OPEN",
            is_draft=True,
            ready_or_merge_available=False,
            target_branch="ecosystem/task-12345678",
            default_branch="main",
            context="review lifecycle",
        )


if __name__ == "__main__":
    unittest.main()
