#!/usr/bin/env python3
"""Ingest canonical open External Tasks from registered repositories into the V7 task bus.

GitHub remains the audit/source document for cross-repository requests. The Supabase
`ecosystem.tasks` table is the operational execution queue. Idempotency keys make the
scan safe to run repeatedly.
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

GITHUB_API = "https://api.github.com"
ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "registry" / "projects.json"
MAX_INGEST = int(os.environ.get("KUEPER_MAX_EXTERNAL_INGEST", "5"))

CODES_TO_IDS = {
    "ECO": "ecosystem",
    "KG": "knowledge-graph",
    "SSF": "ssf",
    "NOXIA": "noxia",
    "NXU": "noxia-universe",
    "MISH": "mishkenaz",
    "OMNI": "omnizedenz",
    "AVI": "avi-modell",
    "CONTRA": "contracomology",
    "ARCH": "kueper-archive-schema",
    "ENDIA": "endia",
    "ZEREYA": "zereya",
    "DAVARU": "davaru",
    "FLHERM": "fluide-hermeneutik",
    "RESETH": "resonanz-ethik",
    "KUE": "kueper-com",
    "OTA": "ota",
    "TKD": "thomas-kueper-de",
}


def gh(token: str, path: str) -> Any:
    req = urllib.request.Request(GITHUB_API + path)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"GitHub GET {path}: HTTP {exc.code}: {body}") from exc


def rpc(base: str, secret: str, name: str, payload: dict[str, Any]) -> Any:
    req = urllib.request.Request(
        f"{base.rstrip('/')}/rest/v1/rpc/{name}",
        data=json.dumps(payload).encode(),
        method="POST",
    )
    req.add_header("apikey", secret)
    req.add_header("Authorization", f"Bearer {secret}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            data = json.loads(raw) if raw else None
            if isinstance(data, list) and len(data) == 1:
                return data[0]
            return data
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"Supabase RPC {name}: HTTP {exc.code}: {body}") from exc


def enc(path: str) -> str:
    return "/".join(urllib.parse.quote(x, safe="") for x in path.split("/"))


def default_branch(token: str, repo: str) -> str:
    return gh(token, f"/repos/{repo}")["default_branch"]


def list_open(token: str, repo: str, branch: str) -> list[dict[str, Any]]:
    data = gh(token, f"/repos/{repo}/contents/external-tasks/open?ref={urllib.parse.quote(branch, safe='')}")
    return data if isinstance(data, list) else []


def read_file(token: str, repo: str, path: str, branch: str) -> str:
    data = gh(token, f"/repos/{repo}/contents/{enc(path)}?ref={urllib.parse.quote(branch, safe='')}")
    if not isinstance(data, dict):
        raise RuntimeError(f"could not read {repo}:{path}")
    return base64.b64decode(data.get("content", "")).decode("utf-8")


def frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.S)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip().strip('"\'')
    return out


def section(text: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)"
    m = re.search(pattern, text, re.M | re.S)
    return m.group(1).strip() if m else ""


def resolve_project(value: str | None, fallback: str, by_id: dict[str, dict[str, Any]]) -> str:
    raw = (value or "").strip()
    if raw in by_id:
        return raw
    upper = raw.upper()
    if upper in CODES_TO_IDS and CODES_TO_IDS[upper] in by_id:
        return CODES_TO_IDS[upper]
    normalized = raw.lower().replace("_", "-")
    for pid, p in by_id.items():
        if normalized in {pid.lower(), str(p.get("name", "")).lower().replace(" ", "-")}:
            return pid
    return fallback


def main() -> int:
    gh_token = os.environ.get("KUEPER_BOT_TOKEN")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_secret = os.environ.get("SUPABASE_SECRET_KEY")
    missing = [k for k, v in {
        "KUEPER_BOT_TOKEN": gh_token,
        "SUPABASE_URL": supabase_url,
        "SUPABASE_SECRET_KEY": supabase_secret,
    }.items() if not v]
    if missing:
        raise SystemExit(f"missing required secrets: {', '.join(missing)}")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in registry["projects"] if p.get("enabled", True)}
    results: list[dict[str, Any]] = []
    ingested = 0

    for target_id, project in by_id.items():
        if ingested >= MAX_INGEST:
            break
        repo = project["repository"]
        branch = default_branch(gh_token, repo)
        for item in sorted(list_open(gh_token, repo, branch), key=lambda x: x.get("name", "")):
            if ingested >= MAX_INGEST:
                break
            if item.get("type") != "file" or not item.get("name", "").endswith(".md"):
                continue

            path = item["path"]
            text = read_file(gh_token, repo, path, branch)
            fm = frontmatter(text)
            if fm.get("status", "open").lower() != "open":
                continue

            external_id = fm.get("id") or Path(path).stem
            source_id = resolve_project(fm.get("source"), "ecosystem", by_id)
            resolved_target = resolve_project(fm.get("target"), target_id, by_id)
            if resolved_target != target_id:
                results.append({"path": path, "repository": repo, "result": "target-mismatch", "declared_target": resolved_target, "repository_target": target_id})
                continue

            requested_change = section(text, "Gewünschte Änderung")
            expected_result = section(text, "Erwartetes Ergebnis")
            reason = section(text, "Anlass") or section(text, "Begründung")
            instruction = requested_change or f"Bearbeite den External Task {external_id} gemäß Repository-Governance."
            if expected_result:
                instruction += f"\n\nErwartetes Ergebnis:\n{expected_result}"

            priority = fm.get("priority", "medium").lower()
            if priority not in {"low", "medium", "high", "critical"}:
                priority = "medium"

            payload = {
                "instruction": instruction,
                "external_task_id": external_id,
                "external_task_path": path,
                "title": fm.get("title") or external_id,
                "reason": reason,
                "source_repository": by_id.get(source_id, {}).get("repository"),
                "target_repository": repo,
                "routing_fingerprint": fm.get("routing_fingerprint"),
                "autonomous_ingest": True,
                "allow_repository_changes": True,
                "allow_pull_request": True,
                "allow_merge": False,
            }
            idem = f"external-task:{repo}:{external_id}"
            created = rpc(supabase_url, supabase_secret, "kueper_create_task", {
                "p_type": "IMPLEMENT_EXTERNAL_REQUIREMENT",
                "p_source_project": source_id,
                "p_target_project": target_id,
                "p_payload": payload,
                "p_priority": priority,
                "p_external_id": external_id,
                "p_idempotency_key": idem,
                "p_preferred_provider": "deepseek",
                "p_preferred_model": "deepseek-v4-flash",
                "p_repository": repo,
                "p_metadata": {"actor": "external-task-ingestor", "source": "github-external-task"},
            })
            task_id = created.get("id") if isinstance(created, dict) else None
            results.append({"path": path, "repository": repo, "external_id": external_id, "task_id": task_id, "result": "queued-or-existing"})
            ingested += 1

    print(json.dumps({"ingested": ingested, "limit": MAX_INGEST, "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
