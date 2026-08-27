import unittest

from tools.review.direct_pr_intake import discover, intake, parse_pr_url


ECO_REPO = "thomaspeterkueper/kueper-ecosystem"
NOXIA_REPO = "thomaspeterkueper/noxiagame"
PROJECTS = {ECO_REPO: "ECO", NOXIA_REPO: "NOXIA"}


class FakeDb:
    def __init__(self):
        self.calls = []
        self.tasks = {}
        self.tasks_by_pr = {}

    def rpc(self, name, payload):
        self.calls.append((name, payload))
        if name == "kueper_get_task_for_pr":
            task = self.tasks_by_pr.get(payload["p_pr_url"])
            return dict(task) if task else None
        if name == "kueper_create_task":
            key = payload["p_idempotency_key"]
            if key not in self.tasks:
                self.tasks[key] = {
                    "id": f"task-{len(self.tasks) + 1}",
                    "type": payload["p_type"],
                    "status": "pending",
                    "repository": payload["p_repository"],
                    "target_project": payload["p_target_project"],
                }
            return dict(self.tasks[key])
        if name == "kueper_enqueue_direct_pr_review":
            for task in self.tasks.values():
                if task["id"] == payload["p_task_id"]:
                    task["status"] = "review_pending"
                    task["pr_url"] = payload["p_pr_url"]
                    self.tasks_by_pr[payload["p_pr_url"]] = task
                    return dict(task)
        raise AssertionError(f"unexpected RPC {name}")


class DirectPrIntakeTests(unittest.TestCase):
    def test_parses_canonical_pr_url(self):
        self.assertEqual(
            parse_pr_url(f"https://github.com/{ECO_REPO}/pull/30"),
            (ECO_REPO, 30),
        )

    def test_rejects_non_pr_url(self):
        with self.assertRaises(ValueError):
            parse_pr_url(f"https://github.com/{ECO_REPO}/issues/30")

    def test_routes_non_eco_repository_from_registry(self):
        db = FakeDb()
        result = intake(db, f"https://github.com/{NOXIA_REPO}/pull/10", repository_projects=PROJECTS)
        self.assertEqual(result["target_project"], "NOXIA")
        create = next(payload for name, payload in db.calls if name == "kueper_create_task")
        self.assertEqual(create["p_source_project"], "ECO")
        self.assertEqual(create["p_target_project"], "NOXIA")
        self.assertEqual(create["p_priority"], "medium")

    def test_rejects_repository_missing_from_registry(self):
        with self.assertRaises(ValueError):
            intake(FakeDb(), "https://github.com/example/unregistered/pull/1", repository_projects=PROJECTS)

    def test_duplicate_intake_is_idempotent(self):
        db = FakeDb()
        url = f"https://github.com/{ECO_REPO}/pull/30"
        first = intake(db, url, repository_projects=PROJECTS)
        second = intake(db, url, repository_projects=PROJECTS)
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(db.tasks), 1)
        self.assertEqual(second["status"], "review_pending")

    def test_existing_agent_task_prevents_duplicate_review_task(self):
        db = FakeDb()
        url = f"https://github.com/{NOXIA_REPO}/pull/10"
        db.tasks_by_pr[url] = {
            "id": "origin-task",
            "type": "IMPLEMENT_EXTERNAL_REQUIREMENT",
            "status": "review_pending",
            "pr_url": url,
            "repository": NOXIA_REPO,
            "target_project": "NOXIA",
        }
        result = intake(db, url, repository_projects=PROJECTS)
        self.assertEqual(result["id"], "origin-task")
        self.assertFalse(any(name == "kueper_create_task" for name, _ in db.calls))

    def test_discovery_scans_registry_and_routes_each_repository(self):
        db = FakeDb()

        def fake_fetch(repository, token):
            self.assertEqual(token, "token")
            number = 10 if repository == NOXIA_REPO else 30
            return [{"html_url": f"https://github.com/{repository}/pull/{number}"}]

        result = discover(db, "token", repository_projects=PROJECTS, fetch_open_prs=fake_fetch)
        self.assertEqual(len(result), 2)
        targets = {payload["p_repository"]: payload["p_target_project"] for name, payload in db.calls if name == "kueper_create_task"}
        self.assertEqual(targets[ECO_REPO], "ECO")
        self.assertEqual(targets[NOXIA_REPO], "NOXIA")


if __name__ == "__main__":
    unittest.main()
