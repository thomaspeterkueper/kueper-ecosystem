#!/usr/bin/env python3
"""Small stdlib-only guard for KUEPER scheduled GitHub Actions.

The guard acquires/releases a Supabase-backed execution lease so an external
Supabase dispatch and GitHub's native schedule can coexist without duplicating
expensive worker/reviewer runs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value.rstrip("/") if name == "SUPABASE_URL" else value


def _rpc(function_name: str, payload: dict) -> object:
    base_url = _required_env("SUPABASE_URL")
    secret = _required_env("SUPABASE_SECRET_KEY")
    req = urllib.request.Request(
        f"{base_url}/rest/v1/rpc/{function_name}",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "apikey": secret,
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase RPC {function_name} failed: HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Supabase RPC {function_name} unreachable: {exc.reason}") from exc
    return json.loads(raw) if raw else None


def _write_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")
    else:
        print(f"{name}={value}")


def acquire(args: argparse.Namespace) -> int:
    scheduler_run_id = (args.scheduler_run_id or "").strip() or None
    source = args.source
    result = _rpc(
        "kueper_acquire_scheduler_lease",
        {
            "p_worker_name": args.worker,
            "p_run_id": scheduler_run_id,
            "p_source": source,
            "p_lease_seconds": args.lease_seconds,
            "p_cooldown_seconds": args.cooldown_seconds,
        },
    )
    if not isinstance(result, dict):
        raise RuntimeError(f"unexpected lease response: {result!r}")

    acquired = bool(result.get("acquired"))
    _write_output("should_run", "true" if acquired else "false")
    _write_output("scheduler_run_id", str(result.get("run_id") or ""))
    _write_output("lease_token", str(result.get("lease_token") or ""))
    _write_output("skip_reason", str(result.get("reason") or ""))

    if acquired:
        print(f"scheduler lease acquired for {args.worker}: {result.get('run_id')}")
    else:
        print(f"scheduler execution skipped for {args.worker}: {result.get('reason', 'not acquired')}")
    return 0


def finish(args: argparse.Namespace) -> int:
    status = "succeeded" if args.status == "success" else "failed"
    error = None if status == "succeeded" else f"GitHub job status: {args.status}"
    _rpc(
        "kueper_finish_scheduler_run",
        {
            "p_run_id": args.run_id,
            "p_lease_token": args.lease_token,
            "p_status": status,
            "p_github_run_id": args.github_run_id,
            "p_error": error,
        },
    )
    print(f"scheduler run {args.run_id} marked {status}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    acquire_parser = sub.add_parser("acquire")
    acquire_parser.add_argument("--worker", required=True, choices=("agent-worker-v7", "pr-review-agent"))
    acquire_parser.add_argument("--scheduler-run-id", default="")
    acquire_parser.add_argument("--source", required=True, choices=("supabase", "github_schedule", "manual"))
    acquire_parser.add_argument("--lease-seconds", type=int, default=5400)
    acquire_parser.add_argument("--cooldown-seconds", type=int, default=600)
    acquire_parser.set_defaults(func=acquire)

    finish_parser = sub.add_parser("finish")
    finish_parser.add_argument("--run-id", required=True)
    finish_parser.add_argument("--lease-token", required=True)
    finish_parser.add_argument("--status", required=True)
    finish_parser.add_argument("--github-run-id", type=int, required=True)
    finish_parser.set_defaults(func=finish)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:  # fail closed: duplicate prevention is part of the safety boundary
        print(f"scheduler guard error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
