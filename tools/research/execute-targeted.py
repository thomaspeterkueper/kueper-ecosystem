#!/usr/bin/env python3
"""Execute explicitly selected queued research IDs.

This is a thin operational wrapper around execute.py. It does not weaken evidence
validation or canonicalization boundaries; it only controls which queued items are
selected for a manual/targeted run.

For OTA technical-object research, this wrapper also enforces the consumer boundary
before any external research starts: only externally researchable claim classes are
accepted and NOXIA balancing must be explicitly marked out of scope / non-mutating.

Large pinned source files are handled fail-closed: the full source is still fetched
and blob-verified by execute.py, but only explicitly anchored excerpts are passed to
the research agent when the source exceeds the configured prompt-size threshold.
"""
from __future__ import annotations

import json
import os

import execute as core

TECH_OBJECT_CONTRACT = "ota-tech-object-v1"
TECH_OBJECT_RESEARCHABLE_CLASSES = {"R", "R-Anker", "H", "T"}
MAX_SOURCE_CONTEXT_CHARS = int(os.environ.get("KUEPER_MAX_SOURCE_CONTEXT_CHARS", "120000"))
SOURCE_ANCHOR_WINDOW_CHARS = int(os.environ.get("KUEPER_SOURCE_ANCHOR_WINDOW_CHARS", "24000"))
_ORIGINAL_SOURCE_DOCUMENT_CONTEXT = core.source_document_context


def anchored_source_document_context(token: str, item: dict):
    """Return the full verified source or a fail-closed anchored excerpt.

    The original helper always fetches and verifies the exact pinned blob first.
    Excerpting is only a prompt-transport optimization for very large source files;
    it does not weaken source identity. Oversized sources require explicit queue
    anchors so the executor never silently drops arbitrary portions of a source.
    """
    context = _ORIGINAL_SOURCE_DOCUMENT_CONTEXT(token, item)
    if not context:
        return context

    text = context.get("text") or ""
    if len(text) <= MAX_SOURCE_CONTEXT_CHARS:
        return context

    anchors = [
        str(value).strip()
        for value in (item.get("source_anchors") or [])
        if str(value).strip()
    ]
    if not anchors:
        raise RuntimeError(
            f"oversized source {context['repository']}:{context['path']} has "
            f"{len(text)} characters; explicit source_anchors are required"
        )

    lower = text.lower()
    spans: list[tuple[int, int, str]] = []
    missing: list[str] = []
    for anchor in anchors:
        needle = anchor.lower()
        start = 0
        hits = 0
        while True:
            pos = lower.find(needle, start)
            if pos < 0:
                break
            hits += 1
            spans.append(
                (
                    max(0, pos - SOURCE_ANCHOR_WINDOW_CHARS),
                    min(len(text), pos + len(anchor) + SOURCE_ANCHOR_WINDOW_CHARS),
                    anchor,
                )
            )
            if hits >= 3:
                break
            start = pos + len(needle)
        if hits == 0:
            missing.append(anchor)

    if missing:
        raise RuntimeError(
            "source anchor(s) not found in pinned source blob: " + ", ".join(missing)
        )

    spans.sort(key=lambda value: value[0])
    merged: list[tuple[int, int, set[str]]] = []
    for start, end, anchor in spans:
        if merged and start <= merged[-1][1]:
            prev_start, prev_end, prev_anchors = merged[-1]
            merged[-1] = (prev_start, max(prev_end, end), prev_anchors | {anchor})
        else:
            merged.append((start, end, {anchor}))

    parts: list[str] = []
    used = 0
    header = (
        "[TARGETED EXCERPT FROM EXACT PINNED SOURCE — full blob identity was verified; "
        "only explicit source-anchor neighborhoods are included to keep agent prompt "
        "transport below operating-system argument limits.]\n"
        f"Full source characters: {len(text)}\n"
        f"Source anchors: {', '.join(anchors)}\n"
    )
    used += len(header)
    for index, (start, end, span_anchors) in enumerate(merged, start=1):
        marker = (
            f"\n--- SOURCE EXCERPT {index} | chars {start}:{end} | anchors: "
            f"{', '.join(sorted(span_anchors))} ---\n"
        )
        remaining = MAX_SOURCE_CONTEXT_CHARS - used - len(marker)
        if remaining <= 0:
            break
        chunk = text[start:end]
        if len(chunk) > remaining:
            chunk = chunk[:remaining]
        parts.append(marker + chunk)
        used += len(marker) + len(chunk)

    excerpt = header + "".join(parts)
    if not parts:
        raise RuntimeError("anchored source excerpt could not be constructed within prompt limit")

    result = dict(context)
    result["text"] = excerpt
    result["excerpted"] = True
    result["source_character_count"] = len(text)
    result["source_anchors"] = anchors
    return result


# Targeted research uses the fail-closed prompt transport above. Generic queue
# execution remains unchanged until/unless it explicitly adopts the same contract.
core.source_document_context = anchored_source_document_context


def validate_research_contract(item: dict) -> None:
    contract = item.get("research_contract")
    if contract != TECH_OBJECT_CONTRACT:
        return

    if item.get("source_project") != "ota":
        raise SystemExit(
            f"{item.get('id')}: {TECH_OBJECT_CONTRACT} requires source_project=ota"
        )
    if item.get("consumer_project") != "noxia":
        raise SystemExit(
            f"{item.get('id')}: {TECH_OBJECT_CONTRACT} requires consumer_project=noxia"
        )
    if not item.get("source_path") or not item.get("source_blob_sha"):
        raise SystemExit(
            f"{item.get('id')}: technical-object research requires pinned source_path + source_blob_sha"
        )

    classes = set(item.get("claim_classes") or [])
    if not classes or not classes.issubset(TECH_OBJECT_RESEARCHABLE_CLASSES):
        bad = sorted(classes - TECH_OBJECT_RESEARCHABLE_CLASSES)
        raise SystemExit(
            f"{item.get('id')}: technical-object research may only target "
            f"{sorted(TECH_OBJECT_RESEARCHABLE_CLASSES)}; invalid classes: {bad}"
        )

    impact = item.get("consumer_impact_policy") or {}
    if impact.get("auto_update_noxia") is not False:
        raise SystemExit(
            f"{item.get('id')}: technical-object contract requires auto_update_noxia=false"
        )
    if impact.get("balancing_is_out_of_scope") is not True:
        raise SystemExit(
            f"{item.get('id')}: technical-object contract requires balancing_is_out_of_scope=true"
        )
    if impact.get("flag_noxia_impact") is not True:
        raise SystemExit(
            f"{item.get('id')}: technical-object contract requires flag_noxia_impact=true"
        )


def main() -> int:
    token = os.environ.get("KUEPER_BOT_TOKEN")
    if not token:
        raise SystemExit("KUEPER_BOT_TOKEN required")

    requested = [
        value.strip()
        for value in os.environ.get("KUEPER_RESEARCH_IDS", "").split(",")
        if value.strip()
    ]
    if not requested:
        raise SystemExit("KUEPER_RESEARCH_IDS required (comma-separated research IDs)")

    queued = core.queue(token)
    by_id = {item["id"]: (item, payload) for item, payload in queued}
    missing = [research_id for research_id in requested if research_id not in by_id]
    if missing:
        raise SystemExit(f"requested research IDs are not queued: {', '.join(missing)}")

    results = []
    for research_id in requested:
        item, payload = by_id[research_id]
        validate_research_contract(item)
        results.append(core.execute(token, item, payload))

    print(
        json.dumps(
            {
                "selected": len(requested),
                "requested_ids": requested,
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
