from __future__ import annotations

import contextlib
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_worker as worker
import agent_worker_v77 as v77


class ScriptedDB:
    """Answers RPCs from a dict of name -> value or callable(payload)."""

    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def rpc(self, name, payload):
        self.calls.append((name, payload))
        answer = self.answers.get(name)
        return answer(payload) if callable(answer) else answer

    def names(self):
        return [name for name, _ in self.calls]


@contextlib.contextmanager
def no_heartbeat(*_args, **_kwargs):
    yield


CHAIN = [("deepseek", "deepseek-v4-flash"), ("gateway", "anthropic/claude-haiku-5.5")]
TASK = {"id": "t1", "lease_token": "lease", "type": "CLASSIFY"}


class WorkerV77Tests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(worker, "Heartbeat", no_heartbeat)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_402_falls_back_to_gateway_and_reserves_budget(self):
        db = ScriptedDB({"kueper_provider_available": True, "kueper_reserve_llm_invocation": {"allowed": True}})

        def executor(task, provider, model):
            if provider == "deepseek":
                raise worker.ProviderUnavailable("deepseek", "billing-insufficient-balance", "402", 21600)
            return {"kind": "analysis", "content": "ok"}

        outcome, provider, model, depth, err = v77.run_chain(db, TASK, "lease", CHAIN, "r", executor)
        self.assertEqual((provider, model, depth), ("gateway", "anthropic/claude-haiku-5.5", 1))
        self.assertEqual(outcome["content"], "ok")
        self.assertIn("kueper_pause_provider", db.names())
        reserve = [p for n, p in db.calls if n == "kueper_reserve_llm_invocation"]
        self.assertEqual(reserve[0]["p_provider"], "gateway")

    def test_429_falls_back(self):
        db = ScriptedDB({"kueper_provider_available": True, "kueper_reserve_llm_invocation": {"allowed": True}})
        seen = []

        def executor(task, provider, model):
            seen.append(provider)
            if provider == "deepseek":
                raise worker.ProviderUnavailable("deepseek", "http-429", "rate", 1800)
            return {"kind": "analysis"}

        outcome, *_ = v77.run_chain(db, TASK, "lease", CHAIN, "r", executor)
        self.assertIsNotNone(outcome)
        self.assertEqual(seen, ["deepseek", "gateway"])

    def test_exhausted_chain_returns_none_with_last_error(self):
        db = ScriptedDB({"kueper_provider_available": True, "kueper_reserve_llm_invocation": {"allowed": True}})

        def executor(task, provider, model):
            raise worker.ProviderUnavailable(provider, "http-503", "down", 1800)

        outcome, _p, _m, depth, err = v77.run_chain(db, TASK, "lease", CHAIN, "r", executor)
        self.assertIsNone(outcome)
        self.assertEqual(err.provider, "gateway")
        self.assertEqual(depth, 1)

    def test_fallback_budget_denied_is_skipped(self):
        db = ScriptedDB({"kueper_provider_available": True, "kueper_reserve_llm_invocation": {"allowed": False, "reason": "daily-call-budget-exhausted"}})
        calls = []

        def executor(task, provider, model):
            calls.append(provider)
            raise worker.ProviderUnavailable(provider, "http-429", "x", 1800)

        outcome, *_rest, err = v77.run_chain(db, TASK, "lease", CHAIN, "r", executor)
        self.assertIsNone(outcome)
        self.assertEqual(calls, ["deepseek"])
        self.assertEqual(err.provider, "deepseek")

    def test_claim_skips_paused_deepseek(self):
        def available(payload):
            return payload["p_provider"] != "deepseek"

        db = ScriptedDB({"kueper_provider_available": available,
                         "kueper_claim_task_with_llm_budget": {"claimed": True, "task": TASK, "budget": {"calls": 1}}})
        decision = SimpleNamespace(provider="deepseek", model="deepseek-v4-flash", reason="r")
        task, info, depth = v77.claim_along_chain(db, {"id": "t1"}, "w", decision, CHAIN)
        self.assertEqual(depth, 1)
        claim = [p for n, p in db.calls if n == "kueper_claim_task_with_llm_budget"][0]
        self.assertEqual((claim["p_provider"], claim["p_model"]), ("gateway", "anthropic/claude-haiku-5.5"))

    def test_claim_budget_exhausted_tries_next_provider(self):
        responses = iter([{"claimed": False, "reason": "daily-call-budget-exhausted"},
                          {"claimed": True, "task": TASK, "budget": {}}])
        db = ScriptedDB({"kueper_provider_available": True,
                         "kueper_claim_task_with_llm_budget": lambda _p: next(responses)})
        decision = SimpleNamespace(provider="deepseek", model="deepseek-v4-flash", reason="r")
        task, info, depth = v77.claim_along_chain(db, {"id": "t1"}, "w", decision, CHAIN)
        self.assertIsNotNone(task)
        self.assertEqual(info["provider"], "gateway")

    def test_claim_race_does_not_try_other_providers(self):
        db = ScriptedDB({"kueper_provider_available": True,
                         "kueper_claim_task_with_llm_budget": {"claimed": False, "reason": "task-no-longer-runnable"}})
        decision = SimpleNamespace(provider="deepseek", model="deepseek-v4-flash", reason="r")
        task, info, _ = v77.claim_along_chain(db, {"id": "t1"}, "w", decision, CHAIN)
        self.assertIsNone(task)
        self.assertEqual(len([n for n in db.names() if n == "kueper_claim_task_with_llm_budget"]), 1)

    def test_without_gateway_key_chain_is_primary_only(self):
        decision = SimpleNamespace(provider="deepseek", model="deepseek-v4-flash", reason="r")
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(v77.candidates_for({"type": "CLASSIFY"}, decision), [("deepseek", "deepseek-v4-flash")])

    def test_gateway_env_points_claude_code_at_gateway(self):
        with mock.patch.dict(os.environ, {"AI_GATEWAY_API_KEY": "k"}):
            env = v77.gateway_agent_env({"ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic", "ANTHROPIC_API_KEY": "x"}, "google/gemini-3-flash")
        self.assertEqual(env["ANTHROPIC_BASE_URL"], "https://ai-gateway.vercel.sh")
        self.assertEqual(env["ANTHROPIC_AUTH_TOKEN"], "k")
        self.assertEqual(env["ANTHROPIC_MODEL"], "google/gemini-3-flash")
        self.assertNotIn("ANTHROPIC_API_KEY", env)

    def test_run_hook_rewrites_env_only_while_gateway_active(self):
        seen = []

        def fake_run(cmd, *args, **kwargs):
            seen.append(kwargs.get("env", {}).get("ANTHROPIC_BASE_URL"))

        with mock.patch.object(worker, "run", fake_run), mock.patch.dict(os.environ, {"AI_GATEWAY_API_KEY": "k"}):
            v77._install_gateway_run_hook()
            worker.run(["claude", "-p"], env={"ANTHROPIC_BASE_URL": "deepseek"})
            with v77.active_provider("gateway", "anthropic/claude-haiku-5.5"):
                worker.run(["claude", "-p"], env={"ANTHROPIC_BASE_URL": "deepseek"})
                worker.run(["git", "status"], env={"ANTHROPIC_BASE_URL": "deepseek"})
        self.assertEqual(seen, ["deepseek", "https://ai-gateway.vercel.sh", "deepseek"])

    def test_gateway_agent_failure_is_attributed_to_gateway(self):
        def failing_repo_task(task, model):
            raise worker.ProviderUnavailable("deepseek", "rate-limit", "429", 1800)

        with mock.patch.object(worker, "repo_task", failing_repo_task):
            with self.assertRaises(worker.ProviderUnavailable) as ctx:
                v77.execute({"id": "t", "repository": "o/r"}, "gateway", "anthropic/claude-haiku-5.5")
        self.assertEqual(ctx.exception.provider, "gateway")

    def test_http_error_classification(self):
        self.assertIsInstance(v77.classify_http_error("gateway", 402, "no credits"), worker.ProviderUnavailable)
        self.assertEqual(v77.classify_http_error("gateway", 429, "slow").code, "http-429")
        self.assertNotIsInstance(v77.classify_http_error("gateway", 400, "bad"), worker.ProviderUnavailable)


if __name__ == "__main__":
    unittest.main()
