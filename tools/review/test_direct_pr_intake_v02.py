import unittest

from tools.review.direct_pr_intake_v02 import discover, intake

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
            if self.task.get("status") == "cancelled":
                self.task["status"] = "review_pending"
                self.task.setdefault("metadata", {}).pop("pr_terminal_state", None)
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

    def test_reopened_cancelled_pr_is_reactivated_by_open_head_discovery(self):
        url = f"https://github.com/{ECO_REPO}/pull/45"
        db = FakeDb({
            "id": "task-45",
            "type": "PR_REVIEW",
            "status": "cancelled",
            "repository": ECO_REPO,
            "pr_url": url,
            "metadata": {"pr_terminal_state": "CLOSED"},
        })

        result = intake(db, url, repository_projects=PROJECTS, head_sha=NEW_SHA)

        self.assertEqual(result["id"], "task-45")
        self.assertEqual(result["status"], "review_pending")
        self.assertEqual(result["metadata"]["discovered_pr_head_sha"], NEW_SHA)
        self.assertNotIn("pr_terminal_state", result["metadata"])

    def test_missing_v02_rpc_falls_back_to_v01_task(self):
        url = f"https://github.com/{ECO_REPO}/pull/44"

        class PreMigrationDb(FakeDb):
            def rpc(self, name, payload):
                if name == "kueper_note_open_pr_head":
                    self.calls.append((name, payload))
                    raise RuntimeError(
                        "PGRST202: Could not find the function public.kueper_note_open_pr_head in the schema cache"
                    )
                return super().rpc(name, payload)

        db = PreMigrationDb({
            "id": "task-44",
            "type": "PR_REVIEW",
            "status": "review_pending",
            "repository": ECO_REPO,
            "pr_url": url,
            "metadata": {},
        })
        result = intake(db, url, repository_projects=PROJECTS, head_sha=NEW_SHA)
        self.assertEqual(result["id"], "task-44")
        self.assertNotIn("discovered_pr_head_sha", result["metadata"])
        self.assertTrue(any(name == "kueper_note_open_pr_head" for name, _ in db.calls))

    def test_non_deployment_head_rpc_error_still_fails(self):
        url = f"https://github.com/{ECO_REPO}/pull/44"

        class BadDataDb(FakeDb):
            def rpc(self, name, payload):
                if name == "kueper_note_open_pr_head":
                    raise RuntimeError("task is not an active/completed review task for this PR")
                return super().rpc(name, payload)

        db = BadDataDb({
            "id": "task-44",
            "type": "PR_REVIEW",
            "status": "review_pending",
            "repository": ECO_REPO,
            "pr_url": url,
            "metadata": {},
        })
        with self.assertRaisesRegex(RuntimeError, "not an active/completed review task"):
            intake(db, url, repository_projects=PROJECTS, head_sha=NEW_SHA)

    def test_discover_records_error_entry_and_continues_per_pr(self):
        # A review_pending task whose head-note RPC fails (e.g. a legacy row
        # created before repository tracking) must be recorded as an error entry
        # while discovery keeps processing the remaining PRs. Aborting the whole
        # batch would starve the review queue.
        url_bad = f"https://github.com/{ECO_REPO}/pull/31"
        url_ok = f"https://github.com/{ECO_REPO}/pull/37"
        head_sha = NEW_SHA

        class FailingHeadDb:
            def __init__(self):
                self.calls = []

            def rpc(self, name, payload):
                self.calls.append((name, payload))
                if name == "kueper_get_task_for_pr":
                    return {
                        "id": "task-31",
                        "type": "PR_REVIEW",
                        "status": "review_pending",
                        "repository": None,
                        "pr_url": payload["p_pr_url"],
                        "metadata": {},
                    }
                if name == "kueper_note_open_pr_head":
                    if payload["p_pr_url"] == url_bad:
                        raise RuntimeError("task is not an active/completed review task for this PR")
                    return {
                        "id": "task-37",
                        "type": "PR_REVIEW",
                        "status": "review_pending",
                        "repository": ECO_REPO,
                        "pr_url": url_ok,
                        "metadata": {"discovered_pr_head_sha": head_sha},
                    }
                raise AssertionError(f"unexpected RPC {name}")

        def fetch(repository, token):
            return [
                {"html_url": url_bad, "head": {"sha": head_sha}},
                {"html_url": url_ok, "head": {"sha": head_sha}},
            ]

        results = discover(
            FailingHeadDb(),
            "token",
            repository_projects=PROJECTS,
            fetch_open_prs=fetch,
        )
        self.assertEqual(len(results), 2)
        error_entry = next(r for r in results if r["pr_url"] == url_bad)
        self.assertEqual(error_entry["status"], "error")
        self.assertIn("not an active/completed review task", error_entry["error"])
        ok_entry = next(r for r in results if r["pr_url"] == url_ok)
        self.assertEqual(ok_entry["status"], "review_pending")
        self.assertEqual(ok_entry["task_id"], "task-37")


if __name__ == "__main__":
    unittest.main()
