#!/usr/bin/env python3
"""Deterministic merge triage for research candidate PRs in the Knowledge Graph.

The script does not call GitHub and holds no secrets. It reads
  * a local clone of kueper-knowledge-graph (research branches fetched),
  * the research queue of this repository,
  * a JSON list of open PRs (number, head_ref, head_sha, draft, checks_ok, mergeable),
and decides per PR: ``merge``, ``hold`` (with reasons) or ``close`` (superseded).
Merging itself is done by the caller (Claude run "KG-Merge und Rückfragen").

Candidates stay non-canonical after merge: merging only moves them into the KG
staging area ``research/candidates/`` so the Canon Conflict Loop can assess them.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location("research_execute", ROOT / "tools/research/execute.py")
assert _SPEC and _SPEC.loader
EXECUTE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(EXECUTE)
POLICY = EXECUTE.POLICY
CANDIDATE_PATH = POLICY["candidate_path"]

BRANCH_RE = re.compile(r"^research/(res-[0-9a-z-]+)$")
# "TBD" is deliberately not listed: real sources (e.g. NASA BVAD tables) use it.
PLACEHOLDER_RE = re.compile(r"(example\.com|lorem ipsum|\bTODO\b|\[citation needed\]|<URL>|\bXXX\b)", re.I)
BASE_SECTIONS = ["## Forschungsfrage", "## Befundlage", "## Gegenbefunde und Unsicherheit",
                 "## Claim-Source-Mapping", "## Quellen", "## Relevanz für KUEPER-Projekte", "## Offene Fragen"]


def git(kg: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=kg, check=True, capture_output=True, text=True).stdout


def research_id(head_ref: str) -> str | None:
    m = BRANCH_RE.match(head_ref or "")
    return m.group(1).upper() if m else None


def check_text(text: str, item: dict[str, Any]) -> list[str]:
    """Structural gate equivalent to execute.validate_result, without the agent's JSON."""
    reasons: list[str] = []
    profile_name, profile = EXECUTE.evidence_profile(item)
    required = list(BASE_SECTIONS)
    if profile.get("require_claim_classification"):
        required.append("## Claim-Klassifikation")
    if profile.get("require_freshness_check") or profile.get("require_conflict_check"):
        required.append("## Aktualität und Widerspruchsprüfung")
    try:
        route_id, _ = EXECUTE.publication_route(profile, item.get("publication_route_hint"))
    except RuntimeError as exc:
        route_id = None
        reasons.append(f"publication route: {exc}")
    if route_id:
        required.append("## Publikationsroute")
    missing = [s for s in required if s not in text]
    if missing:
        reasons.append(f"missing sections: {missing}")
    urls = set(re.findall(r"https?://[^\s)>\]]+", text))
    if len(urls) < int(profile.get("minimum_urls", 2)):
        reasons.append(f"only {len(urls)} URLs (< {profile.get('minimum_urls', 2)} for {profile_name})")
    if profile.get("require_strong_source"):
        markers = [str(m).lower() for m in profile.get("strong_source_markers", [])]
        low = text.lower()
        # Accept the marker with a hyphen or a space ("peer-reviewed" / "peer reviewed").
        if markers and not any(m in low or m.replace("-", " ") in low for m in markers):
            reasons.append(f"no strong source marker for {profile_name}")
    if not re.search(r"non-canonical|nicht[- ]kanonisch", text, re.I):
        reasons.append("status 'non-canonical' not stated")
    hit = PLACEHOLDER_RE.search(text)
    if hit:
        reasons.append(f"placeholder text: {hit.group(0)!r}")
    return reasons


def triage_pr(pr: dict[str, Any], kg: Path, queue_dir: Path, base: str, on_main: set[str],
              ids_seen: dict[str, list[int]]) -> dict[str, Any]:
    out: dict[str, Any] = {"number": pr["number"], "head_ref": pr["head_ref"], "decision": "hold", "reasons": []}
    rid = research_id(pr["head_ref"])
    out["id"] = rid
    if not rid:
        out["reasons"].append("head branch is not research/res-…")
        return out
    if rid in on_main:
        out["decision"] = "close"
        out["reasons"].append("candidate already on main (superseded)")
        return out
    if len(ids_seen.get(rid, [])) > 1:
        out["reasons"].append(f"several open PRs for {rid}: {ids_seen[rid]}")
    qf = queue_dir / f"{rid}.json"
    if not qf.exists():
        out["reasons"].append("no queue entry")
        item: dict[str, Any] = {"id": rid}
    else:
        item = json.loads(qf.read_text(encoding="utf-8"))
        if item.get("status") != "candidate-pr":
            out["reasons"].append(f"queue status is {item.get('status')!r}, expected 'candidate-pr'")
        url = item.get("candidate_pr") or ""
        if not url.endswith(f"/pull/{pr['number']}"):
            out["reasons"].append(f"queue points to {url or 'no PR'}")
    expected = f"{CANDIDATE_PATH}/{rid}.md"
    head = pr.get("head_sha") or f"origin/{pr['head_ref']}"
    try:
        mb = git(kg, "merge-base", base, head).strip()
        changed = [l for l in git(kg, "diff", "--name-only", mb, head).splitlines() if l]
    except subprocess.CalledProcessError as exc:
        out["reasons"].append(f"git: {exc.stderr.strip()[:200]}")
        return out
    if changed != [expected]:
        out["reasons"].append(f"changes other files: {changed}")
    try:
        text = git(kg, "show", f"{head}:{expected}")
    except subprocess.CalledProcessError:
        out["reasons"].append(f"{expected} missing on head")
        return out
    out["reasons"].extend(check_text(text, item))
    if pr.get("checks_ok") is False:
        out["reasons"].append("CI not green")
    if pr.get("mergeable") is False:
        out["reasons"].append("not mergeable")
    out["source_project"] = item.get("source_project")
    if not out["reasons"]:
        out["decision"] = "merge"
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kg", required=True, type=Path, help="local clone of kueper-knowledge-graph")
    ap.add_argument("--prs", required=True, type=Path, help="JSON list of open PRs")
    ap.add_argument("--queue", type=Path, default=ROOT / "research/queue")
    ap.add_argument("--base", default="origin/main")
    a = ap.parse_args(argv)
    prs = json.loads(a.prs.read_text(encoding="utf-8"))
    prs = [p for p in prs if str(p.get("head_ref", "")).startswith("research/")]
    on_main = {Path(p).stem for p in git(a.kg, "ls-tree", "--name-only", a.base, CANDIDATE_PATH + "/").splitlines()}
    ids_seen: dict[str, list[int]] = {}
    for p in prs:
        rid = research_id(p["head_ref"])
        if rid:
            ids_seen.setdefault(rid, []).append(p["number"])
    results = [triage_pr(p, a.kg, a.queue, a.base, on_main, ids_seen) for p in sorted(prs, key=lambda p: p["number"])]
    summary: dict[str, int] = {}
    for r in results:
        summary[r["decision"]] = summary.get(r["decision"], 0) + 1
    json.dump({"summary": summary, "results": results}, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
