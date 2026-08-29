#!/usr/bin/env python3
import unittest

from branch_hygiene import classify_branch, repositories

REPO = "thomaspeterkueper/kueper-ecosystem"
FORK = "someuser/kueper-ecosystem"


def pr(number, state, head_ref, base_ref="main", merged_at=None, head_repo=REPO, base_repo=REPO):
    return {
        "number": number,
        "state": state,
        "merged_at": merged_at,
        "head": {"ref": head_ref, "repo": {"full_name": head_repo}},
        "base": {"ref": base_ref, "repo": {"full_name": base_repo}},
    }


class BranchHygieneTests(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "always_review_prefixes": ["research/"],
            "ephemeral_prefixes": ["tmp-", "test/", "agent/", "ecosystem/task-"],
        }

    def test_default_branch_is_kept(self):
        self.assertEqual(classify_branch("main", "main", [], False, self.policy, REPO)[0], "KEEP")

    def test_open_pr_head_is_kept(self):
        prs = [pr(7, "open", "feat/x")]
        self.assertEqual(classify_branch("feat/x", "main", prs, False, self.policy, REPO)[0], "KEEP")

    def test_stacked_pr_base_is_kept(self):
        prs = [pr(8, "open", "feat/y", base_ref="feat/x")]
        self.assertEqual(classify_branch("feat/x", "main", prs, False, self.policy, REPO)[0], "KEEP")

    def test_merged_non_research_branch_is_delete_candidate(self):
        prs = [pr(9, "closed", "fix/x", merged_at="2026-08-29T00:00:00Z")]
        self.assertEqual(classify_branch("fix/x", "main", prs, False, self.policy, REPO)[0], "DELETE")

    def test_research_branch_stays_review_even_after_merge(self):
        prs = [pr(10, "closed", "research/x", merged_at="2026-08-29T00:00:00Z")]
        self.assertEqual(classify_branch("research/x", "main", prs, False, self.policy, REPO)[0], "REVIEW")

    def test_closed_unmerged_is_review(self):
        prs = [pr(11, "closed", "feat/z")]
        self.assertEqual(classify_branch("feat/z", "main", prs, False, self.policy, REPO)[0], "REVIEW")

    def test_merged_with_closed_unmerged_is_review(self):
        prs = [
            pr(5, "closed", "fix/x", merged_at="2026-08-29T00:00:00Z"),
            pr(12, "closed", "fix/x"),
        ]
        action, reason = classify_branch("fix/x", "main", prs, False, self.policy, REPO)
        self.assertEqual(action, "REVIEW")
        self.assertIn("#5", reason)
        self.assertIn("#12", reason)

    def test_fork_pr_head_ref_does_not_associate(self):
        # Merged fork PR whose head.ref collides with a scanned-repo branch name.
        prs = [pr(9, "closed", "fix/y", merged_at="2026-08-29T00:00:00Z", head_repo=FORK)]
        action, reason = classify_branch("fix/y", "main", prs, False, self.policy, REPO)
        self.assertEqual(action, "REVIEW")
        self.assertNotIn("#9", reason)

    def test_open_fork_pr_head_ref_does_not_keep(self):
        prs = [pr(13, "open", "feat/x", head_repo=FORK)]
        self.assertEqual(classify_branch("feat/x", "main", prs, False, self.policy, REPO)[0], "REVIEW")

    def test_fork_pr_base_keeps_branch(self):
        # A fork PR's base ref is in the scanned repo's namespace and still keeps the branch.
        prs = [pr(14, "open", "fork-change", base_ref="fix/x", head_repo=FORK)]
        self.assertEqual(classify_branch("fix/x", "main", prs, False, self.policy, REPO)[0], "KEEP")

    def test_registry_plus_private_metadata_extra(self):
        registry = {"projects": [{"repository": "a/main", "provider": "github", "enabled": True}]}
        policy = {"extra_repositories": ["a/private"], "excluded_repositories": []}
        self.assertEqual(repositories(registry, policy), ["a/main", "a/private"])


if __name__ == "__main__":
    unittest.main()
