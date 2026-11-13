#!/usr/bin/env python3
"""Wöchentlicher Gesundheitsbericht der Control Plane (ECO-OPS-20261028-weekly-health).

Führt zusammen, was sonst verstreut liegt, und zeigt Trends gegenüber der
Vorwoche – nur lesend, nur stdlib:

1. je registriertem Repo (``registry/projects.json``, ``enabled: true``):
   Erfolgsquote je Workflow (7 Tage), längste Rotphase, offene PRs nach Alter
   (0–7, 8–30, > 30 Tage), Anzahl Branches;
2. offene External Tasks dieses Repos nach Alter;
3. Research-Queue (``research/queue/*.json``): Verteilung nach Status,
   Top-3-Fehlergründe, Durchsatz je Woche, Anteil ``needs-review`` je
   Evidenzprofil.

Der Task-Bus (Punkt 3 der Task) wird noch nicht erhoben – dafür fehlt eine
freigegebene lesende RPC ohne Ledger-Details; der Bericht sagt das offen.

    GH_TOKEN=… python3 tools/ops/weekly_health.py \
        [--root .] [--out-md status/health-weekly.md] [--out-json status/health-weekly.json] \
        [--alert-file external-tasks/open/ECO-OPS-health-alert.md] [--no-github]

Die Vorwoche wird aus der vorhandenen ``--out-json``-Datei gelesen, bevor sie
überschrieben wird. Ohne Token (oder mit ``--no-github``) entfallen die
GitHub-Kennzahlen; sie werden als „nicht erhoben“ ausgewiesen, nie als grün.
Exit 0 immer, außer bei Aufruffehlern – der Bericht ist Beobachtung, kein Gate.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

API = "https://api.github.com"
ALERT_TASK_ID = "ECO-OPS-health-alert"

# Schwellwerte (Task: Workflow < 80 % grün, PR > 30 Tage, Profil > 40 % needs-review)
WORKFLOW_MIN_SUCCESS = 0.8
WORKFLOW_MIN_RUNS = 3
PR_MAX_AGE_DAYS = 30
PROFILE_MAX_NEEDS_REVIEW = 0.4
PROFILE_MIN_ITEMS = 5
TASK_MAX_AGE_DAYS = 30

AGE_BUCKETS = ("0-7", "8-30", ">30")


# --------------------------------------------------------------------------
# Hilfen
# --------------------------------------------------------------------------

def parse_ts(value) -> datetime | None:
    """ISO-Zeitstempel oder Datum lesen; ohne Zone gilt UTC."""
    if not value or not isinstance(value, str):
        return None
    text = value.strip().replace("Z", "+00:00")
    for candidate in (text, text[:10]):
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    return None


def age_bucket(days: float) -> str:
    if days <= 7:
        return "0-7"
    if days <= 30:
        return "8-30"
    return ">30"


def iso_week(moment: datetime) -> str:
    year, week, _ = moment.isocalendar()
    return f"{year}-W{week:02d}"


# --------------------------------------------------------------------------
# Auswertelogik (rein, ohne Netz – getestet in test_weekly_health.py)
# --------------------------------------------------------------------------

def workflow_stats(runs: list[dict], now: datetime) -> dict:
    """Erfolgsquote je Workflow und längste Rotphase (Stunden) aus Actions-Läufen.

    Gezählt werden nur abgeschlossene Läufe mit ``success`` oder ``failure``
    (``cancelled``/``skipped`` sind kein Urteil über den Workflow). Eine
    Rotphase reicht vom ersten roten Lauf bis zum nächsten grünen bzw. bis jetzt.
    """
    by_name: dict[str, list[tuple[datetime, str]]] = defaultdict(list)
    for run in runs:
        if run.get("status") != "completed":
            continue
        conclusion = run.get("conclusion")
        if conclusion not in ("success", "failure", "timed_out", "startup_failure"):
            continue
        created = parse_ts(run.get("created_at"))
        if created is None:
            continue
        verdict = "success" if conclusion == "success" else "failure"
        by_name[run.get("name") or "?"].append((created, verdict))

    result = {}
    for name, items in by_name.items():
        items.sort()
        total = len(items)
        ok = sum(1 for _, v in items if v == "success")
        longest = 0.0
        red_since = None
        for moment, verdict in items:
            if verdict == "failure" and red_since is None:
                red_since = moment
            elif verdict == "success" and red_since is not None:
                longest = max(longest, (moment - red_since).total_seconds() / 3600)
                red_since = None
        if red_since is not None:
            longest = max(longest, (now - red_since).total_seconds() / 3600)
        result[name] = {
            "runs": total,
            "success": ok,
            "rate": round(ok / total, 3) if total else None,
            "longest_red_hours": round(longest, 1),
            "red_now": red_since is not None,
        }
    return result


def pr_age_buckets(prs: list[dict], now: datetime) -> dict:
    buckets = {key: 0 for key in AGE_BUCKETS}
    oldest = None
    for pr in prs:
        created = parse_ts(pr.get("created_at"))
        if created is None:
            continue
        days = (now - created).total_seconds() / 86400
        buckets[age_bucket(days)] += 1
        if oldest is None or created < oldest:
            oldest = created
    return {"buckets": buckets, "total": sum(buckets.values()),
            "oldest": oldest.date().isoformat() if oldest else None}


_FRONT_CREATED = re.compile(r"^created:\s*['\"]?(\d{4}-\d{2}-\d{2})", re.MULTILINE)


def task_age_buckets(paths: list[str], now: datetime) -> dict:
    """Offene External Tasks nach Alter; Alter aus ``created:`` im Frontmatter."""
    buckets = {key: 0 for key in AGE_BUCKETS}
    unknown = 0
    over_limit = []
    for path in paths:
        try:
            with open(path, encoding="utf-8") as fh:
                head = fh.read(4000)
        except OSError:
            unknown += 1
            continue
        match = _FRONT_CREATED.search(head)
        created = parse_ts(match.group(1)) if match else None
        if created is None:
            unknown += 1
            continue
        days = (now - created).total_seconds() / 86400
        buckets[age_bucket(days)] += 1
        if days > TASK_MAX_AGE_DAYS:
            over_limit.append(os.path.basename(path)[:-3] if path.endswith(".md") else os.path.basename(path))
    return {"buckets": buckets, "unknown": unknown, "total": sum(buckets.values()) + unknown,
            "over_limit": sorted(over_limit)}


_NOISE = (
    "isn't described by this version", "is not a model this version", "auto-compact",
    "[claude-code:unrecognized_model]", "falling back to the existing research agent",
    "CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT",
)


def failure_reason(item: dict) -> str | None:
    """Kurzer, gruppierbarer Fehlergrund eines Queue-Eintrags (oder None).

    Nimmt die aussagekräftigste Zeile aus ``validation_summary``,
    ``validation_error`` oder ``last_error``: Rauschzeilen der Agent-Hülle werden
    übersprungen, IDs und Zahlenfolgen vereinheitlicht.
    """
    for key in ("validation_summary", "validation_error", "last_error"):
        raw = item.get(key)
        if not raw:
            continue
        if not isinstance(raw, str):
            raw = json.dumps(raw, ensure_ascii=False)
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        useful = [ln for ln in lines if not any(n in ln for n in _NOISE)]
        if not useful:
            continue
        # Endgültiger Fehler steht meist zuletzt (z. B. „API Error: 402 …“).
        line = useful[-1] if re.search(r"error|fail|\d{3}", useful[-1], re.I) else useful[0]
        line = re.sub(r"RES-[0-9A-Z-]+", "RES-…", line)
        line = re.sub(r"user ID \d+", "user ID …", line)
        line = re.sub(r"\s+", " ", line)
        return line[:90]
    return None


def queue_stats(items: list[dict], now: datetime) -> dict:
    status = Counter(item.get("status") or "?" for item in items)
    reasons = Counter()
    for item in items:
        if item.get("status") in ("needs-review", "validation-error"):
            reason = failure_reason(item)
            if reason:
                reasons[reason] += 1
    weekly = Counter()
    since = now - timedelta(weeks=8)
    for item in items:
        created = parse_ts(item.get("created"))
        if created and created >= since:
            weekly[iso_week(created)] += 1
    profiles: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for item in items:
        profile = item.get("evidence_profile") or "ohne Profil"
        profiles[profile][0] += 1
        if item.get("status") == "needs-review":
            profiles[profile][1] += 1
    newest = max((parse_ts(i.get("created")) for i in items if parse_ts(i.get("created"))), default=None)
    return {
        "total": len(items),
        "status": dict(status.most_common()),
        "top_reasons": [{"reason": r, "count": c} for r, c in reasons.most_common(3)],
        "created_per_week": dict(sorted(weekly.items())),
        "needs_review_by_profile": {
            name: {"items": n, "needs_review": nr, "share": round(nr / n, 3) if n else 0.0}
            for name, (n, nr) in sorted(profiles.items())
        },
        "newest_entry": newest.date().isoformat() if newest else None,
    }


def findings(snapshot: dict) -> list[dict]:
    """Schwellwertverstöße, nach Schwere sortiert (höchste zuerst)."""
    found = []
    for repo, data in (snapshot.get("repos") or {}).items():
        for name, wf in (data.get("workflows") or {}).items():
            if wf["runs"] >= WORKFLOW_MIN_RUNS and wf["rate"] is not None and wf["rate"] < WORKFLOW_MIN_SUCCESS:
                found.append({
                    "kind": "workflow", "severity": 1 - wf["rate"] + (0.5 if wf.get("red_now") else 0),
                    "text": f"{repo}: Workflow „{name}“ nur {wf['rate']:.0%} grün ({wf['success']}/{wf['runs']})"
                            + (", derzeit rot" if wf.get("red_now") else ""),
                    "action": f"Letzten roten Lauf von „{name}“ in {repo} ansehen; gleicher Fehler in Folge → Task anlegen.",
                })
        old = ((data.get("pull_requests") or {}).get("buckets") or {}).get(">30", 0)
        if old:
            found.append({
                "kind": "pr", "severity": min(1.0, 0.3 + old / 20),
                "text": f"{repo}: {old} offene PR(s) älter als {PR_MAX_AGE_DAYS} Tage",
                "action": f"Alte PRs in {repo} sichten: übernehmen, neu aufsetzen oder schließen.",
            })
    for name, prof in ((snapshot.get("research_queue") or {}).get("needs_review_by_profile") or {}).items():
        if prof["items"] >= PROFILE_MIN_ITEMS and prof["share"] > PROFILE_MAX_NEEDS_REVIEW:
            found.append({
                "kind": "profile", "severity": prof["share"],
                "text": f"Research-Profil „{name}“: {prof['share']:.0%} needs-review ({prof['needs_review']}/{prof['items']})",
                "action": f"Häufigsten Ablehnungsgrund für „{name}“ prüfen (Validator oder Prompt anpassen).",
            })
    tasks = snapshot.get("external_tasks") or {}
    if tasks.get("over_limit"):
        n = len(tasks["over_limit"])
        found.append({
            "kind": "tasks", "severity": min(1.0, 0.2 + n / 30),
            "text": f"{n} offene External Task(s) älter als {TASK_MAX_AGE_DAYS} Tage",
            "action": "Alte Tasks erledigen, parken (mit Rückfrage) oder schließen.",
        })
    found.sort(key=lambda f: -f["severity"])
    return found


def arrow(current, previous) -> str:
    """↑/↓/→ gegenüber der Vorwoche; ohne Vorwert leer."""
    if previous is None or current is None:
        return ""
    if current > previous:
        return " ↑"
    if current < previous:
        return " ↓"
    return " →"


def _prev(previous: dict | None, *path):
    node = previous
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def render_markdown(snapshot: dict, previous: dict | None) -> str:
    out = [
        "# Wöchentlicher Gesundheitsbericht",
        "",
        f"Stand: {snapshot['generated_at']} – erzeugt von `tools/ops/weekly_health.py` "
        "(ECO-OPS-20261028-weekly-health). Pfeile vergleichen mit "
        + (f"dem Bericht vom {previous['generated_at'][:10]}." if previous else "der Vorwoche (noch keine vorhanden)."),
        "",
        "## Was als Nächstes dran ist",
        "",
    ]
    top = snapshot["findings"][:3]
    if top:
        out += [f"{i}. {f['text']} – {f['action']}" for i, f in enumerate(top, 1)]
    else:
        out.append("Kein Schwellwert überschritten.")
    out += ["", "## Repositories (7 Tage)", ""]
    repos = snapshot.get("repos")
    if not repos:
        out.append(f"Nicht erhoben: {snapshot.get('github_note') or 'kein GitHub-Zugriff'}.")
    else:
        out += ["| Repo | Workflows grün | längste Rotphase | PRs 0–7 / 8–30 / >30 | Branches |",
                "| --- | --- | --- | --- | --- |"]
        for repo, data in repos.items():
            if data.get("error"):
                out.append(f"| {repo} | nicht erhoben ({data['error']}) | – | – | – |")
                continue
            wfs = data.get("workflows") or {}
            runs = sum(w["runs"] for w in wfs.values())
            ok = sum(w["success"] for w in wfs.values())
            rate = round(ok / runs, 3) if runs else None
            prev_rate = _prev(previous, "repos", repo, "summary", "rate")
            red = max((w["longest_red_hours"] for w in wfs.values()), default=0.0)
            prs = data.get("pull_requests") or {}
            b = prs.get("buckets") or {}
            prev_old = _prev(previous, "repos", repo, "pull_requests", "buckets", ">30")
            branches = data.get("branches")
            prev_branches = _prev(previous, "repos", repo, "branches")
            rate_txt = f"{rate:.0%} ({ok}/{runs}){arrow(rate, prev_rate)}" if rate is not None else "keine Läufe"
            out.append(
                f"| {repo} | {rate_txt} | {red:.0f} h | {b.get('0-7', 0)} / {b.get('8-30', 0)} / "
                f"{b.get('>30', 0)}{arrow(b.get('>30', 0), prev_old)} | "
                f"{branches if branches is not None else '–'}{arrow(branches, prev_branches)} |"
            )
        red_wfs = [(repo, name, w) for repo, d in repos.items() for name, w in (d.get("workflows") or {}).items()
                   if w["runs"] >= WORKFLOW_MIN_RUNS and w["rate"] is not None and w["rate"] < WORKFLOW_MIN_SUCCESS]
        if red_wfs:
            out += ["", "Workflows unter 80 % grün:", ""]
            out += [f"- {repo} – {name}: {w['rate']:.0%} ({w['success']}/{w['runs']}), längste Rotphase "
                    f"{w['longest_red_hours']:.0f} h{' – derzeit rot' if w['red_now'] else ''}"
                    for repo, name, w in red_wfs]
    tasks = snapshot.get("external_tasks") or {}
    b = tasks.get("buckets") or {}
    out += ["", "## External Tasks (dieses Repo, `external-tasks/open`)", "",
            f"0–7 Tage: {b.get('0-7', 0)} · 8–30 Tage: {b.get('8-30', 0)} · über 30 Tage: {b.get('>30', 0)}"
            f"{arrow(b.get('>30', 0), _prev(previous, 'external_tasks', 'buckets', '>30'))}"
            + (f" · ohne Datum: {tasks['unknown']}" if tasks.get("unknown") else "")]
    q = snapshot.get("research_queue") or {}
    out += ["", "## Research-Queue", "",
            f"{q.get('total', 0)} Einträge{arrow(q.get('total'), _prev(previous, 'research_queue', 'total'))}, "
            f"neuester vom {q.get('newest_entry') or '–'}.", "",
            "| Status | Anzahl | Vorwoche |", "| --- | --- | --- |"]
    for status, count in (q.get("status") or {}).items():
        before = _prev(previous, "research_queue", "status", status)
        out.append(f"| `{status}` | {count}{arrow(count, before)} | {before if before is not None else '–'} |")
    if q.get("top_reasons"):
        out += ["", "Häufigste Fehlergründe (`needs-review`, `validation-error`):", ""]
        out += [f"{i}. {r['count']}× `{r['reason']}`" for i, r in enumerate(q["top_reasons"], 1)]
    if q.get("created_per_week"):
        out += ["", "Neue Einträge je ISO-Woche (seit 8 Wochen): "
                + ", ".join(f"{w}: {n}" for w, n in q["created_per_week"].items())]
    profiles = [(n, p) for n, p in (q.get("needs_review_by_profile") or {}).items() if p["needs_review"]]
    if profiles:
        out += ["", "| Evidenzprofil | Einträge | needs-review | Anteil |", "| --- | --- | --- | --- |"]
        out += [f"| {n} | {p['items']} | {p['needs_review']} | {p['share']:.0%} |"
                for n, p in sorted(profiles, key=lambda x: -x[1]["share"])]
    out += ["", "## Task-Bus", "",
            "Nicht erhoben – es gibt noch keine freigegebene lesende Kennzahlen-RPC ohne Ledger-Details "
            "(siehe ECO-OPS-20261028-weekly-health).", ""]
    return "\n".join(out)


def render_alert(snapshot: dict, today: str) -> str:
    rows = "\n".join(f"- {f['text']} – {f['action']}" for f in snapshot["findings"])
    return (
        "---\n"
        f"id: {ALERT_TASK_ID}\n"
        "title: Gesundheitsbericht – Schwellwerte überschritten\n"
        "status: open\n"
        f"created: {today}\n"
        "requested_by: tools/ops/weekly_health.py\n"
        "priority: medium\n"
        "type: operations / continuous improvement\n"
        "---\n\n"
        f"# {ALERT_TASK_ID} — Gesundheitsbericht: Schwellwerte überschritten\n\n"
        f"Letzte Prüfung: {today}. Diese Datei wird bei jedem Lauf überschrieben und entfernt, "
        "sobald kein Schwellwert mehr überschritten ist. Details: `status/health-weekly.md`.\n\n"
        "## Befund\n\n"
        f"{rows}\n"
    )


# --------------------------------------------------------------------------
# Datenquellen
# --------------------------------------------------------------------------

class GitHub:
    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "kueper-weekly-health",
        }

    def get_all(self, path: str, params: dict, key: str | None = None, max_pages: int = 10) -> list:
        url = f"{API}{path}?{urllib.parse.urlencode({**params, 'per_page': 100})}"
        items: list = []
        for _ in range(max_pages):
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read() or b"null")
                link = resp.headers.get("Link") or ""
            items.extend(body.get(key, []) if key else body)
            match = re.search(r'<([^>]+)>;\s*rel="next"', link)
            if not match:
                break
            url = match.group(1)
        return items


def collect_repo(gh: GitHub, repo: str, now: datetime) -> dict:
    since = (now - timedelta(days=7)).date().isoformat()
    try:
        runs = gh.get_all(f"/repos/{repo}/actions/runs", {"created": f">={since}"}, key="workflow_runs")
        prs = gh.get_all(f"/repos/{repo}/pulls", {"state": "open"})
        branches = gh.get_all(f"/repos/{repo}/branches", {}, max_pages=30)
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}"}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"error": "nicht erreichbar"}
    workflows = workflow_stats(runs, now)
    total = sum(w["runs"] for w in workflows.values())
    ok = sum(w["success"] for w in workflows.values())
    return {
        "workflows": workflows,
        "summary": {"runs": total, "success": ok, "rate": round(ok / total, 3) if total else None},
        "pull_requests": pr_age_buckets(prs, now),
        "branches": len(branches),
    }


def enabled_repos(root: str) -> list[str]:
    with open(os.path.join(root, "registry", "projects.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    projects = data["projects"] if isinstance(data, dict) else data
    return [p["repository"] for p in projects if p.get("enabled") and p.get("repository")]


def load_queue(root: str) -> list[dict]:
    items = []
    for path in sorted(glob.glob(os.path.join(root, "research", "queue", "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            items.append(data)
    return items


def build_snapshot(root: str, now: datetime, token: str | None) -> dict:
    snapshot: dict = {"generated_at": now.replace(microsecond=0).isoformat(), "repos": {}}
    if token:
        gh = GitHub(token)
        for repo in enabled_repos(root):
            snapshot["repos"][repo] = collect_repo(gh, repo, now)
    else:
        snapshot["github_note"] = "kein Token (GH_TOKEN/GITHUB_TOKEN) oder --no-github"
    open_tasks = sorted(glob.glob(os.path.join(root, "external-tasks", "open", "*.md")))
    snapshot["external_tasks"] = task_age_buckets(open_tasks, now)
    snapshot["research_queue"] = queue_stats(load_queue(root), now)
    snapshot["findings"] = findings(snapshot)
    return snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-md", default="status/health-weekly.md")
    parser.add_argument("--out-json", default="status/health-weekly.json")
    parser.add_argument("--alert-file", help="rollierende Alert-Task pflegen (überschreiben bzw. entfernen)")
    parser.add_argument("--no-github", action="store_true", help="GitHub-Kennzahlen nicht erheben")
    args = parser.parse_args(argv)

    now = datetime.now(timezone.utc)
    previous = None
    if os.path.exists(args.out_json):
        try:
            with open(args.out_json, encoding="utf-8") as fh:
                previous = json.load(fh)
        except (OSError, ValueError):
            previous = None
    token = None if args.no_github else (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
    snapshot = build_snapshot(args.root, now, token)

    os.makedirs(os.path.dirname(args.out_md) or ".", exist_ok=True)
    with open(args.out_md, "w", encoding="utf-8") as fh:
        fh.write(render_markdown(snapshot, previous))
    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    if args.alert_file:
        if snapshot["findings"]:
            with open(args.alert_file, "w", encoding="utf-8") as fh:
                fh.write(render_alert(snapshot, now.date().isoformat()))
        elif os.path.exists(args.alert_file):
            os.remove(args.alert_file)
    print(f"{len(snapshot['findings'])} Schwellwertverstöße; Bericht: {args.out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
