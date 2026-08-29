#!/usr/bin/env python3
"""Deterministic, document-scoped OTA research discovery.

Unlike the general discovery loop, this sweep does not ask the model to search the
whole OTA repository for a topic. Control-plane code first selects one tracked OTA
document deterministically, pins its current Git revision, builds a tiny workspace
with that document plus at most a few explicitly referenced neighbours, and only
then invokes the discovery agent.

The selected source document is the only file allowed to become `source_path`.
Context excerpts are secondary orientation only.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

import discover as core

PROJECT_ID = "ota"
DOCUMENT_PREFIX = "src/content/documents/"
MAX_CONTEXT_DOCS = int(os.environ.get("KUEPER_OTA_CONTEXT_DOCS", "3"))
MAX_CONTEXT_CHARS = int(os.environ.get("KUEPER_OTA_CONTEXT_CHARS", "6000"))
MAX_GAPS = int(os.environ.get("KUEPER_OTA_MAX_DISCOVERIES", "2"))

SIGNATURE_RE = re.compile(r"\b(OTA-[A-Z]{2,10}-\d{4})\b")

# Cheap deterministic signals. They select what deserves model attention; they do
# not themselves establish evidence quality.
SCORE_PATTERNS: tuple[tuple[re.Pattern[str], int, int], ...] = (
    (re.compile(r"\[R(?:-Anker)?\]", re.I), 8, 10),
    (re.compile(r"\bESTABLISHED\b", re.I), 7, 8),
    (re.compile(r"\[OFFEN\]", re.I), 10, 6),
    (re.compile(r"\b(?:ausstehend|ungeklärt|unklar|dringend|vorläufig|offen)\b", re.I), 5, 8),
    (re.compile(r"\bTODO\b", re.I), 5, 5),
    (re.compile(r"\[H\]", re.I), 4, 6),
    (re.compile(r"\[T\]", re.I), 2, 6),
    (re.compile(r"\bDOI\b|doi\.org/", re.I), 4, 8),
    (re.compile(r"\barXiv\b|arxiv\.org/", re.I), 3, 8),
    (re.compile(r"https?://", re.I), 1, 12),
)
EXTERNAL_SIGNAL_RE = re.compile(
    r"\[R(?:-Anker)?\]|\bESTABLISHED\b|\bDOI\b|doi\.org/|\barXiv\b|arxiv\.org/",
    re.I,
)


def tracked_documents(root: Path) -> list[str]:
    out = core.run(["git", "ls-files"], cwd=root)
    return sorted(
        line.strip()
        for line in out.splitlines()
        if line.startswith(DOCUMENT_PREFIX) and line.endswith(".md")
    )


def blob_sha(root: Path, path: str) -> str:
    return core.run(["git", "rev-parse", f"HEAD:{path}"], cwd=root).strip()


def score_document(text: str) -> int | None:
    if not EXTERNAL_SIGNAL_RE.search(text):
        return None
    score = 0
    for pattern, weight, cap in SCORE_PATTERNS:
        score += min(len(pattern.findall(text)), cap) * weight
    # Tiny tie-breaker toward substantive documents without letting length dominate.
    score += min(len(text) // 8000, 5)
    return score


def already_audited_current_revision(
    history: list[dict[str, Any]], path: str, current_blob: str
) -> bool:
    for item in history:
        if item.get("source_project") != PROJECT_ID or item.get("source_path") != path:
            continue
        old_blob = item.get("source_blob_sha")
        # Legacy source-grounded items did not always record a blob SHA. Treat them
        # as already covered until the document itself changes through a future
        # revision-aware item.
        if not old_blob or old_blob == current_blob:
            return True
    return False


def select_source(
    root: Path, history: list[dict[str, Any]]
) -> tuple[str, str, int, int]:
    candidates: list[tuple[int, str, str]] = []
    for path in tracked_documents(root):
        file_path = root / path
        try:
            text = file_path.read_text(encoding="utf-8")
            current_blob = blob_sha(root, path)
        except Exception:
            continue
        if already_audited_current_revision(history, path, current_blob):
            continue
        score = score_document(text)
        if score is None:
            continue
        candidates.append((score, path, current_blob))

    if not candidates:
        raise RuntimeError("no unreviewed OTA document revision with external evidence signals")

    # Highest deterministic score first; lexical path is a stable tie-breaker.
    candidates.sort(key=lambda row: (-row[0], row[1]))
    score, path, current_blob = candidates[0]
    return path, current_blob, score, len(candidates)


def signature_map(paths: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for path in paths:
        match = SIGNATURE_RE.search(Path(path).name)
        if match:
            out.setdefault(match.group(1), []).append(path)
    return out


def select_context_paths(source_path: str, source_text: str, all_paths: list[str]) -> list[str]:
    mapping = signature_map(all_paths)
    source_suffix = "-DE.md" if source_path.endswith("-DE.md") else "-EN.md" if source_path.endswith("-EN.md") else ""
    seen: set[str] = set()
    selected: list[str] = []
    for signature in SIGNATURE_RE.findall(source_text):
        for path in mapping.get(signature, []):
            if path == source_path or path in seen:
                continue
            seen.add(path)
            selected.append(path)
    selected.sort(key=lambda p: (0 if source_suffix and p.endswith(source_suffix) else 1, p))
    return selected[:MAX_CONTEXT_DOCS]


def context_excerpt(text: str) -> str:
    if len(text) <= MAX_CONTEXT_CHARS:
        return text
    return text[:MAX_CONTEXT_CHARS].rstrip() + "\n\n[Excerpt truncated by OTA scoped discovery]\n"


def build_scope(
    clone_root: Path, source_path: str, context_paths: list[str]
) -> Path:
    scope = Path(tempfile.mkdtemp(prefix="kueper-ota-scope-"))
    shutil.copyfile(clone_root / source_path, scope / "SOURCE.md")
    context_dir = scope / "context"
    context_dir.mkdir()
    manifest = {
        "source_path": source_path,
        "source_file": "SOURCE.md",
        "context": [],
        "rules": [
            "SOURCE.md is the only authoritative source document for this discovery.",
            "Context files are excerpts and may only be used as secondary ecosystem context.",
            "Do not inspect files outside this scoped workspace.",
        ],
    }
    for idx, path in enumerate(context_paths, start=1):
        text = (clone_root / path).read_text(encoding="utf-8")
        name = f"{idx:02d}-{Path(path).name}"
        (context_dir / name).write_text(context_excerpt(text), encoding="utf-8")
        manifest["context"].append({"original_path": path, "file": f"context/{name}"})
    (scope / "SCOPE.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return scope


def scoped_prompt(
    project: dict[str, Any],
    profile_name: str,
    profile: dict[str, Any],
    previous: list[dict[str, Any]],
    source_path: str,
    context_paths: list[str],
) -> str:
    profile_rules = json.dumps(profile, ensure_ascii=False)
    previous_json = json.dumps(previous, ensure_ascii=False, indent=2)
    allowed_routes = json.dumps(profile.get("allowed_publication_routes", []), ensure_ascii=False)
    claim_classes = json.dumps(profile.get("claim_classes", {}), ensure_ascii=False)
    context_json = json.dumps(context_paths, ensure_ascii=False)

    return f"""You are the document-scoped knowledge-gap analyst for the KUEPER ecosystem.

Project: {PROJECT_ID}
Repository: {project['repository']}
Evidence profile: {profile_name}
Evidence profile rules: {profile_rules}
Claim classes: {claim_classes}
Allowed publication-route hints: {allowed_routes}

CONTROL-PLANE SCOPE — mandatory:
- The source document has already been selected deterministically by code.
- Original source_path: {source_path}
- Read `SOURCE.md` completely.
- `context/` contains at most {MAX_CONTEXT_DOCS} excerpts of documents explicitly referenced by SOURCE.md.
- Original context paths: {context_json}
- Context excerpts are secondary orientation only.
- Do NOT inspect parent directories, the network, Git metadata, or any file outside this workspace.
- Do NOT choose a different source document.
- Every proposed gap MUST set `source_path` exactly to `{source_path}`.
- Find at most {MAX_GAPS} externally researchable gaps in SOURCE.md. If the document does not justify a good external research gap, return an empty gaps array.

Previous OTA research topics:
{previous_json}

Classification rules:
- Classify before external research.
- Use the profile's exact claim-class keys.
- R / real anchors may require external verification.
- T/H/S may be researched for premises, constraints, counterevidence or falsifiability, but source count never establishes the model/speculation.
- F/W claims are not externally validated. Omit a gap that is only F/W with no real-world anchor.
- Preserve explicit uncertainty.
- `publication_route_hint` is advisory only; never imply publication occurs here.

Novelty rules:
- Do not repeat a prior topic by rephrasing, translating, broadening or cosmetic narrowing.
- A genuine follow-up must list prior IDs in `related_research_ids` and explain the materially unresolved addition in `novelty_reason`.

For each gap score 0..1:
- project_relevance
- cross_project_reuse
- uncertainty
- evidence_potential
`relevance_score` is their arithmetic mean and must be >= {core.POLICY['minimum_relevance_score']}.

Write ONLY `.kueper-discovery.json` with:
{{"gaps":[{{"title":"...","question":"...","why_now":"...","project_id":"ota","source_path":"{source_path}","suggested_languages":["en"],"claim_classes":["R"],"external_research_required":true,"real_world_anchor":"... or null","publication_route_hint":"fictional_archive_document or real_scientific_epaper or null","related_research_ids":[],"novelty_reason":"","project_relevance":0.0,"cross_project_reuse":0.0,"uncertainty":0.0,"evidence_potential":0.0,"relevance_score":0.0}}]}}
Do not edit any other file.
"""


def main() -> int:
    token = os.environ.get("KUEPER_BOT_TOKEN")
    if not token:
        raise SystemExit("KUEPER_BOT_TOKEN required")

    pmap = core.projects()
    project = pmap[PROJECT_ID]
    eligible = next(
        entry for entry in core.POLICY["eligible_projects"] if entry.get("id") == PROJECT_ID
    )
    profile_name = eligible.get("evidence_profile", "general")
    profile = core.POLICY["evidence_profiles"][profile_name]
    history = core.queue_history(token)
    previous = core.prior_topics(history, PROJECT_ID)
    prior_ids = {
        item.get("id")
        for item in history
        if item.get("source_project") == PROJECT_ID and item.get("id")
    }
    existing = {item.get("fingerprint", "") for item in history}

    clone_root = Path(tempfile.mkdtemp(prefix="kueper-ota-source-"))
    scope: Path | None = None
    selection_started = time.monotonic()
    try:
        core.run(
            [
                "git",
                "clone",
                "--quiet",
                "--depth",
                "1",
                core.auth_url(project["repository"], token),
                str(clone_root),
            ]
        )
        source_ref = core.run(["git", "rev-parse", "HEAD"], cwd=clone_root).strip()
        all_paths = tracked_documents(clone_root)
        source_path, source_blob, selection_score, candidate_count = select_source(
            clone_root, history
        )
        source_text = (clone_root / source_path).read_text(encoding="utf-8")
        context_paths = select_context_paths(source_path, source_text, all_paths)
        scope = build_scope(clone_root, source_path, context_paths)
    finally:
        shutil.rmtree(clone_root, ignore_errors=True)

    selection_seconds = round(time.monotonic() - selection_started, 3)
    allowed_claims = set(profile.get("claim_classes", {}))
    allowed_routes = set(profile.get("allowed_publication_routes", []))

    agent_started = time.monotonic()
    try:
        cmd = os.environ.get(
            "KUEPER_DISCOVERY_AGENT_CMD", "codex exec --full-auto"
        ).split()
        core.run(
            cmd
            + [
                scoped_prompt(
                    project,
                    profile_name,
                    profile,
                    previous,
                    source_path,
                    context_paths,
                )
            ],
            cwd=scope,
        )
        result_file = scope / ".kueper-discovery.json"
        if not result_file.exists():
            raise RuntimeError("agent did not create .kueper-discovery.json")
        data = json.loads(result_file.read_text(encoding="utf-8"))
    finally:
        agent_seconds = round(time.monotonic() - agent_started, 3)

    results: list[dict[str, Any]] = []
    for gap in data.get("gaps", [])[:MAX_GAPS]:
        if gap.get("project_id") != PROJECT_ID:
            continue
        if str(gap.get("source_path") or "").strip().replace("\\", "/") != source_path:
            continue
        score = float(gap.get("relevance_score", 0))
        if score < float(core.POLICY["minimum_relevance_score"]):
            continue
        claim_classes_used = [
            x for x in gap.get("claim_classes", []) if isinstance(x, str)
        ]
        if profile.get("require_claim_classification"):
            if not claim_classes_used or any(
                x not in allowed_claims for x in claim_classes_used
            ):
                continue
            if gap.get("external_research_required") is not True:
                continue
        route_hint = gap.get("publication_route_hint")
        if route_hint is not None and allowed_routes and route_hint not in allowed_routes:
            continue

        langs = [
            x
            for x in gap.get("suggested_languages", [])
            if isinstance(x, str)
        ][: core.POLICY["max_languages_per_topic"]]
        seed = (
            f"{PROJECT_ID}|{gap.get('title')}|{gap.get('question')}".lower().strip()
        )
        fingerprint = hashlib.sha256(seed.encode()).hexdigest()[:16]
        if fingerprint in existing:
            continue
        related = [
            rid
            for rid in gap.get("related_research_ids", [])
            if isinstance(rid, str) and rid in prior_ids
        ]
        novelty = str(gap.get("novelty_reason", "") or "").strip()
        if gap.get("related_research_ids") and not related:
            continue
        if related and len(novelty) < 20:
            continue

        now = dt.datetime.now(dt.timezone.utc)
        rid = f"RES-{now.strftime('%Y%m%d')}-{fingerprint[:8].upper()}"
        item = {
            "id": rid,
            "status": "queued",
            "created": now.replace(microsecond=0).isoformat(),
            "source_project": PROJECT_ID,
            "source_repository": project["repository"],
            "source_path": source_path,
            "source_ref": source_ref,
            "source_blob_sha": source_blob,
            "selection_method": "deterministic-document-scope-v1",
            "selection_score": selection_score,
            "context_paths": context_paths,
            "title": gap.get("title"),
            "question": gap.get("question"),
            "why_now": gap.get("why_now"),
            "languages": langs or core.POLICY["default_languages"],
            "evidence_profile": profile_name,
            "claim_classes": claim_classes_used,
            "external_research_required": True,
            "real_world_anchor": gap.get("real_world_anchor"),
            "publication_route_hint": route_hint,
            "project_weight": float(eligible.get("weight", 1.0)),
            "relevance_score": score,
            "scores": {
                key: gap.get(key)
                for key in (
                    "project_relevance",
                    "cross_project_reuse",
                    "uncertainty",
                    "evidence_potential",
                )
            },
            "related_research_ids": related,
            "novelty_reason": novelty or None,
            "fingerprint": fingerprint,
        }
        content = base64.b64encode(
            (json.dumps(item, indent=2, ensure_ascii=False) + "\n").encode()
        ).decode()
        core.gh(
            token,
            "PUT",
            f"/repos/{core.CONTROL}/contents/research/queue/{rid}.json",
            {
                "message": f"research: queue {rid}",
                "content": content,
                "branch": "main",
            },
        )
        existing.add(fingerprint)
        results.append(item)

    if scope is not None:
        shutil.rmtree(scope, ignore_errors=True)

    print(
        json.dumps(
            {
                "project": PROJECT_ID,
                "evidence_profile": profile_name,
                "selection_method": "deterministic-document-scope-v1",
                "selected_source_path": source_path,
                "selected_source_ref": source_ref,
                "selected_source_blob_sha": source_blob,
                "selection_score": selection_score,
                "eligible_document_revisions": candidate_count,
                "context_paths": context_paths,
                "selection_seconds": selection_seconds,
                "agent_seconds": agent_seconds,
                "prior_topics_supplied": len(previous),
                "queued": len(results),
                "items": results,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
