#!/usr/bin/env python3
"""KUEPER governance sweep — read-only drift detector.

Checks the control plane (decisions/, registry/) and every registered
repository's external-tasks/open/ for exactly the pattern of drift found
manually during interactive governance sessions: decisions missing from
the index, superseded decisions without a backlink, near-duplicate
decision titles (the ECO-ARC-0029/0033 incident), registry entries whose
'code' field disagrees with the ECO-ARC-0006 code table, dangling
integration targets, missing governance paths, and tasks addressed to ECO
sitting unprocessed.

This tool never decides anything and never edits decisions or the
registry. It only reports. See ECO-ARC-0027/0034: governance judgement
calls stay with the owner, this is Execution Infrastructure surfacing
what needs a look, not making the call itself.

Output: status/governance-sweep.json (machine-readable) and
status/governance-sweep.md (human-readable), both always overwritten.
A finding is only turned into an External Task in this repository's own
inbox if its stable id was not already present in the previous run's
report -- repeat sweeps of an unresolved issue do not spam new tasks.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "registry" / "projects.json"
DECISIONS = ROOT / "decisions"
STATUS_JSON = ROOT / "status" / "governance-sweep.json"
STATUS_MD = ROOT / "status" / "governance-sweep.md"
CONTROL_PLANE_REPO = "thomaspeterkueper/kueper-ecosystem"
API = "https://api.github.com"

VALID_ROLES = {
    "control-plane", "application", "engineering", "knowledge-platform",
    "knowledge-graph", "archive", "website", "infrastructure", "authoring",
}
CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*$")
DECISION_FILE_PATTERN = re.compile(r"^ECO-ARC-(\d{4})-2026-DE\.md$")


@dataclass
class Finding:
    id: str
    category: str
    severity: str  # "info" | "warning" | "error"
    message: str


@dataclass
class SweepResult:
    generated_at: str
    findings: list[Finding] = field(default_factory=list)

    def add(self, category: str, severity: str, message: str, key: str) -> None:
        fid = hashlib.sha1(f"{category}:{key}".encode("utf-8")).hexdigest()[:12]
        self.findings.append(Finding(fid, category, severity, message))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^a-z0-9äöüß ]", " ", t)
    t = re.sub(r"\b(zusammenarbeit|am selben repository|konsolidierte fassung)\b", "", t)
    return re.sub(r"\s+", " ", t).strip()


def parse_decision(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    m = DECISION_FILE_PATTERN.match(path.name)
    number = m.group(1) if m else None
    title_match = re.search(r"^#\s*ECO-ARC-\d{4}-2026-DE\s*—\s*(.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else path.stem
    status_match = re.search(r"^Status:\s*(\S+)", text, re.MULTILINE)
    status = status_match.group(1) if status_match else "unknown"
    return {"number": number, "title": title, "status": status, "text": text, "path": path}


def check_decisions(result: SweepResult) -> list[dict[str, Any]]:
    decision_files = sorted(DECISIONS.glob("ECO-ARC-*-2026-DE.md"))
    decisions = [parse_decision(p) for p in decision_files]
    index_text = (DECISIONS / "README.md").read_text(encoding="utf-8")

    # 1. every decision file appears in the index
    for d in decisions:
        marker = f"ECO-ARC-{d['number']}-2026-DE"
        if marker not in index_text:
            result.add(
                "decisions_index_missing", "warning",
                f"{marker} fehlt im Entscheidungs-Index (decisions/README.md).",
                key=marker,
            )

    # 2. superseded decisions should backlink to what superseded them
    for d in decisions:
        if d["status"] == "superseded" and "ECO-ARC-00" not in d["text"].split("superseded", 1)[-1][:400] \
                and not re.search(r"superseded.{0,300}?ECO-ARC-\d{4}", d["text"], re.IGNORECASE | re.DOTALL):
            result.add(
                "superseded_without_backlink", "warning",
                f"ECO-ARC-{d['number']} ist als 'superseded' markiert, aber ohne erkennbaren "
                f"Verweis auf die ablösende Entscheidung im Text.",
                key=d["number"],
            )

    # 3. near-duplicate titles among accepted/active decisions (the 0029/0033 pattern)
    active = [d for d in decisions if d["status"] not in ("superseded", "rejected")]
    seen: dict[str, str] = {}
    for d in active:
        norm = normalize_title(d["title"])
        if not norm:
            continue
        if norm in seen and seen[norm] != d["number"]:
            pair = tuple(sorted([seen[norm], d["number"]]))
            result.add(
                "duplicate_decision_topic", "warning",
                f"ECO-ARC-{pair[0]} und ECO-ARC-{pair[1]} haben nahezu identische Titel "
                f"('{d['title']}') und sind beide aktiv — möglicher Doppel-Kanonisierungsfall "
                f"wie ECO-ARC-0029/0033.",
                key=f"{pair[0]}-{pair[1]}",
            )
        else:
            seen[norm] = d["number"]

    return decisions


def extract_code_table(decisions: list[dict[str, Any]]) -> dict[str, str]:
    codes: dict[str, str] = {}
    zero_six = next((d for d in decisions if d["number"] == "0006"), None)
    if not zero_six:
        return codes
    for line in zero_six["text"].splitlines():
        m = re.match(r"^\|\s*`([A-Z][A-Z0-9]*)`\s*\|\s*`([^`]+)`\s*\|", line)
        if m:
            codes[m.group(1)] = m.group(2)
    return codes


def check_registry(result: SweepResult, code_table: dict[str, str]) -> dict[str, Any]:
    registry = load_json(REGISTRY)
    projects = registry.get("projects", [])
    ids = {p["id"] for p in projects}

    project_codes: dict[str, str] = {}
    for p in projects:
        pid = p["id"]
        if p.get("role") not in VALID_ROLES:
            result.add(
                "registry_invalid_role", "error",
                f"Projekt '{pid}' hat eine unbekannte Rolle: {p.get('role')!r}.",
                key=pid,
            )
        code = p.get("code")
        if code:
            if not CODE_PATTERN.match(code):
                result.add(
                    "registry_invalid_code_format", "error",
                    f"Projekt '{pid}' hat einen Code, der nicht dem Muster entspricht: {code!r}.",
                    key=pid,
                )
            project_codes[pid] = code
        for it in p.get("integrations", []):
            if it.get("target") not in ids:
                result.add(
                    "registry_dangling_integration", "error",
                    f"Projekt '{pid}' referenziert ein nicht existierendes Ziel "
                    f"'{it.get('target')}' in seinen Integrationen.",
                    key=f"{pid}->{it.get('target')}",
                )

    # code table (ECO-ARC-0006) vs registry cross-check
    repo_by_code = {}
    for p in projects:
        c = p.get("code")
        if c:
            repo_by_code[c] = p["repository"].split("/")[-1]
    for code, repo_name in code_table.items():
        actual = repo_by_code.get(code)
        if actual is None:
            result.add(
                "code_table_not_registered", "info",
                f"Code '{code}' ({repo_name}) steht in der ECO-ARC-0006-Tabelle, "
                f"aber kein Registry-Eintrag trägt diesen Code.",
                key=code,
            )
        elif actual != repo_name:
            result.add(
                "code_table_mismatch", "warning",
                f"Code '{code}' zeigt in ECO-ARC-0006 auf '{repo_name}', in der Registry "
                f"aber auf '{actual}'.",
                key=code,
            )
    for pid, code in project_codes.items():
        if code not in code_table:
            result.add(
                "registry_code_not_in_table", "warning",
                f"Projekt '{pid}' trägt Code '{code}', der nicht in der "
                f"ECO-ARC-0006-Codetabelle steht.",
                key=pid,
            )

    return registry


class GitHub:
    def __init__(self, token: str) -> None:
        self.token = token

    def get(self, path: str) -> tuple[int, Any]:
        req = urllib.request.Request(API + path)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/vnd.github+json")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, None

    def contents(self, repo: str, path: str, ref: str) -> Any:
        st, data = self.get(f"/repos/{repo}/contents/{path}?ref={ref}")
        return data if st == 200 else None

    def text(self, repo: str, path: str, ref: str) -> str | None:
        data = self.contents(repo, path, ref)
        if isinstance(data, dict) and data.get("content"):
            return base64.b64decode(data["content"]).decode("utf-8", "replace")
        return None


def check_repositories(result: SweepResult, registry: dict[str, Any], gh: GitHub) -> None:
    for p in registry.get("projects", []):
        if not p.get("enabled") or p.get("provider") != "github":
            continue
        repo = p["repository"]
        pid = p["id"]
        st, info = gh.get(f"/repos/{repo}")
        if st != 200:
            result.add(
                "repository_unreachable", "error",
                f"Repository '{repo}' (Projekt '{pid}') nicht erreichbar (HTTP {st}).",
                key=pid,
            )
            continue
        branch = info["default_branch"]

        for req_path in p.get("governance", {}).get("required_paths", []):
            if gh.contents(repo, req_path, branch) is None:
                result.add(
                    "governance_path_missing", "warning",
                    f"Projekt '{pid}' fehlt der Pflichtpfad '{req_path}'.",
                    key=f"{pid}:{req_path}",
                )

        listing = gh.contents(repo, "external-tasks/open", branch)
        if isinstance(listing, list):
            for f in listing:
                if not f["name"].endswith(".md"):
                    continue
                text = gh.text(repo, f["path"], branch)
                if text and re.search(r"^target:\s*ECO\s*$", text, re.MULTILINE):
                    result.add(
                        "task_addressed_to_eco", "info",
                        f"Offener, an ECO adressierter Task in '{pid}': {f['name']}",
                        key=f"{pid}:{f['name']}",
                    )


def render_markdown(result: SweepResult) -> str:
    lines = [
        "# Governance-Sweep — Bericht",
        "",
        f"Erzeugt: {result.generated_at}",
        "",
        f"**{len(result.findings)} Fund(e)** — "
        f"{sum(1 for f in result.findings if f.severity == 'error')} error, "
        f"{sum(1 for f in result.findings if f.severity == 'warning')} warning, "
        f"{sum(1 for f in result.findings if f.severity == 'info')} info",
        "",
    ]
    if not result.findings:
        lines.append("Keine Auffälligkeiten.")
        return "\n".join(lines) + "\n"
    by_category: dict[str, list[Finding]] = {}
    for f in result.findings:
        by_category.setdefault(f.category, []).append(f)
    for category, items in sorted(by_category.items()):
        lines.append(f"## {category} ({len(items)})")
        for it in items:
            lines.append(f"- **[{it.severity}]** {it.message}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    result = SweepResult(generated_at=datetime.now(timezone.utc).isoformat())

    decisions = check_decisions(result)
    code_table = extract_code_table(decisions)
    registry = check_registry(result, code_table)

    token = os.environ.get("KUEPER_BOT_TOKEN")
    if token:
        gh = GitHub(token)
        check_repositories(result, registry, gh)
    else:
        result.add(
            "sweep_incomplete", "info",
            "KUEPER_BOT_TOKEN nicht gesetzt — Repository-/Task-Prüfungen übersprungen, "
            "nur lokale Kontrollen (Entscheidungen, Registry) ausgeführt.",
            key="no-token",
        )

    previous_ids: set[str] = set()
    if STATUS_JSON.exists():
        try:
            prev = load_json(STATUS_JSON)
            previous_ids = {f["id"] for f in prev.get("findings", [])}
        except Exception:
            previous_ids = set()

    new_findings = [f for f in result.findings if f.id not in previous_ids]

    STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATUS_JSON.write_text(
        json.dumps(
            {
                "generated_at": result.generated_at,
                "findings": [f.__dict__ for f in result.findings],
                "new_since_last_run": [f.__dict__ for f in new_findings],
            },
            indent=2, ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    STATUS_MD.write_text(render_markdown(result), encoding="utf-8")

    print(f"{len(result.findings)} Fund(e), davon {len(new_findings)} neu seit letztem Lauf.")
    for f in new_findings:
        print(f"  NEU [{f.severity}] {f.category}: {f.message}")

    # Signal to the workflow whether a new-findings task should be filed.
    gha_output = os.environ.get("GITHUB_OUTPUT")
    if gha_output:
        with open(gha_output, "a", encoding="utf-8") as fh:
            fh.write(f"has_new_findings={'true' if new_findings else 'false'}\n")
    if new_findings:
        (ROOT / ".governance-sweep-new-findings.json").write_text(
            json.dumps([f.__dict__ for f in new_findings], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
