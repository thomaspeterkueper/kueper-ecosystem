"""Deterministic regression tests for the fail-closed external-check merge gate.

Covers the acceptance cases of NOXIA-ECO-20260831-merge-gate-required-checks:

- review-approved PR, Vercel green, Supabase Migrations failed  -> no merge;
- required check missing                                       -> no merge;
- check result belongs to an older head                        -> no merge;
- all required checks green on the current head                -> merge may proceed.

Plus the remaining fail-closed matrix (incomplete/neutral/ambiguous results,
unknown check ids, missing/invalid policy, truncated evidence) and wiring
assertions for the registry and the loop's merge invocation.
"""
import importlib.util
import pathlib
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("merge_gate", HERE / "merge_gate.py")
merge_gate = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(merge_gate)

HEAD = "a" * 40
OLD_HEAD = "b" * 40

NOXIA_POLICY = {
    "mode": "fail-closed",
    "required": ["vercel", "supabase-preview", "supabase-migrations"],
}


def run(name, conclusion, status="completed", app_slug=None, head_sha=HEAD):
    return {"name": name, "conclusion": conclusion, "status": status, "app_slug": app_slug, "head_sha": head_sha}


def status(context, state, head_sha=HEAD):
    return {"context": context, "state": state, "head_sha": head_sha}


def evidence(*, check_runs=None, statuses=None, head_sha=HEAD, truncated=False):
    return {
        "head_sha": head_sha,
        "check_runs": check_runs or [],
        "statuses": statuses or [],
        "truncated": truncated,
    }


def noxia_evidence(migrations=("success", "completed"), preview=("success", "completed"),
                    vercel="success", head_sha=HEAD, truncated=False):
    return evidence(
        check_runs=[
            run("Migrations", migrations[0], migrations[1], app_slug="supabase", head_sha=head_sha),
            run("Preview Branch", preview[0], preview[1], app_slug="supabase", head_sha=head_sha),
            run("Vercel", vercel, head_sha=head_sha),
        ],
        head_sha=head_sha,
        truncated=truncated,
    )


class MergeGateEvaluationTests(unittest.TestCase):
    def test_observed_regression_migrations_failed_blocks_merge(self):
        # Review-approved and mergeable PR; Vercel green; Supabase Migrations failed.
        decision = merge_gate.evaluate(
            NOXIA_POLICY, noxia_evidence(migrations=("failure", "completed")), HEAD
        )
        self.assertFalse(decision["allowed"])
        states = {c["id"]: c["state"] for c in decision["checks"]}
        self.assertEqual(states["vercel"], "success")
        self.assertEqual(states["supabase-preview"], "success")
        self.assertEqual(states["supabase-migrations"], "failed")
        self.assertTrue(any("supabase-migrations" in r and "failed" in r for r in decision["blocking_reasons"]))

    def test_missing_required_check_blocks_merge(self):
        # No supabase-preview result at all -> must not count as green.
        decision = merge_gate.evaluate(
            NOXIA_POLICY,
            evidence(check_runs=[
                run("Vercel", "success"),
                run("Migrations", "success", app_slug="supabase"),
            ]),
            HEAD,
        )
        self.assertFalse(decision["allowed"])
        states = {c["id"]: c["state"] for c in decision["checks"]}
        self.assertEqual(states["supabase-preview"], "missing")

    def test_old_head_results_do_not_count(self):
        # All checks green, but for the previous head -> blocked for the current head.
        decision = merge_gate.evaluate(NOXIA_POLICY, noxia_evidence(head_sha=OLD_HEAD), HEAD)
        self.assertFalse(decision["allowed"])
        self.assertTrue(any("belongs to head" in r for r in decision["blocking_reasons"]))

    def test_all_required_checks_green_current_head_allows_merge(self):
        decision = merge_gate.evaluate(NOXIA_POLICY, noxia_evidence(), HEAD)
        self.assertTrue(decision["allowed"])
        self.assertTrue(all(c["state"] == "success" for c in decision["checks"]))
        self.assertEqual(decision["blocking_reasons"], [])

    def test_vercel_via_commit_status_succeeds(self):
        decision = merge_gate.evaluate(
            NOXIA_POLICY,
            evidence(
                check_runs=[
                    run("Migrations", "success", app_slug="supabase"),
                    run("Preview Branch", "success", app_slug="supabase"),
                ],
                statuses=[status("Vercel", "success")],
            ),
            HEAD,
        )
        self.assertTrue(decision["allowed"])

    def test_vercel_failed_status_blocks_merge(self):
        decision = merge_gate.evaluate(
            NOXIA_POLICY,
            evidence(
                check_runs=[
                    run("Migrations", "success", app_slug="supabase"),
                    run("Preview Branch", "success", app_slug="supabase"),
                ],
                statuses=[status("Vercel", "failure")],
            ),
            HEAD,
        )
        self.assertFalse(decision["allowed"])
        self.assertTrue(any(c["id"] == "vercel" and c["state"] == "failed" for c in decision["checks"]))

    def test_unknown_required_check_blocks_merge(self):
        decision = merge_gate.evaluate(
            {"mode": "fail-closed", "required": ["vercel", "no-such-check"]},
            evidence(check_runs=[run("Vercel", "success")]),
            HEAD,
        )
        self.assertFalse(decision["allowed"])
        self.assertTrue(any(c["state"] == "unknown" for c in decision["checks"]))

    def test_incomplete_required_check_blocks_merge(self):
        decision = merge_gate.evaluate(
            NOXIA_POLICY, noxia_evidence(migrations=("failure", "in_progress")), HEAD
        )
        # in_progress with no conclusion must not count as failed; blocked as incomplete.
        self.assertFalse(decision["allowed"])
        states = {c["id"]: c["state"] for c in decision["checks"]}
        self.assertEqual(states["supabase-migrations"], "incomplete")

    def test_neutral_conclusion_blocks_merge(self):
        decision = merge_gate.evaluate(
            NOXIA_POLICY, noxia_evidence(migrations=("neutral", "completed")), HEAD
        )
        self.assertFalse(decision["allowed"])
        self.assertTrue(any(c["id"] == "supabase-migrations" and c["state"] == "failed" for c in decision["checks"]))

    def test_completed_without_conclusion_blocks_merge(self):
        decision = merge_gate.evaluate(
            NOXIA_POLICY, noxia_evidence(migrations=(None, "completed")), HEAD
        )
        self.assertFalse(decision["allowed"])
        self.assertTrue(any(c["id"] == "supabase-migrations" and c["state"] == "failed" for c in decision["checks"]))

    def test_conflicting_results_block_merge(self):
        decision = merge_gate.evaluate(
            NOXIA_POLICY,
            evidence(check_runs=[
                run("Vercel", "success"),
                run("Preview Branch", "success", app_slug="supabase"),
                run("Migrations", "success", app_slug="supabase"),
                run("Migrations", "failure", app_slug="supabase"),
            ]),
            HEAD,
        )
        self.assertFalse(decision["allowed"])
        self.assertTrue(any(c["id"] == "supabase-migrations" and c["state"] == "failed" for c in decision["checks"]))

    def test_check_run_for_other_head_is_ignored(self):
        # A green run exists but only under a different head_sha -> missing.
        decision = merge_gate.evaluate(
            NOXIA_POLICY,
            evidence(check_runs=[run("Vercel", "success", head_sha=OLD_HEAD)]),
            HEAD,
        )
        self.assertFalse(decision["allowed"])
        self.assertTrue(all(c["state"] == "missing" for c in decision["checks"]))

    def test_no_policy_blocks_merge_fail_closed(self):
        decision = merge_gate.evaluate(None, evidence(), HEAD)
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["mode"], "missing")

    def test_mode_off_allows_without_checks(self):
        decision = merge_gate.evaluate({"mode": "off"}, evidence(), HEAD)
        self.assertTrue(decision["allowed"])

    def test_policy_without_required_checks_blocks(self):
        decision = merge_gate.evaluate({"mode": "fail-closed", "required": []}, evidence(), HEAD)
        self.assertFalse(decision["allowed"])

    def test_invalid_mode_blocks(self):
        decision = merge_gate.evaluate({"mode": "banana", "required": ["vercel"]}, evidence(), HEAD)
        self.assertFalse(decision["allowed"])

    def test_truncated_evidence_blocks_merge(self):
        decision = merge_gate.evaluate(NOXIA_POLICY, noxia_evidence(truncated=True), HEAD)
        self.assertFalse(decision["allowed"])
        self.assertTrue(any("truncated" in r for r in decision["blocking_reasons"]))

    def test_evidence_for_other_head_blocks(self):
        decision = merge_gate.evaluate(NOXIA_POLICY, noxia_evidence(), OLD_HEAD)
        self.assertFalse(decision["allowed"])
        self.assertTrue(any("belongs to head" in r for r in decision["blocking_reasons"]))

    def test_custom_object_descriptor(self):
        policy = {"mode": "fail-closed", "required": [
            {"id": "ci", "source": "check-run", "name": "build", "match": "exact"},
        ]}
        decision = merge_gate.evaluate(
            policy, evidence(check_runs=[run("build", "success")]), HEAD
        )
        self.assertTrue(decision["allowed"])


class MergeGatePolicyTests(unittest.TestCase):
    def test_gate_decision_no_policy_blocks_without_network(self):
        with mock.patch.object(merge_gate, "collect_evidence", side_effect=AssertionError("network must not be called")):
            decision = merge_gate.gate_decision("token", {}, "owner/repo", HEAD)
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["mode"], "missing")

    def test_gate_decision_uses_collected_evidence(self):
        def fake_gh(token, path):
            if "/check-runs" in path:
                return {"total_count": 2, "check_runs": [
                    {"name": "Migrations", "conclusion": "failure", "status": "completed",
                     "app": {"slug": "supabase"}, "head_sha": HEAD},
                    {"name": "Vercel", "conclusion": "success", "status": "completed",
                     "app": {"slug": "vercel"}, "head_sha": HEAD},
                ]}
            if path.endswith("/status"):
                return {"statuses": []}
            return None
        with mock.patch.object(merge_gate, "gh_json", side_effect=fake_gh):
            decision = merge_gate.gate_decision("token", {"merge_gate": NOXIA_POLICY}, "owner/repo", HEAD)
        self.assertFalse(decision["allowed"])
        states = {c["id"]: c["state"] for c in decision["checks"]}
        self.assertEqual(states["supabase-migrations"], "failed")
        self.assertEqual(states["supabase-preview"], "missing")

    def test_gate_decision_network_error_blocks(self):
        with mock.patch.object(merge_gate, "gh_json", side_effect=RuntimeError("HTTP 500")):
            decision = merge_gate.gate_decision("token", {"merge_gate": NOXIA_POLICY}, "owner/repo", HEAD)
        self.assertFalse(decision["allowed"])
        self.assertTrue(any("evidence collection failed" in r for r in decision["blocking_reasons"]))

    def test_gate_decision_mode_off_without_network(self):
        with mock.patch.object(merge_gate, "collect_evidence", side_effect=AssertionError("network must not be called")):
            decision = merge_gate.gate_decision("token", {"merge_gate": {"mode": "off"}}, "owner/repo", HEAD)
        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["mode"], "off")


    def test_normalize_policy_none_and_off(self):
        self.assertIsNone(merge_gate.normalize_policy({}))
        self.assertEqual(merge_gate.normalize_policy({"merge_gate": {"mode": "off"}}), {"mode": "off"})
        with self.assertRaises(ValueError):
            merge_gate.normalize_policy({"merge_gate": {"mode": "fail-closed", "required": []}})
        with self.assertRaises(ValueError):
            merge_gate.normalize_policy({"merge_gate": {"mode": "open"}})

    def test_known_descriptors(self):
        self.assertEqual(merge_gate.normalize_descriptor("vercel")["name"], "vercel")
        self.assertEqual(merge_gate.normalize_descriptor("supabase-migrations")["app_slug"], "supabase")
        self.assertIsNone(merge_gate.normalize_descriptor("unknown-thing"))
        self.assertIsNone(merge_gate.normalize_descriptor(42))

    def test_registry_declares_noxia_fail_closed_gate(self):
        import json
        registry = json.loads((HERE.parent.parent / "registry" / "projects.json").read_text(encoding="utf-8"))
        noxia = next(p for p in registry["projects"] if p["id"] == "noxia")
        policy = merge_gate.normalize_policy(noxia)
        self.assertEqual(policy["mode"], "fail-closed")
        self.assertEqual(policy["required"], ["vercel", "supabase-preview", "supabase-migrations"])
        self.assertTrue(all(merge_gate.normalize_descriptor(c) is not None for c in policy["required"]))


class OrchestrateWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        spec = importlib.util.spec_from_file_location("orchestrate", HERE / "orchestrate.py")
        cls.orchestrate = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules["orchestrate"] = cls.orchestrate  # dataclass annotations resolve via sys.modules
        spec.loader.exec_module(cls.orchestrate)

    def _pr(self):
        return {"html_url": "https://github.com/o/r/pull/1", "head": {"sha": HEAD}, "number": 1}

    def test_queue_auto_merge_invoked_only_when_gate_allows(self):
        pr = self._pr()
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return mock.Mock(returncode=0)

        with mock.patch.object(self.orchestrate.merge_gate, "gate_decision",
                               return_value={"allowed": False, "blocking_reasons": ["check failed"], "checks": []}), \
             mock.patch.object(self.orchestrate, "run", side_effect=fake_run):
            merge, gate = self.orchestrate.queue_auto_merge("token", {"merge_gate": NOXIA_POLICY}, "o/r", pr)
        self.assertEqual(merge, "merge-gate-blocked")
        self.assertEqual(calls, [])

        with mock.patch.object(self.orchestrate.merge_gate, "gate_decision",
                               return_value={"allowed": True, "blocking_reasons": [], "checks": []}), \
             mock.patch.object(self.orchestrate, "run", side_effect=fake_run):
            merge, gate = self.orchestrate.queue_auto_merge("token", {"merge_gate": NOXIA_POLICY}, "o/r", pr)
        self.assertEqual(merge, "auto-merge-queued")
        self.assertEqual(len(calls), 1)
        self.assertIn("gh", calls[0][0])
        self.assertIn("merge", calls[0])
        self.assertIn("--auto", calls[0])

    def test_queue_auto_merge_blocks_without_head_sha(self):
        pr = {"html_url": "https://github.com/o/r/pull/1", "head": {"sha": ""}}
        with mock.patch.object(self.orchestrate, "run", side_effect=AssertionError("merge must not run")):
            merge, gate = self.orchestrate.queue_auto_merge("token", {"merge_gate": NOXIA_POLICY}, "o/r", pr)
        self.assertEqual(merge, "merge-gate-blocked")

    def test_merge_invocation_is_behind_the_gate(self):
        source = (HERE / "orchestrate.py").read_text(encoding="utf-8")
        self.assertIn("import merge_gate", source)
        lines = source.splitlines()
        merge_index = next(i for i, line in enumerate(lines) if '"gh","pr","merge"' in line)
        # The merge call must sit inside queue_auto_merge, below the allowed check.
        allowed_index = next(i for i, line in enumerate(lines) if 'gate["allowed"]' in line)
        self.assertLess(allowed_index, merge_index)
        self.assertIn("merge-gate-blocked", source)
        # The legacy unconditional merge shape is gone.
        self.assertNotIn('merge="auto-merge-queued" if cp.returncode==0 else "auto-merge-unavailable"', source)


if __name__ == "__main__":
    unittest.main()
