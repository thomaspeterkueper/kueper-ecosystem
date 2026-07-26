#!/usr/bin/env python3
import datetime as dt
import unittest
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

if __name__ == "__main__":
    unittest.main()
