#!/usr/bin/env python3
"""Route structured follow-up requests created by autonomous project agents.

A project agent may write JSON request envelopes to `.kueper/outbox/`. This router
validates the envelope against the ecosystem registry, applies recursion/deduplication
limits, and creates a canonical External Task in the target repository.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.github.com"
ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "registry" / "projects.json"
MAX_DEPTH = int(os.environ.get("KUEPER_MAX_FOLLOWUP_DEPTH", "3"))
MAX_ROUTES = int(os.environ.get("KUEPER_MAX_FOLLOWUPS", "10"))


def gh(token: str, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode(errors="replace")
        raise RuntimeError(f"GitHub {method} {path}: HTTP {exc.code}: {payload}") from exc


def codes() -> dict[str, str]:
    return {
        "ecosystem": "ECO", "knowledge-graph": "KG", "ssf": "SSF", "noxia": "NOXIA",
        "noxia-universe": "NXU", "mishkenaz": "MISH", "omnizedenz": "OMNI",
        "avi-modell": "AVI", "contracomology": "CONTRA", "kueper-archive-schema": "ARCH",
        "endia": "ENDIA", "zereya": "ZEREYA", "davaru": "DAVARU",
        "fluide-hermeneutik": "FLHERM", "resonanz-ethik": "RESETH",
        "kueper-com": "KUE", "ota": "OTA", "thomas-kueper-de": "TKD",
    }


def registry() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    by_id, by_code = {}, {}
    for p in data["projects"]:
        if p.get("enabled", True) and p["id"] in codes():
            q = dict(p)
            q["code"] = codes()[p["id"]]
            by_id[p["id"]] = q
            by_code[q["code"]] = q
    return by_id, by_code


def get_file(token: str, repo: str, path: str, ref: str) -> dict[str, Any] | None:
    p = "/".join(urllib.parse.quote(x, safe="") for x in path.split("/"))
    try:
        return gh(token, "GET", f"/repos/{repo}/contents/{p}?ref={urllib.parse.quote(ref, safe='')}")
    except RuntimeError as exc:
        if "HTTP 404" in str(exc):
            return None
        raise


def list_dir(token: str, repo: str, path: str, ref: str) -> list[dict[str, Any]]:
    x = get_file(token, repo, path, ref)
    return x if isinstance(x, list) else []


def repo_default(token: str, repo: str) -> str:
    return gh(token, "GET", f"/repos/{repo}")["default_branch"]


def decode(payload: dict[str, Any]) -> str:
    import base64
    return base64.b64decode(payload.get("content", "")).decode()


def fingerprint(source: str, target: str, title: str, requested_change: str) -> str:
    norm = "|".join(x.strip().lower() for x in (source, target, title, requested_change))
    return hashlib.sha256(norm.encode()).hexdigest()[:16]


def validate(env: dict[str, Any], source_code: str, by_code: dict[str, dict[str, Any]]) -> list[str]:
    errors = []
    required = ("target", "title", "reason", "requested_change", "expected_result")
    for key in required:
        if not isinstance(env.get(key), str) or not env[key].strip():
            errors.append(f"missing:{key}")
    if env.get("target") not in by_code:
        errors.append("unknown-target")
    if env.get("target") == source_code:
        errors.append("same-source-target")
    depth = env.get("depth", 1)
    if not isinstance(depth, int) or depth < 1 or depth > MAX_DEPTH:
        errors.append("depth-limit")
    if env.get("priority", "medium") not in {"low", "medium", "high", "critical"}:
        errors.append("invalid-priority")
    return errors


def existing_fingerprints(token: str, target: dict[str, Any]) -> set[str]:
    branch = repo_default(token, target["repository"])
    found: set[str] = set()
    for state in ("open", "parked", "done"):
        for item in list_dir(token, target["repository"], f"external-tasks/{state}", branch):
            if item.get("type") != "file" or not item.get("name", "").endswith(".md"):
                continue
            payload = get_file(token, target["repository"], item["path"], branch)
            if isinstance(payload, dict):
                m = re.search(r"^routing_fingerprint:\s*['\"]?([0-9a-f]+)", decode(payload), re.M)
                if m:
                    found.add(m.group(1))
    return found


def next_id(token: str, source: str, target: dict[str, Any], date: str) -> tuple[str, str]:
    branch = repo_default(token, target["repository"])
    prefix = f"EXT-{source}-{target['code']}-{date.replace('-', '')}-"
    nums = []
    for state in ("open", "parked", "done", "rejected"):
        for item in list_dir(token, target["repository"], f"external-tasks/{state}", branch):
            name = item.get("name", "")
            m = re.match(re.escape(prefix) + r"(\d{3})\.md$", name)
            if m:
                nums.append(int(m.group(1)))
    ident = f"{prefix}{max(nums, default=0) + 1:03d}"
    return ident, branch


def markdown(env: dict[str, Any], ident: str, source: str, target: str, fp: str, today: str) -> str:
    affects = env.get("affects") or [source, target]
    affects_s = ", ".join(str(x) for x in affects)
    parent = str(env.get("parent_task") or "")
    depth = int(env.get("depth", 1))
    return f'''---
id: {ident}
title: {env['title'].strip()}
status: open
source: {source}
target: {target}
created: {today}
requested_by: autonomous-project-loop
priority: {env.get('priority', 'medium')}
affects: [{affects_s}]
routing_fingerprint: {fp}
parent_task: {parent}
routing_depth: {depth}
---

## Anlass

{env['reason'].strip()}

## Gewünschte Änderung

{env['requested_change'].strip()}

## Begründung

Dieser Bedarf wurde im zuständigen Quellprojekt während der autonomen Bearbeitung erkannt und liegt fachlich im Ziel-Repository `{target}`.

## Betroffene Repositories

- `{source}`
- `{target}`

## Erwartetes Ergebnis

{env['expected_result'].strip()}

## Hinweise

Automatisch gerouteter Folge-Request. Parent: `{parent or 'none'}`. Routing-Tiefe: {depth}/{MAX_DEPTH}.
'''


def route_envelope(token: str, source_project: dict[str, Any], env: dict[str, Any], by_code: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source = source_project["code"]
    errors = validate(env, source, by_code)
    if errors:
        return {"result": "rejected-envelope", "errors": errors}
    target = by_code[env["target"]]
    fp = fingerprint(source, target["code"], env["title"], env["requested_change"])
    if fp in existing_fingerprints(token, target):
        return {"result": "duplicate", "fingerprint": fp, "target": target["repository"]}
    today = dt.date.today().isoformat()
    ident, branch = next_id(token, source, target, today)
    path = f"external-tasks/open/{ident}.md"
    content = markdown(env, ident, source, target["code"], fp, today)
    gh(token, "PUT", f"/repos/{target['repository']}/contents/{path}", {
        "message": f"chore(tasks): route {ident}",
        "content": __import__("base64").b64encode(content.encode()).decode(),
        "branch": branch,
    })
    return {"result": "routed", "id": ident, "target": target["repository"], "path": path, "fingerprint": fp}


def main() -> int:
    token = os.environ.get("KUEPER_BOT_TOKEN")
    if not token:
        raise SystemExit("KUEPER_BOT_TOKEN is required")
    by_id, by_code = registry()
    results = []
    routed = 0
    for source_project in by_id.values():
        if routed >= MAX_ROUTES:
            break
        repo = source_project["repository"]
        branch = repo_default(token, repo)
        for item in list_dir(token, repo, ".kueper/outbox", branch):
            if routed >= MAX_ROUTES:
                break
            if item.get("type") != "file" or not item.get("name", "").endswith(".json"):
                continue
            payload = get_file(token, repo, item["path"], branch)
            if not isinstance(payload, dict):
                continue
            try:
                env = json.loads(decode(payload))
            except Exception as exc:
                results.append({"source": repo, "file": item["path"], "result": "invalid-json", "error": str(exc)})
                continue
            result = route_envelope(token, source_project, env, by_code)
            result.update({"source": repo, "file": item["path"]})
            results.append(result)
            if result["result"] == "routed":
                routed += 1
    print(json.dumps({"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "routed": routed, "results": results}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
