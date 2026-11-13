"""Tests für die Auswertelogik von credential_health.py – ohne Netzaufrufe."""
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))

import credential_health as ch  # noqa: E402

NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)


class GithubTests(unittest.TestCase):
    def test_parse_utc_and_offset(self):
        self.assertEqual(ch.parse_github_expiration("2026-12-01 10:00:00 UTC").day, 1)
        parsed = ch.parse_github_expiration("2026-12-01 10:00:00 +0100")
        self.assertEqual(parsed.astimezone(timezone.utc).hour, 9)
        self.assertIsNone(ch.parse_github_expiration("kaputt"))
        self.assertIsNone(ch.parse_github_expiration(None))

    def test_valid_without_expiration(self):
        self.assertEqual(ch.evaluate_github("T", 200, None, NOW, 14).status, ch.OK)

    def test_expiring_soon(self):
        r = ch.evaluate_github("T", 200, "2026-11-20 00:00:00 UTC", NOW, 14)
        self.assertEqual(r.status, ch.EXPIRING)
        self.assertEqual(r.expires_at, "2026-11-20")

    def test_far_expiration_ok(self):
        self.assertEqual(ch.evaluate_github("T", 200, "2027-03-01 00:00:00 UTC", NOW, 14).status, ch.OK)

    def test_expired_and_unauthorized(self):
        self.assertEqual(ch.evaluate_github("T", 200, "2026-11-01 00:00:00 UTC", NOW, 14).status, ch.ERROR)
        self.assertEqual(ch.evaluate_github("T", 401, None, NOW, 14).status, ch.ERROR)
        self.assertEqual(ch.evaluate_github("T", 403, None, NOW, 14).status, ch.ERROR)

    def test_no_answer_is_unknown_not_ok(self):
        self.assertEqual(ch.evaluate_github("T", None, None, NOW, 14).status, ch.UNKNOWN)


class DeepseekTests(unittest.TestCase):
    def body(self, amount, available=True):
        return {"is_available": available,
                "balance_infos": [{"currency": "USD", "total_balance": amount}]}

    def test_sufficient(self):
        r = ch.evaluate_deepseek(200, self.body("10.50"), 2.0)
        self.assertEqual(r.status, ch.OK)
        self.assertEqual(r.balance, "10.50 USD")

    def test_low_balance(self):
        self.assertEqual(ch.evaluate_deepseek(200, self.body("1.00"), 2.0).status, ch.LOW)

    def test_unavailable_flag(self):
        self.assertEqual(ch.evaluate_deepseek(200, self.body("5.00", False), 2.0).status, ch.LOW)

    def test_402_and_401(self):
        self.assertEqual(ch.evaluate_deepseek(402, None, 2.0).status, ch.LOW)
        self.assertEqual(ch.evaluate_deepseek(401, None, 2.0).status, ch.ERROR)

    def test_unreadable_body(self):
        self.assertEqual(ch.evaluate_deepseek(200, {"balance_infos": []}, 2.0).status, ch.UNKNOWN)


class GatewayAndSupabaseTests(unittest.TestCase):
    def test_gateway(self):
        self.assertEqual(ch.evaluate_gateway(200, {"balance": "12.3"}, 2.0).status, ch.OK)
        self.assertEqual(ch.evaluate_gateway(200, {"balance": "0.5"}, 2.0).status, ch.LOW)
        self.assertEqual(ch.evaluate_gateway(401, None, 2.0).status, ch.ERROR)
        self.assertEqual(ch.evaluate_gateway(200, {}, 2.0).status, ch.OK)

    def test_supabase(self):
        self.assertEqual(ch.evaluate_supabase(200).status, ch.OK)
        self.assertEqual(ch.evaluate_supabase(401).status, ch.ERROR)
        self.assertEqual(ch.evaluate_supabase(500).status, ch.UNKNOWN)


class RunAndAlertTests(unittest.TestCase):
    def test_missing_secrets_are_not_problems(self):
        with mock.patch.object(ch, "_request") as req:
            results = ch.run_checks({}, NOW)
        req.assert_not_called()
        self.assertTrue(all(r.status == ch.MISSING for r in results))
        self.assertFalse(ch.has_problem(results))

    def test_secret_values_never_in_output_or_alert(self):
        secret = "ghp_SUPERGEHEIM123"
        env = {"KUEPER_BOT_TOKEN": secret, "DEEPSEEK_API_KEY": "sk-GEHEIM456"}

        def fake(url, headers, timeout=20):
            if "github" in url:
                return 401, {}, b""
            return 402, {}, b""

        with mock.patch.object(ch, "_request", side_effect=fake):
            results = ch.run_checks(env, NOW)
        self.assertTrue(ch.has_problem(results))
        alert = ch.render_alert(results, "2026-11-13")
        for value in env.values():
            self.assertNotIn(value, alert)
            self.assertNotIn(value, repr(results))
        self.assertIn(ch.ALERT_TASK_ID, alert)

    def test_alert_file_is_overwritten_not_duplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ECO-OPS-credential-alert.md")
            bad = [ch.Result("KUEPER_BOT_TOKEN", ch.ERROR, "401")]
            with mock.patch.object(ch, "run_checks", return_value=bad):
                self.assertEqual(ch.main(["--alert-file", path]), 1)
                self.assertEqual(ch.main(["--alert-file", path]), 1)
            self.assertEqual(os.listdir(tmp), ["ECO-OPS-credential-alert.md"])
            with mock.patch.object(ch, "run_checks", return_value=[ch.Result("X", ch.OK)]):
                self.assertEqual(ch.main([]), 0)


if __name__ == "__main__":
    unittest.main()
