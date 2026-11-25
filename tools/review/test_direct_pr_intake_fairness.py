import unittest

from tools.review.direct_pr_intake_v02 import HOLD_LABEL, discover

A = "thomaspeterkueper/a-repo"
Z = "thomaspeterkueper/z-repo"


class RecordingDb:
    def __init__(self):
        self.seen = []

    def rpc(self, name, payload):
        if name == "kueper_get_task_for_pr":
            self.seen.append(payload["p_pr_url"])
            return {"id": payload["p_pr_url"], "status": "review_pending", "type": "PR_REVIEW"}
        if name == "kueper_note_open_pr_head":
            return {"id": payload["p_pr_url"], "status": "review_pending", "type": "PR_REVIEW"}
        raise AssertionError(name)


def prs(repo, count, labels=None):
    return [{"html_url": f"https://github.com/{repo}/pull/{n}",
             "head": {"sha": f"{n:040x}"},
             "labels": labels or []} for n in range(1, count + 1)]


class FairnessTests(unittest.TestCase):
    def test_cap_does_not_starve_later_repositories(self):
        db = RecordingDb()
        data = {A: prs(A, 60), Z: prs(Z, 3)}
        discover(db, "t", repository_projects={A: "A", Z: "Z"},
                 fetch_open_prs=lambda repo, token: data[repo], max_prs=6)
        self.assertEqual(len(db.seen), 6)
        self.assertEqual(sum(1 for url in db.seen if Z in url), 3)

    def test_hold_label_is_skipped_and_reported(self):
        db = RecordingDb()
        data = {A: prs(A, 2, labels=[{"name": HOLD_LABEL}]) + prs(A, 3)[2:]}
        result = discover(db, "t", repository_projects={A: "A"},
                          fetch_open_prs=lambda repo, token: data[repo], max_prs=10)
        self.assertEqual([r["status"] for r in result].count("skipped-hold"), 2)
        self.assertEqual(db.seen, [f"https://github.com/{A}/pull/3"])

    def test_hold_label_match_ignores_case(self):
        db = RecordingDb()
        data = {A: prs(A, 1, labels=[{"name": "KUEPER-Hold"}])}
        result = discover(db, "t", repository_projects={A: "A"},
                          fetch_open_prs=lambda repo, token: data[repo])
        self.assertEqual(result[0]["status"], "skipped-hold")
        self.assertEqual(db.seen, [])

    def test_malformed_row_does_not_consume_budget(self):
        db = RecordingDb()
        data = {A: [{"html_url": "", "head": {}}] + prs(A, 2)}
        discover(db, "t", repository_projects={A: "A"},
                 fetch_open_prs=lambda repo, token: data[repo], max_prs=2)
        self.assertEqual(len(db.seen), 2)

    def test_unreachable_repository_does_not_abort_discovery(self):
        db = RecordingDb()

        def fetch(repo, token):
            if repo == A:
                raise RuntimeError("HTTP 403")
            return prs(Z, 1)

        result = discover(db, "t", repository_projects={A: "A", Z: "Z"}, fetch_open_prs=fetch)
        self.assertEqual(result[0]["status"], "error")
        self.assertEqual(db.seen, [f"https://github.com/{Z}/pull/1"])


if __name__ == "__main__":
    unittest.main()
