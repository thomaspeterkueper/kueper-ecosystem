#!/usr/bin/env python3
"""KUEPER V7.1 worker compatibility wrapper.

Adds two production-safety fixes without duplicating the V7 execution engine:
- prefer the JSONB claim RPC so lease_token is always serialized correctly;
- re-probe DeepSeek when the circuit breaker is paused, so a replenished account can recover immediately.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# agent_worker imports provider_router as a sibling module.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_worker as worker  # noqa: E402


class PatchedSupabaseRPC(worker.SupabaseRPC):
    def rpc(self, name: str, payload: dict[str, Any]) -> Any:
        if name == "kueper_claim_task":
            try:
                task = super().rpc("kueper_claim_task_v7", payload)
            except worker.WorkerError as exc:
                # Transitional fallback until the V7.1 migration has been applied.
                if "HTTP 404" not in str(exc) and "PGRST202" not in str(exc):
                    raise
                task = super().rpc(name, payload)
            if task:
                task_id = task.get("id") if isinstance(task, dict) else None
                lease = task.get("lease_token") if isinstance(task, dict) else None
                if not task_id or not lease:
                    raise worker.WorkerError(
                        "claimed task is missing id/lease_token; apply migration "
                        "20260821163500_worker_v71_claim_and_provider_reset.sql before retrying"
                    )
            return task

        if name == "kueper_provider_available":
            available = super().rpc(name, payload)
            if available or str(payload.get("p_provider", "")).lower() != "deepseek":
                return available

            # A billing pause may have become obsolete after the account was topped up.
            # Probe the provider once before postponing work for another six hours.
            if deepseek_probe():
                try:
                    super().rpc("kueper_reset_provider", {"p_provider": "deepseek", "p_reason": "availability probe succeeded"})
                except worker.WorkerError as exc:
                    # The migration may not yet be deployed. Bypass only this stale pause
                    # for the current run; real provider errors will pause it again.
                    print(f"WARN could not persist DeepSeek provider reset: {exc}", flush=True)
                print("DeepSeek availability probe succeeded; stale provider pause bypassed.", flush=True)
                return True
            return False

        return super().rpc(name, payload)


def deepseek_probe() -> bool:
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        return False
    req = urllib.request.Request("https://api.deepseek.com/models")
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            if response.status != 200:
                return False
            if raw:
                json.loads(raw)
            return True
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"DeepSeek availability probe failed: {exc}", flush=True)
        return False


def main() -> int:
    worker.SupabaseRPC = PatchedSupabaseRPC
    return worker.main()


if __name__ == "__main__":
    raise SystemExit(main())
