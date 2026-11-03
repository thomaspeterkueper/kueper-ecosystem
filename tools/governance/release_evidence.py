#!/usr/bin/env python3
"""Read-only PR release evidence audit. Never merges or changes branch protection."""
import json, os, sys, urllib.parse, urllib.request, urllib.error

REPOS = [
    "thomaspeterkueper/noxiagame",
    "thomaspeterkueper/kueper-ecosystem",
    "thomaspeterkueper/kueper-knowledge-graph",
    "thomaspeterkueper/solarsciencefoundation",
]
API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

def get(path):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "kueper-release-evidence-audit",
        **({"Authorization": "Bearer " + TOKEN} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)

def inspect(repo, pr):
    number, sha = pr["number"], pr["head"]["sha"]
    root = "/repos/" + repo
    reviews = get(root + "/pulls/" + str(number) + "/reviews?per_page=100")
    # Latest submitted review per reviewer; dismissals and change requests count.
    latest = {}
    for review in reviews:
        login = (review.get("user") or {}).get("login")
        if login and review.get("submitted_at"):
            latest[login] = review["state"]
    checks = get(root + "/commits/" + sha + "/check-runs?per_page=100")
    runs = checks.get("check_runs", [])
    failures = [r["name"] for r in runs if r.get("conclusion") in ("failure", "timed_out", "cancelled", "action_required")]
    pending = [r["name"] for r in runs if r.get("status") != "completed"]
    approvals = [user for user, state in latest.items() if state == "APPROVED" and user != pr["user"]["login"]]
    blockers = []
    if pr.get("draft"): blockers.append("draft")
    if not approvals: blockers.append("no_independent_approval")
    if failures: blockers.append("failed_checks")
    if pending: blockers.append("pending_checks")
    if not runs: blockers.append("no_check_runs_observed")
    if checks.get("total_count", 0) > len(runs): blockers.append("check_runs_pagination_incomplete")
    return {"repo": repo, "pr": number, "head_sha": sha, "draft": pr["draft"],
            "independent_approvals": approvals, "failed_checks": failures,
            "pending_checks": pending, "blockers": blockers, "assessment": "needs_review" if blockers else "evidence_present_not_release_authorization"}

def main():
    findings = []
    errors = []
    for repo in REPOS:
        try:
            prs = get("/repos/" + repo + "/pulls?state=open&per_page=100")
            if len(prs) == 100: errors.append(repo + ": PR pagination incomplete")
            for pr in prs:
                try: findings.append(inspect(repo, pr))
                except (urllib.error.HTTPError, urllib.error.URLError, ValueError, KeyError) as exc:
                    errors.append(repo + "#" + str(pr["number"]) + ": " + str(exc))
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError, KeyError) as exc:
            errors.append(repo + ": " + str(exc))
    print(json.dumps({"kind": "read_only_release_evidence", "findings": findings, "errors": errors}, indent=2))
    if errors: return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
