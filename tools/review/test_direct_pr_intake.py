import unittest

from tools.review.direct_pr_intake import intake, parse_pr_url


class FakeDb:
    def __init__(self):
        self.calls = []

    def rpc(self, name, payload):
        self.calls.append((name, payload))
        if name == "kueper_create_task":
            return {"id": "11111111-1111-1111-1111-111111111111", "status": "pending"}
        if name == "kueper_enqueue_direct_pr_review":
            return {
                "id": payload["p_task_id"],
                "status": "review_pending",
                "pr_url": payload["p_pr_url"],
                "repository": payload["p_repository"],
            }
        raise AssertionError(f"unexpected RPC {name}")


class DirectPrIntakeTests(unittest.TestCase):
    def test_parses_canonical_pr_url(self):
        self.assertEqual(
            parse_pr_url("https://github.com/thomaspeterkueper/kueper-ecosystem/pull/30"),
            ("thomaspeterkueper/kueper-ecosystem", 30),
        )

    def test_rejects_non_pr_url(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/thomaspeterkueper/kueper-ecosystem/issues/30")

    def test_intake_uses_dedicated_enqueue_rpc_and_medium_priority(self):
        db = FakeDb()
        result = intake(db, "https://github.com/thomaspeterkueper/kueper-ecosystem/pull/30")
        self.assertEqual(result["status"], "review_pending")
        self.assertEqual([name for name, _ in db.calls], [
            "kueper_create_task",
            "kueper_enqueue_direct_pr_review",
        ])
        create = db.calls[0][1]
        self.assertEqual(create["p_priority"], "medium")
        enqueue = db.calls[1][1]
        self.assertEqual(enqueue["p_repository"], "thomaspeterkueper/kueper-ecosystem")
        self.assertEqual(enqueue["p_pr_url"], "https://github.com/thomaspeterkueper/kueper-ecosystem/pull/30")


if __name__ == "__main__":
    unittest.main()
