#!/usr/bin/env python3
import unittest

from branch_hygiene import classify_branch, repositories


class BranchHygieneTests(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "always_review_prefixes": ["research/"],
            "ephemeral_prefixes": ["tmp-", "test/", "agent/", "ecosystem/task-"],
        }

    def test_default_branch_is_kept(self):
        self.assertEqual(classify_branch("main", "main", [], False, self.policy)[0], "KEEP")

    def test_open_pr_head_is_kept(self):
        prs = [{"number": 7, "state": "open", "head": {"ref": "feat/x"}, "base": {"ref": "main"}}]
        self.assertEqual(classify_branch("feat/x", "main", prs, False, self.policy)[0], "KEEP")

    def test_stacked_pr_base_is_kept(self):
        prs = [{"number": 8, "state": "open", "head": {"ref": "feat/y"}, "base": {"ref": "feat/x"}}]
        self.assertEqual(classify_branch("feat/x", "main", prs, False, self.policy)[0], "KEEP")

    def test_merged_non_research_branch_is_delete_candidate(self):
        prs = [{"number": 9, "state": "closed", "merged_at": "2026-08-29T00:00:00Z", "head": {"ref": "fix/x"}, "base": {"ref": "main"}}]
        self.assertEqual(classify_branch("fix/x", "main", prs, False, self.policy)[0], "DELETE")

    def test_research_branch_stays_review_even_after_merge(self):
        prs = [{"number": 10, "state": "closed", "merged_at": "2026-08-29T00:00:00Z", "head": {"ref": "research/x"}, "base": {"ref": "main"}}]
        self.assertEqual(classify_branch("research/x", "main", prs, False, self.policy)[0], "REVIEW")

    def test_closed_unmerged_is_review(self):
        prs = [{"number": 11, "state": "closed", "merged_at": None, "head": {"ref": "feat/z"}, "base": {"ref": "main"}}]
        self.assertEqual(classify_branch("feat/z", "main", prs, False, self.policy)[0], "REVIEW")

    def test_registry_plus_private_metadata_extra(self):
        registry = {"projects": [{"repository": "a/main", "provider": "github", "enabled": True}]}
        policy = {"extra_repositories": ["a/private"], "excluded_repositories": []}
        self.assertEqual(repositories(registry, policy), ["a/main", "a/private"])


if __name__ == "__main__":
    unittest.main()
