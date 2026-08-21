#!/usr/bin/env python3
import datetime as dt
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from provider_router import load_policy, route

UTC = dt.timezone.utc

class ProviderRouterTest(unittest.TestCase):
    def setUp(self):
        self.policy = load_policy()

    def test_medium_research_defers_in_first_peak(self):
        d = route({"type":"RESEARCH", "priority":"medium"}, dt.datetime(2026,7,26,2,0,tzinfo=UTC), self.policy)
        self.assertFalse(d.execute_now)
        self.assertEqual(d.provider, "deepseek")
        self.assertEqual(d.price_multiplier, 2.0)
        self.assertEqual(d.cost_policy, "prefer_off_peak")
        self.assertTrue(d.available_at.startswith("2026-07-26T04:02"))

    def test_high_research_runs_in_peak(self):
        d = route({"type":"RESEARCH", "priority":"high"}, dt.datetime(2026,7,26,7,0,tzinfo=UTC), self.policy)
        self.assertTrue(d.execute_now)
        self.assertEqual(d.price_multiplier, 2.0)

    def test_medium_research_runs_off_peak(self):
        d = route({"type":"RESEARCH", "priority":"medium"}, dt.datetime(2026,7,26,5,0,tzinfo=UTC), self.policy)
        self.assertTrue(d.execute_now)
        self.assertEqual(d.price_multiplier, 1.0)

    def test_bug_is_not_deferred(self):
        d = route({"type":"BUG", "priority":"medium"}, dt.datetime(2026,7,26,2,30,tzinfo=UTC), self.policy)
        self.assertTrue(d.execute_now)

    def test_complex_research_uses_pro(self):
        d = route({"type":"RESEARCH", "priority":"high"}, dt.datetime(2026,7,26,5,0,tzinfo=UTC), self.policy)
        self.assertEqual(d.model, "deepseek-v4-pro")

    def test_payload_can_force_off_peak_for_expensive_code(self):
        d = route({
            "type":"COMPLEX_CODING",
            "priority":"medium",
            "payload":{"cost_policy":"off_peak_only", "estimated_effort":"high"}
        }, dt.datetime(2026,7,26,2,0,tzinfo=UTC), self.policy)
        self.assertFalse(d.execute_now)
        self.assertEqual(d.model, "deepseek-v4-pro")
        self.assertEqual(d.cost_policy, "off_peak_only")

    def test_payload_can_mark_normal_task_immediate(self):
        d = route({
            "type":"RESEARCH",
            "priority":"medium",
            "payload":{"cost_policy":"immediate"}
        }, dt.datetime(2026,7,26,2,0,tzinfo=UTC), self.policy)
        self.assertTrue(d.execute_now)
        self.assertEqual(d.cost_policy, "immediate")

    def test_high_priority_overrides_off_peak_only(self):
        d = route({
            "type":"RESEARCH",
            "priority":"high",
            "payload":{"cost_policy":"off_peak_only"}
        }, dt.datetime(2026,7,26,2,0,tzinfo=UTC), self.policy)
        self.assertTrue(d.execute_now)

    def test_invalid_cost_policy_is_rejected(self):
        with self.assertRaises(RuntimeError):
            route({"type":"RESEARCH", "payload":{"cost_policy":"free_money"}}, dt.datetime(2026,7,26,5,0,tzinfo=UTC), self.policy)

if __name__ == "__main__":
    unittest.main()
