import unittest

from tools.review.direct_pr_intake_v02 import intake

ECO_REPO = "thomaspeterkueper/kueper-ecosystem"
PROJECTS = {ECO_REPO: "ECO"}
OLD_SHA = "1" * 40
NEW_SHA = "2" * 40


class FakeDb:
    def __init__(self, task):
        self.task = task
        self.calls = []

    def rpc(self, name, payload):
        self.calls.append((name, payload))
        if name == "kueper_get_task_for_pr":
            return dict(self.task) if self.task else None
        if name == "kueper_note_open_pr_head":
            self.task.setdefault("metadata", {})["discovered_pr_head_sha"] = payload["p_head_sha"]
            return dict(self.task)
        raise AssertionError(f"unexpected RPC {name}")


class DirectPrIntakeV02Tests(unittest.TestCase):
    def test_review_pending_direct_task_records_current_head(self):
        url = f"https://github.com/{ECO_REPO}/pull/37"
        db = FakeDb({
            "id": "task-37",
            "type": "PR_REVIEW",
            "status": "review_pending",
            "repository": ECO_REPO,
            "pr_url": url,
            "metadata": {},
        })
        result = intake(db, url, repository_projects=PROJECTS, head_sha=NEW_SHA)
        self.assertEqual(result["metadata"]["discovered_pr_head_sha"], NEW_SHA)
        self.assertTrue(any(name == "kueper_note_open_pr_head" for name, _ in db.calls))

    def test_review_pending_agent_task_records_changed_head_without_duplicate_task(self):
        url = f"https://github.com/{ECO_REPO}/pull/3"
        db = FakeDb({
            "id": "origin-task",
            "type": "IMPLEMENT_EXTERNAL_REQUIREMENT",
            "status": "review_pending",
            "repository": ECO_REPO,
            "pr_url": url,
            "metadata": {"discovered_pr_head_sha": OLD_SHA},
        })
        result = intake(db, url, repository_projects=PROJECTS, head_sha=NEW_SHA)
        self.assertEqual(result["id"], "origin-task")
        self.assertEqual(result["metadata"]["discovered_pr_head_sha"], NEW_SHA)
        self.assertFalse(any(name == "kueper_create_task" for name, _ in db.calls))

    def test_missing_head_does_not_call_head_rpc(self):
        url = f"https://github.com/{ECO_REPO}/pull/37"
        db = FakeDb({
            "id": "task-37",
            "type": "PR_REVIEW",
            "status": "review_pending",
            "repository": ECO_REPO,
            "pr_url": url,
            "metadata": {},
        })
        result = intake(db, url, repository_projects=PROJECTS)
        self.assertEqual(result["id"], "task-37")
        self.assertFalse(any(name == "kueper_note_open_pr_head" for name, _ in db.calls))


if __name__ == "__main__":
    unittest.main()
