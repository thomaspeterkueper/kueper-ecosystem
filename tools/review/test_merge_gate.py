#!/usr/bin/env python3
from __future__ import annotations
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import merge_gate  # noqa: E402
HEAD="ee23d493a818214e4e534729da589c7b0b4b66a4"
POLICY={"mode":"fail-closed","required":[
 {"id":"vercel","source":"commit_status","context":"Vercel"},
 {"id":"supabase-preview","source":"check_run","name":"Supabase Preview"},
 {"id":"supabase-migrations","source":"check_run","name":"Supabase Preview","reject_output_patterns":["❌","error:","failure","failed"]},
]}
def status(state="success",sha=HEAD): return {"sha":sha,"statuses":[{"context":"Vercel","state":state}]}
def checks(conclusion="success",sha=HEAD,include=True,run_status="completed",summary=""):
 runs=[]
 if include: runs.append({"name":"Supabase Preview","head_sha":sha,"status":run_status,"conclusion":conclusion,"output":{"summary":summary}})
 return {"check_runs":runs}
class MergeGateTests(unittest.TestCase):
 def test_regression_vercel_green_supabase_migration_failure_blocks(self):
  r=merge_gate.evaluate(POLICY,HEAD,status(),checks("failure")); self.assertFalse(r["allowed"]); self.assertIn("supabase-preview-failure",r["reason"])
 def test_explicit_error_output_blocks_even_if_conclusion_says_success(self):
  r=merge_gate.evaluate(POLICY,HEAD,status(),checks("success",summary="ERROR: migration failed")); self.assertFalse(r["allowed"]); self.assertIn("supabase-migrations-output-error",r["reason"])
 def test_missing_required_check_blocks(self):
  r=merge_gate.evaluate(POLICY,HEAD,status(),checks(include=False)); self.assertFalse(r["allowed"]); self.assertIn("missing-or-ambiguous",r["reason"])
 def test_check_from_old_head_blocks(self):
  r=merge_gate.evaluate(POLICY,HEAD,status(),checks(sha="old-head")); self.assertFalse(r["allowed"]); self.assertIn("stale-head",r["reason"])
 def test_incomplete_check_blocks(self):
  r=merge_gate.evaluate(POLICY,HEAD,status(),checks(conclusion="",run_status="in_progress")); self.assertFalse(r["allowed"]); self.assertIn("incomplete",r["reason"])
 def test_failed_vercel_blocks(self):
  r=merge_gate.evaluate(POLICY,HEAD,status("failure"),checks()); self.assertFalse(r["allowed"]); self.assertIn("vercel-failure",r["reason"])
 def test_all_required_current_head_green_allows_review_to_continue(self):
  r=merge_gate.evaluate(POLICY,HEAD,status(),checks()); self.assertTrue(r["allowed"]); self.assertEqual(r["reason"],"all-required-checks-green"); self.assertEqual([x["id"] for x in r["details"]],["vercel","supabase-preview","supabase-migrations"])
 def test_status_payload_for_old_head_blocks(self):
  r=merge_gate.evaluate(POLICY,HEAD,status(sha="old-head"),checks()); self.assertFalse(r["allowed"]); self.assertEqual(r["reason"],"stale-status-head")
if __name__=="__main__": unittest.main()
