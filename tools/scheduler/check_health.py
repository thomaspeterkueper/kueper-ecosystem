#!/usr/bin/env python3
"""Deterministic health check for the KUEPER external scheduler.

Replaces ad-hoc GitHub Actions history observation for the two scheduled
workers (`KUEPER Agent Worker V7`, `KUEPER Automated PR Review`) with a
machine-readable verdict.

Backends:
  auto (default) - use Supabase when SUPABASE_URL + SUPABASE_SECRET_KEY are
                   set, otherwise fall back to GitHub run history.
  supabase       - call public.kueper_scheduler_health() and report the
                   server-side stale flags.
  github         - evaluate the last cron slots against the GitHub Actions
                   run history. A slot counts as covered when a schedule or
                   workflow_dispatch run was created within it, so a covered
                   slot proves the trigger source fired - not that the agent
                   work succeeded. Cancelled or queued runs still cover the
                   slot.

Exit codes:
  0  all checked workers healthy
  1  at least one worker stale
  2  configuration or transport error (fail closed)

Stdlib only. Read-only: never dispatches, never enables or disables anything.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request

WORKERS = {
    "agent-worker-v7": {
        "workflow_file": "agent-worker-v7.yml",
        "slot_minutes": set(range(0, 60, 15)),
        "cadence": "*/15 * * * *",
    },
    "pr-review-agent": {
        "workflow_file": "pr-review-agent.yml",
        "slot_minutes": {7, 22, 37, 52},
        "cadence": "7,22,37,52 * * * *",
    },
}

SLOT_INTERVAL_MINUTES = 15
DEFAULT_SLOT_COUNT = 4
DEFAULT_MAX_RUN_AGE_MINUTES = 40
DEFAULT_REPO = "thomaspeterkueper/kueper-ecosystem"
API_BASE = "https://api.github.com"


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value


def _rpc(function_name: str, payload: dict) -> object:
    base_url = _required_env("SUPABASE_URL").rstrip("/")
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


def _http_get_json(url: str, token: str | None) -> object:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "kueper-scheduler-health"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub API {url} failed: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub API {url} unreachable: {exc.reason}") from exc
    return json.loads(raw) if raw else None


def _parse_iso(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


def _now() -> dt.datetime:
    """Wall-clock source for slot/age evaluation; patched by tests."""
    return dt.datetime.now(dt.timezone.utc)


def recent_slots(slot_minutes: set[int], now: dt.datetime, count: int) -> list[dt.datetime]:
    """Return the most recent `count` slot times (newest first).

    A slot is the start of a 15-minute interval whose minute-of-hour is in
    `slot_minutes`. Slots in the future are skipped.
    """
    slots: list[dt.datetime] = []
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    while len(slots) < count:
        for minute in sorted(slot_minutes, reverse=True):
            slot = hour_start.replace(minute=minute)
            if slot <= now:
                slots.append(slot)
                if len(slots) == count:
                    break
        hour_start -= dt.timedelta(hours=1)
    return slots[:count]


def fetch_github_runs(repo: str, workflow_file: str, token: str | None) -> list[dict]:
    url = (
        f"{API_BASE}/repos/{repo}/actions/workflows/{workflow_file}/runs"
        "?per_page=20&exclude_pull_requests=true"
    )
    result = _http_get_json(url, token)
    if not isinstance(result, dict) or "workflow_runs" not in result:
        raise RuntimeError(f"unexpected GitHub runs response for {workflow_file}: {result!r}")
    return [run for run in result["workflow_runs"] if run.get("event") in ("schedule", "workflow_dispatch")]


def evaluate_github_worker(
    worker: str,
    runs: list[dict],
    now: dt.datetime,
    slot_count: int = DEFAULT_SLOT_COUNT,
    max_run_age_minutes: int = DEFAULT_MAX_RUN_AGE_MINUTES,
) -> dict:
    spec = WORKERS[worker]
    slots = recent_slots(spec["slot_minutes"], now, slot_count)
    interval = dt.timedelta(minutes=SLOT_INTERVAL_MINUTES)
    run_times = sorted(
        (_parse_iso(run["created_at"]) for run in runs if run.get("created_at")),
        reverse=True,
    )
    covered = [any(slot <= t < slot + interval for t in run_times) for slot in slots]
    covered_count = sum(covered)
    consecutive = 0
    for is_covered in covered:
        if is_covered:
            consecutive += 1
        else:
            break
    latest_run = runs[0] if runs else None
    latest_run_at = _parse_iso(latest_run["created_at"]) if latest_run else None
    latest_age = (now - latest_run_at).total_seconds() / 60 if latest_run_at else None
    schedule_times = [
        _parse_iso(run["created_at"])
        for run in runs
        if run.get("event") == "schedule" and run.get("created_at")
    ]
    last_schedule_at = max(schedule_times) if schedule_times else None

    healthy = (
        latest_age is not None
        and latest_age <= max_run_age_minutes
        and covered_count >= 2
        and (covered[0] or covered[1])
    )
    return {
        "worker": worker,
        "cadence": spec["cadence"],
        "verdict": "healthy" if healthy else "stale",
        "latest_run_at": latest_run_at.isoformat() if latest_run_at else None,
        "latest_run_event": latest_run.get("event") if latest_run else None,
        "latest_run_status": latest_run.get("status") if latest_run else None,
        "latest_run_conclusion": latest_run.get("conclusion") if latest_run else None,
        "latest_run_age_minutes": round(latest_age, 1) if latest_age is not None else None,
        "slots_covered": covered_count,
        "slots_total": slot_count,
        "consecutive_slots_covered": consecutive,
        "last_schedule_run_at": last_schedule_at.isoformat() if last_schedule_at else None,
    }


def evaluate_supabase_workers(worker_names: list[str]) -> list[dict]:
    rows = _rpc("kueper_scheduler_health", {})
    if not isinstance(rows, list):
        raise RuntimeError(f"unexpected scheduler health response: {rows!r}")
    by_worker = {row.get("worker_name"): row for row in rows if isinstance(row, dict)}
    results = []
    for worker in worker_names:
        row = by_worker.get(worker)
        if row is None or row.get("stale") is not False:
            results.append({"worker": worker, "verdict": "stale", "row": row})
        else:
            results.append({"worker": worker, "verdict": "healthy", "row": row})
    return results


def _verdict(results: list[dict]) -> str:
    return "stale" if any(result["verdict"] == "stale" for result in results) else "healthy"


def _exit_code(verdict: str) -> int:
    return 0 if verdict == "healthy" else 1


def render_human(backend: str, results: list[dict]) -> str:
    lines = [f"scheduler health via {backend}:"]
    for result in results:
        row = result.get("row")
        if row is not None:
            detail = f"status={row.get('last_status')} stale={row.get('stale')}"
        else:
            latest = result.get("latest_run_at")
            detail = (
                f"latest={latest} ({result.get('latest_run_event')},"
                f" {result.get('latest_run_status')})"
            )
            detail += (
                f" slots={result.get('slots_covered')}/{result.get('slots_total')}"
                f" consecutive={result.get('consecutive_slots_covered')}"
            )
            if result.get("last_schedule_run_at"):
                detail += f" last_schedule={result.get('last_schedule_run_at')}"
        lines.append(f"  {result['worker']}: {result['verdict']} ({detail})")
    lines.append(f"verdict: {_verdict(results)}")
    return "\n".join(lines)


def render_json(backend: str, results: list[dict]) -> str:
    return json.dumps(
        {
            "backend": backend,
            "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "verdict": _verdict(results),
            "workers": results,
        },
        indent=2,
        default=str,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("auto", "supabase", "github"), default="auto")
    parser.add_argument("--worker", choices=("all", *WORKERS.keys()), default="all")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--slots", type=int, default=DEFAULT_SLOT_COUNT)
    parser.add_argument("--max-run-age-minutes", type=int, default=DEFAULT_MAX_RUN_AGE_MINUTES)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    workers = list(WORKERS.keys()) if args.worker == "all" else [args.worker]
    now = _now()
    try:
        if args.backend == "supabase" or (
            args.backend == "auto" and os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SECRET_KEY")
        ):
            backend = "supabase"
            results = evaluate_supabase_workers(workers)
        else:
            backend = "github"
            token = os.environ.get("GH_TOKEN") or None
            results = [
                evaluate_github_worker(
                    worker,
                    fetch_github_runs(args.repo, WORKERS[worker]["workflow_file"], token),
                    now,
                    slot_count=args.slots,
                    max_run_age_minutes=args.max_run_age_minutes,
                )
                for worker in workers
            ]
    except Exception as exc:  # fail closed: never report health on partial data
        print(f"scheduler health check error: {exc}", file=sys.stderr)
        return 2
    verdict = _verdict(results)
    if args.as_json:
        print(render_json(backend, results))
    else:
        print(render_human(backend, results))
    return _exit_code(verdict)


if __name__ == "__main__":
    raise SystemExit(main())
