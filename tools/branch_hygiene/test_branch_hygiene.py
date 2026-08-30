#!/usr/bin/env python3
import unittest

from branch_hygiene import classify_branch, repositories

REPO = "thomaspeterkueper/kueper-ecosystem"
FORK = "someuser/kueper-ecosystem"
BRANCH_SHA = "a" * 40
OTHER_SHA = "b" * 40


def pr(number, state, head_ref, base_ref="main", merged_at=None, head_repo=REPO, base_repo=REPO, head_sha=BRANCH_SHA):
    return {
        "number": number,
        "state": state,
        "merged_at": merged_at,
        "head": {"ref": head_ref, "sha": head_sha, "repo": {"full_name": head_repo}},
        "base": {"ref": base_ref, "repo": {"full_name": base_repo}},
    }


class BranchHygieneTests(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "always_review_prefixes": ["research/"],
            "ephemeral_prefixes": ["tmp-", "test/", "agent/", "ecosystem/task-"],
        }

    def classify(self, branch, prs, *, branch_sha=BRANCH_SHA, default="main", protected=False):
        return classify_branch(branch, branch_sha, default, prs, protected, self.policy, REPO)

    def test_default_branch_is_kept(self):
        self.assertEqual(self.classify("main", [])[0], "KEEP")

    def test_protected_branch_is_kept(self):
        self.assertEqual(self.classify("release", [], protected=True)[0], "KEEP")

    def test_open_pr_head_is_kept(self):
        self.assertEqual(self.classify("feat/x", [pr(7, "open", "feat/x")])[0], "KEEP")

    def test_stacked_pr_base_is_kept(self):
        self.assertEqual(self.classify("feat/x", [pr(8, "open", "feat/y", base_ref="feat/x")])[0], "KEEP")

    def test_merged_exact_head_sha_is_delete_candidate(self):
        prs = [pr(9, "closed", "fix/x", merged_at="2026-08-29T00:00:00Z", head_sha=BRANCH_SHA)]
        action, reason = self.classify("fix/x", prs, branch_sha=BRANCH_SHA)
        self.assertEqual(action, "DELETE_CANDIDATE")
        self.assertIn("exactly matches", reason)

    def test_branch_moved_after_merge_is_review(self):
        prs = [pr(9, "closed", "fix/x", merged_at="2026-08-29T00:00:00Z", head_sha=BRANCH_SHA)]
        action, reason = self.classify("fix/x", prs, branch_sha=OTHER_SHA)
        self.assertEqual(action, "REVIEW")
        self.assertIn("may have moved", reason)

    def test_missing_current_sha_is_review(self):
        prs = [pr(9, "closed", "fix/x", merged_at="2026-08-29T00:00:00Z", head_sha=BRANCH_SHA)]
        self.assertEqual(self.classify("fix/x", prs, branch_sha=None)[0], "REVIEW")

    def test_research_branch_stays_review_even_after_merge(self):
        prs = [pr(10, "closed", "research/x", merged_at="2026-08-29T00:00:00Z")]
        self.assertEqual(self.classify("research/x", prs)[0], "REVIEW")

    def test_closed_unmerged_is_review(self):
        self.assertEqual(self.classify("feat/z", [pr(11, "closed", "feat/z")])[0], "REVIEW")

    def test_merged_with_closed_unmerged_is_review(self):
        prs = [
            pr(5, "closed", "fix/x", merged_at="2026-08-29T00:00:00Z"),
            pr(12, "closed", "fix/x"),
        ]
        action, reason = self.classify("fix/x", prs)
        self.assertEqual(action, "REVIEW")
        self.assertIn("#5", reason)
        self.assertIn("#12", reason)

    def test_fork_pr_head_ref_does_not_associate(self):
        prs = [pr(9, "closed", "fix/y", merged_at="2026-08-29T00:00:00Z", head_repo=FORK)]
        action, reason = self.classify("fix/y", prs)
        self.assertEqual(action, "REVIEW")
        self.assertNotIn("#9", reason)

    def test_open_fork_pr_head_ref_does_not_keep(self):
        self.assertEqual(self.classify("feat/x", [pr(13, "open", "feat/x", head_repo=FORK)])[0], "REVIEW")

    def test_fork_pr_base_keeps_branch(self):
        prs = [pr(14, "open", "fork-change", base_ref="fix/x", head_repo=FORK)]
        self.assertEqual(self.classify("fix/x", prs)[0], "KEEP")

    def test_registry_plus_private_metadata_extra(self):
        registry = {"projects": [{"repository": "a/main", "provider": "github", "enabled": True}]}
        policy = {"extra_repositories": ["a/private"], "excluded_repositories": []}
        self.assertEqual(repositories(registry, policy), ["a/main", "a/private"])


if __name__ == "__main__":
    unittest.main()
