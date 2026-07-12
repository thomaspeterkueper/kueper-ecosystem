#!/usr/bin/env python3
"""
KUEPER Ecosystem — GitHub Collector v1
Umsetzung von ECO-ARC-0005, erster Umsetzungsumfang (GitHub-basierte Zustaende).

Aufgabe:
  Soll (registry/projects.json) mit Ist (GitHub) vergleichen und einen
  normalisierten Snapshot erzeugen. Der Collector prueft ausschliesslich
  lesend, schreibt nichts in Ziel-Repositories und gibt keine Secrets aus.

Nutzung:
  GH_TOKEN=<token> python3 tools/collector/collect.py > status/snapshot.json

Zustandswerte je Check: ok | warning | error | unknown | not_applicable
Gesamtstatus je Projekt:  healthy | degraded | critical | unknown
Ein gruener Gesamtstatus wird nie aus fehlenden Daten abgeleitet.
"""
import json, os, sys, datetime, urllib.request, urllib.error

API = "https://api.github.com"
REG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "registry", "projects.json")


def _token():
    t = os.environ.get("GH_TOKEN")
    if not t:
        sys.stderr.write("GH_TOKEN nicht gesetzt.\n")
        sys.exit(2)
    return t


def gh(path, token):
    req = urllib.request.Request(API + path)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None
    except urllib.error.URLError:
        return 0, None


def path_exists(repo, branch, path, token):
    status, _ = gh(f"/repos/{repo}/contents/{path}?ref={branch}", token)
    return status == 200


def collect_project(p, id_to_repo, token):
    repo = p["repository"]
    checks = {}
    project = {
        "id": p["id"],
        "name": p["name"],
        "repository": repo,
        "role": p["role"],
        "enabled": p.get("enabled", True),
        "checks": checks,
    }

    status, data = gh(f"/repos/{repo}", token)
    if status != 200:
        checks["repository_reachable"] = {
            "state": "error",
            "detail": f"HTTP {status}",
        }
        project["overall"] = "critical"
        return project

    branch = data.get("default_branch")
    checks["repository_reachable"] = {"state": "ok", "detail": branch}
    project["default_branch"] = branch
    project["private"] = data.get("private")
    project["last_push"] = data.get("pushed_at")

    # offene PRs
    st, prs = gh(f"/repos/{repo}/pulls?state=open&per_page=100", token)
    if st == 200 and isinstance(prs, list):
        checks["open_pull_requests"] = {"state": "ok", "detail": len(prs)}
    else:
        checks["open_pull_requests"] = {"state": "unknown", "detail": None}

    # Governance: required_paths
    req_paths = p.get("governance", {}).get("required_paths", [])
    missing = [rp for rp in req_paths if not path_exists(repo, branch, rp, token)]
    checks["governance_required_paths"] = {
        "state": "error" if missing else "ok",
        "detail": {"missing": missing, "checked": len(req_paths)},
    }

    # offene external-tasks
    st, listing = gh(f"/repos/{repo}/contents/external-tasks/open?ref={branch}", token)
    if st == 200 and isinstance(listing, list):
        open_tasks = sorted(f["name"] for f in listing if f["name"].endswith(".md"))
        checks["external_tasks_open"] = {
            "state": "warning" if open_tasks else "ok",
            "detail": {"count": len(open_tasks), "files": open_tasks},
        }
    elif any("external-tasks" in rp for rp in req_paths):
        checks["external_tasks_open"] = {"state": "unknown", "detail": None}
    else:
        checks["external_tasks_open"] = {"state": "not_applicable", "detail": None}

    # Integrationen: Ziel als aktiviertes Projekt registriert?
    integ_results = []
    for integ in p.get("integrations", []):
        tgt = integ["target"]
        registered = tgt in id_to_repo
        integ_results.append({
            "target": tgt,
            "required": integ["required"],
            "state": "ok" if registered else ("error" if integ["required"] else "warning"),
            "detail": "registered" if registered else "target not in registry",
        })
    checks["integrations"] = {
        "state": _worst(r["state"] for r in integ_results) if integ_results else "not_applicable",
        "detail": integ_results,
    }

    project["overall"] = _overall(checks)
    return project


_ORDER = {"ok": 0, "not_applicable": 0, "unknown": 1, "warning": 2, "error": 3}


def _worst(states):
    return max(states, key=lambda s: _ORDER.get(s, 1)) if states else "unknown"


def _overall(checks):
    states = [c["state"] for c in checks.values()]
    if any(s == "error" for s in states):
        return "critical"
    if any(s == "unknown" for s in states):
        # Warnungen zaehlen als degraded, aber fehlende Daten duerfen kein gruen ergeben
        return "degraded" if any(s == "warning" for s in states) else "unknown"
    if any(s == "warning" for s in states):
        return "degraded"
    return "healthy"


def main():
    token = _token()
    with open(os.path.abspath(REG_PATH), encoding="utf-8") as f:
        reg = json.load(f)
    id_to_repo = {p["id"]: p["repository"] for p in reg["projects"]}

    projects = [collect_project(p, id_to_repo, token) for p in reg["projects"]]

    counts = {}
    for p in projects:
        counts[p["overall"]] = counts.get(p["overall"], 0) + 1
    total_open_tasks = sum(
        p["checks"].get("external_tasks_open", {}).get("detail", {}).get("count", 0)
        if isinstance(p["checks"].get("external_tasks_open", {}).get("detail"), dict) else 0
        for p in projects
    )

    snapshot = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0).isoformat(),
        "collector_version": "1.0.0",
        "registry_schema_version": reg.get("schema_version"),
        "summary": {
            "projects": len(projects),
            "overall_counts": counts,
            "open_external_tasks_total": total_open_tasks,
        },
        "projects": projects,
    }
    json.dump(snapshot, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
