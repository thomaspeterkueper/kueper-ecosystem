#!/usr/bin/env python3
"""Bridge OTA's archive-quality workqueue into the KUEPER Research Executor.

The bridge clones the current OTA repository, runs its own content analyzer, then asks the
configured discovery agent to select only genuine external-evidence gaps. Metadata-only
problems and fictional/canonical gaps are deliberately excluded from web research.
Selected items are persisted in the existing central research queue and retain the exact
OTA source path/signature so execute.py can load the declared source document fail-closed.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.github.com"
CONTROL = "thomaspeterkueper/kueper-ecosystem"
OTA_REPO = "thomaspeterkueper/overtime-archive.org"
ROOT = Path(__file__).resolve().parents[2]
POLICY = json.loads((ROOT / "research/policy.json").read_text(encoding="utf-8"))
PROFILE_NAME = "ota-archive-evidence"
PROFILE = POLICY["evidence_profiles"][PROFILE_NAME]
MAX_INPUT_DOCS = 48
MAX_QUEUE = 2


def gh(token: str, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"GitHub HTTP {exc.code}: {exc.read().decode(errors='replace')}"
        ) from exc


def run(cmd: list[str], cwd: Path | None = None) -> str:
    cp = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if cp.returncode:
        raise RuntimeError(cp.stdout)
    return cp.stdout


def auth_url(repo: str, token: str) -> str:
    return f"https://x-access-token:{urllib.parse.quote(token, safe='')}@github.com/{repo}.git"


def scalar(frontmatter: str, key: str) -> str:
    import re

    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", frontmatter, flags=re.MULTILINE)
    if not match:
        return ""
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def inline_list(frontmatter: str, key: str) -> list[str]:
    import re

    match = re.search(rf"^{re.escape(key)}:\s*\[(.*?)\]\s*$", frontmatter, flags=re.MULTILINE)
    if not match:
        return []
    return [
        item.strip().strip("\"'")
        for item in match.group(1).split(",")
        if item.strip().strip("\"'")
    ]


def read_frontmatter(path: Path) -> tuple[str, str]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return "", raw
    parts = raw.split("---", 2)
    return (parts[1] if len(parts) > 2 else ""), (parts[2] if len(parts) > 2 else raw)


def queue_history(token: str) -> list[dict[str, Any]]:
    try:
        entries = gh(token, "GET", f"/repos/{CONTROL}/contents/research/queue?ref=main")
    except Exception:
        return []
    result: list[dict[str, Any]] = []
    for entry in entries if isinstance(entries, list) else []:
        if entry.get("type") != "file" or not entry.get("name", "").endswith(".json"):
            continue
        try:
            payload = gh(token, "GET", f"/repos/{CONTROL}/contents/{entry['path']}?ref=main")
            raw = base64.b64decode(payload.get("content", "")).decode()
            data = json.loads(raw)
            if isinstance(data, dict):
                result.append(data)
        except Exception:
            pass
    return result


def existing_ota_topics(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    same = [item for item in history if item.get("source_project") == "ota"]
    same.sort(key=lambda item: item.get("created", "") or "", reverse=True)
    return [
        {
            "id": item.get("id"),
            "status": item.get("status"),
            "document_signature": item.get("document_signature"),
            "title": item.get("title"),
            "question": item.get("question"),
        }
        for item in same[:40]
    ]


def build_workqueue(ota_root: Path) -> list[dict[str, Any]]:
    analyzer = ota_root / "scripts" / "analyze-archive-content.mjs"
    if not analyzer.exists():
        raise RuntimeError("OTA analyzer missing: scripts/analyze-archive-content.mjs")
    run(["node", str(analyzer)], cwd=ota_root)
    quality_path = ota_root / "src" / "data" / "archive-quality.generated.json"
    if not quality_path.exists():
        raise RuntimeError("OTA analyzer did not generate archive-quality.generated.json")
    quality = json.loads(quality_path.read_text(encoding="utf-8"))
    docs = quality.get("documents", [])
    candidates: list[dict[str, Any]] = []
    for doc in docs:
        file_name = doc.get("file")
        if not file_name:
            continue
        source = ota_root / "src" / "content" / "documents" / file_name
        if not source.exists():
            continue
        fm, _body = read_frontmatter(source)
        signature = scalar(fm, "signature") or doc.get("signature") or source.stem
        epistemic = inline_list(fm, "epistemicStatus")
        flags = list(doc.get("quality", {}).get("flags", []))
        substance = doc.get("quality", {}).get("substance")
        # The bridge surfaces editorial pressure, but does not equate shortness with a
        # research need. The agent below must still identify a real externally-checkable gap.
        candidates.append(
            {
                "source_path": f"src/content/documents/{file_name}",
                "document_signature": signature,
                "canonical_title": doc.get("canonical", {}).get("title"),
                "extracted_title": doc.get("extracted", {}).get("title"),
                "extracted_classification": doc.get("extracted", {}).get("classification"),
                "epistemic_status": epistemic,
                "substance": substance,
                "words": doc.get("metrics", {}).get("words"),
                "headings": doc.get("metrics", {}).get("headings"),
                "inline_reference_targets": doc.get("metrics", {}).get("inlineReferenceTargets"),
                "quality_flags": flags,
                "relation_gap": doc.get("quality", {}).get("relationGap", False),
                "priority": doc.get("quality", {}).get("priority", 0),
            }
        )
    candidates.sort(
        key=lambda item: (
            item.get("substance") == "FRAGMENT",
            item.get("substance") == "KURZ",
            item.get("priority", 0),
        ),
        reverse=True,
    )
    return candidates[:MAX_INPUT_DOCS]


def prompt(workqueue: list[dict[str, Any]], previous: list[dict[str, Any]]) -> str:
    claim_classes = PROFILE.get("claim_classes", {})
    return f'''You are the OTA research-workqueue gate for the KUEPER ecosystem.

You are NOT a general gap generator. You receive the OTA archive's own current editorial diagnostics. Select at most {MAX_QUEUE} items that genuinely need OUTSIDE EVIDENCE and are worth sending to the existing KUEPER Research Executor.

OTA workqueue snapshot:
{json.dumps(workqueue, indent=2, ensure_ascii=False)}

Recent/prior OTA research topics (avoid semantic duplicates):
{json.dumps(previous, indent=2, ensure_ascii=False)}

Allowed OTA claim classes:
{json.dumps(claim_classes, indent=2, ensure_ascii=False)}

Rules:
1. A generic title, generic summary, missing frontmatter relation, short document, missing visual, or formatting problem is NOT by itself a research topic. Those are local editorial/metadata tasks.
2. Pure F/W canon gaps without a real-world anchor are NOT external research topics. Leave them for editorial/canonical review.
3. T/H/S may be researched only for real premises, constraints, counterevidence, plausibility anchors or falsifiability. Do not ask the web to validate a fictional/theoretical postulate.
4. R and R-Anker are eligible when there is a concrete externally checkable claim whose verification, freshness or conflict status materially improves the document.
5. Read the exact source document before proposing a topic. `source_path` in the workqueue is authoritative. Do not infer the research question from the diagnostic row alone.
6. Prefer documents where external evidence can clarify a specific scientific, historical, archaeological, linguistic or technical assertion. Do not pad the archive merely because a document is short.
7. Preserve `document_signature` and `source_path` exactly. The executor will fail closed if the declared source cannot be loaded.
8. Avoid previous topics unless there is a materially new unresolved dimension. If related, list valid prior IDs and explain novelty.
9. `publication_route_hint` is advisory only: use `real_scientific_epaper` only if the research could stand as separable real-world science; otherwise use `fictional_archive_document`.
10. Relevance score is the mean of project_relevance, cross_project_reuse, uncertainty and evidence_potential. Require >= {POLICY['minimum_relevance_score']}.

Write ONLY `.kueper-ota-workqueue-discovery.json` with:
{{"gaps":[{{
  "source_path":"src/content/documents/...",
  "document_signature":"OTA-...",
  "gap_kind":"external_evidence",
  "title":"...",
  "question":"...",
  "why_now":"...",
  "claim_classes":["R"],
  "real_world_anchor":"...",
  "publication_route_hint":"fictional_archive_document",
  "suggested_languages":["de","en"],
  "related_research_ids":[],
  "novelty_reason":"...",
  "project_relevance":0.0,
  "cross_project_reuse":0.0,
  "uncertainty":0.0,
  "evidence_potential":0.0,
  "relevance_score":0.0
}}]}}
Do not edit any other file.
'''


def main() -> int:
    token = os.environ.get("KUEPER_BOT_TOKEN")
    if not token:
        raise SystemExit("KUEPER_BOT_TOKEN required")
    history = queue_history(token)
    previous = existing_ota_topics(history)
    existing_fingerprints = {item.get("fingerprint") for item in history if item.get("fingerprint")}
    prior_ids = {item.get("id") for item in history if item.get("source_project") == "ota" and item.get("id")}
    allowed_claims = set(PROFILE.get("claim_classes", {}))
    allowed_routes = set(PROFILE.get("allowed_publication_routes", []))
    temp = Path(tempfile.mkdtemp(prefix="kueper-ota-workqueue-"))
    queued: list[dict[str, Any]] = []
    try:
        run(["git", "clone", "--quiet", "--depth", "1", auth_url(OTA_REPO, token), str(temp)])
        workqueue = build_workqueue(temp)
        agent_cmd = os.environ.get("KUEPER_DISCOVERY_AGENT_CMD", "claude -p --dangerously-skip-permissions").split()
        run(agent_cmd + [prompt(workqueue, previous)], cwd=temp)
        proposal = temp / ".kueper-ota-workqueue-discovery.json"
        if not proposal.exists():
            raise RuntimeError("agent did not create .kueper-ota-workqueue-discovery.json")
        data = json.loads(proposal.read_text(encoding="utf-8"))
        by_path = {item["source_path"]: item for item in workqueue}
        now = dt.datetime.now(dt.timezone.utc)
        for gap in data.get("gaps", [])[:MAX_QUEUE]:
            source_path = gap.get("source_path")
            signature = gap.get("document_signature")
            if gap.get("gap_kind") != "external_evidence" or source_path not in by_path:
                continue
            if signature != by_path[source_path].get("document_signature"):
                continue
            if not (temp / source_path).exists():
                continue
            claim_classes = [c for c in gap.get("claim_classes", []) if isinstance(c, str)]
            if not claim_classes or any(c not in allowed_claims for c in claim_classes):
                continue
            # Pure canon/work-setting proposals are never allowed through the bridge.
            if set(claim_classes).issubset({"F", "W"}):
                continue
            anchor = str(gap.get("real_world_anchor") or "").strip()
            if not anchor:
                continue
            score = float(gap.get("relevance_score", 0))
            if score < float(POLICY["minimum_relevance_score"]):
                continue
            route = gap.get("publication_route_hint") or PROFILE.get("default_publication_route")
            if route not in allowed_routes:
                continue
            related = [rid for rid in gap.get("related_research_ids", []) if rid in prior_ids]
            novelty = str(gap.get("novelty_reason") or "").strip()
            if gap.get("related_research_ids") and not related:
                continue
            if related and len(novelty) < 20:
                continue
            seed = f"ota|{signature}|{gap.get('question')}".lower().strip()
            fingerprint = hashlib.sha256(seed.encode()).hexdigest()[:16]
            if fingerprint in existing_fingerprints:
                continue
            rid = f"RES-{now.strftime('%Y%m%d')}-{fingerprint[:8].upper()}"
            item = {
                "id": rid,
                "status": "queued",
                "created": now.replace(microsecond=0).isoformat(),
                "source_project": "ota",
                "source_repository": OTA_REPO,
                "source_path": source_path,
                "document_signature": signature,
                "title": gap.get("title"),
                "question": gap.get("question"),
                "why_now": gap.get("why_now"),
                "languages": [x for x in gap.get("suggested_languages", []) if isinstance(x, str)][: POLICY["max_languages_per_topic"]] or ["de", "en"],
                "evidence_profile": PROFILE_NAME,
                "claim_classes": claim_classes,
                "real_world_anchor": anchor,
                "publication_route_hint": route,
                "external_research_required": True,
                "project_weight": 0.9,
                "relevance_score": score,
                "scores": {k: gap.get(k) for k in ("project_relevance", "cross_project_reuse", "uncertainty", "evidence_potential")},
                "related_research_ids": related,
                "novelty_reason": novelty or None,
                "workqueue_basis": {
                    "substance": by_path[source_path].get("substance"),
                    "words": by_path[source_path].get("words"),
                    "quality_flags": by_path[source_path].get("quality_flags"),
                },
                "fingerprint": fingerprint,
            }
            encoded = base64.b64encode((json.dumps(item, indent=2, ensure_ascii=False) + "\n").encode()).decode()
            gh(
                token,
                "PUT",
                f"/repos/{CONTROL}/contents/research/queue/{rid}.json",
                {"message": f"research: queue OTA workqueue {rid}", "content": encoded, "branch": "main"},
            )
            existing_fingerprints.add(fingerprint)
            queued.append(item)
    finally:
        shutil.rmtree(temp, ignore_errors=True)

    print(
        json.dumps(
            {
                "source_project": "ota",
                "evidence_profile": PROFILE_NAME,
                "queued": len(queued),
                "queued_ids": [item["id"] for item in queued],
                "items": queued,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
