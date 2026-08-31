#!/usr/bin/env python3
"""Audit canonical OTA technical objects consumed by NOXIA.

This is an inventory/control-plane check, not a research executor. It discovers
OTA TEC documents that explicitly map to NOXIA, validates their machine identity,
and reports whether the current source blob is covered by at least one queue item
protected by the ota-tech-object-v1 contract.

It never creates or mutates NOXIA balancing data and never canonicalizes research.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

CONTRACT = "ota-tech-object-v1"
RESEARCHABLE = {"R", "R-Anker", "H", "T"}


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    return text[4:end] if end >= 0 else ""


def scalar(fm: str, key: str) -> str | None:
    m = re.search(rf"(?m)^{re.escape(key)}:\s*[\"']?([^\n\"']+?)[\"']?\s*$", fm)
    return m.group(1).strip() if m else None


def block_has_list_value(fm: str, key: str, value: str) -> bool:
    lines = fm.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == f"{key}:":
            base = len(line) - len(line.lstrip())
            for child in lines[i + 1 :]:
                if not child.strip():
                    continue
                indent = len(child) - len(child.lstrip())
                if indent <= base:
                    break
                if child.strip().lstrip("- ").strip().strip("\"'") == value:
                    return True
    return False


def mapping_value(fm: str, mapping: str, key: str) -> str | None:
    lines = fm.splitlines()
    in_mappings = False
    mappings_indent = -1
    in_mapping = False
    mapping_indent = -1
    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if stripped == "mappings:":
            in_mappings = True
            mappings_indent = indent
            in_mapping = False
            continue
        if in_mappings and indent <= mappings_indent:
            in_mappings = False
            in_mapping = False
        if not in_mappings:
            continue
        if stripped == f"{mapping}:":
            in_mapping = True
            mapping_indent = indent
            continue
        if in_mapping and indent <= mapping_indent:
            in_mapping = False
        if in_mapping:
            m = re.match(rf"{re.escape(key)}:\s*[\"']?(.+?)[\"']?\s*$", stripped)
            if m:
                return m.group(1).strip().strip("\"'")
    return None


def load_queue(queue_dir: Path) -> list[dict]:
    items = []
    for path in sorted(queue_dir.glob("*.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            items.append({"id": path.name, "_parse_error": str(exc)})
            continue
        item["_queue_path"] = str(path)
        items.append(item)
    return items


def validate_contract_item(item: dict) -> list[str]:
    if item.get("research_contract") != CONTRACT:
        return []
    errors: list[str] = []
    if item.get("source_project") != "ota":
        errors.append("source_project must be ota")
    if item.get("consumer_project") != "noxia":
        errors.append("consumer_project must be noxia")
    if not item.get("source_path") or not item.get("source_blob_sha"):
        errors.append("source_path and source_blob_sha are required")
    classes = set(item.get("claim_classes") or [])
    if not classes or not classes.issubset(RESEARCHABLE):
        errors.append(f"claim_classes must be non-empty subset of {sorted(RESEARCHABLE)}")
    impact = item.get("consumer_impact_policy") or {}
    if impact.get("flag_noxia_impact") is not True:
        errors.append("flag_noxia_impact must be true")
    if impact.get("auto_update_noxia") is not False:
        errors.append("auto_update_noxia must be false")
    if impact.get("balancing_is_out_of_scope") is not True:
        errors.append("balancing_is_out_of_scope must be true")
    return errors


def discover(ota_root: Path) -> tuple[list[dict], list[str]]:
    docs: list[dict] = []
    errors: list[str] = []
    seen: dict[str, str] = {}
    base = ota_root / "src" / "content" / "documents"
    for path in sorted(base.glob("OTA-TEC-*-DE.md")):
        text = path.read_text(encoding="utf-8")
        fm = frontmatter(text)
        if not fm or scalar(fm, "series") != "TEC":
            continue
        if not block_has_list_value(fm, "contexts", "noxia"):
            continue
        object_id = scalar(fm, "objectId")
        mapped_object_id = mapping_value(fm, "noxia", "objectId")
        role = mapping_value(fm, "noxia", "role")
        signature = scalar(fm, "signature") or path.stem
        rel = path.relative_to(ota_root).as_posix()
        doc_errors = []
        if not object_id:
            doc_errors.append("missing top-level objectId")
        if not mapped_object_id:
            doc_errors.append("missing mappings.noxia.objectId")
        if object_id and mapped_object_id and object_id != mapped_object_id:
            doc_errors.append("top-level objectId differs from mappings.noxia.objectId")
        if not role:
            doc_errors.append("missing mappings.noxia.role")
        if object_id:
            if object_id in seen:
                doc_errors.append(f"duplicate objectId; also used by {seen[object_id]}")
            else:
                seen[object_id] = rel
        if doc_errors:
            errors.extend(f"{rel}: {msg}" for msg in doc_errors)
        docs.append(
            {
                "signature": signature,
                "source_path": rel,
                "source_blob_sha": git_blob_sha(path),
                "object_id": object_id,
                "mapped_object_id": mapped_object_id,
                "role": role,
                "metadata_valid": not doc_errors,
                "metadata_errors": doc_errors,
            }
        )
    return docs, errors


def audit(ota_root: Path, queue_dir: Path) -> dict:
    docs, metadata_errors = discover(ota_root)
    queue = load_queue(queue_dir)
    contract_errors = []
    by_source: dict[str, list[dict]] = defaultdict(list)
    for item in queue:
        if item.get("_parse_error"):
            contract_errors.append(f"{item['id']}: invalid JSON: {item['_parse_error']}")
            continue
        errs = validate_contract_item(item)
        if errs:
            contract_errors.extend(f"{item.get('id')}: {e}" for e in errs)
        if item.get("research_contract") == CONTRACT and item.get("source_path"):
            by_source[item["source_path"]].append(item)

    results = []
    counts = defaultdict(int)
    for doc in docs:
        candidates = by_source.get(doc["source_path"], [])
        current = [
            item for item in candidates
            if item.get("source_blob_sha") == doc["source_blob_sha"]
            and item.get("object_id") == doc.get("object_id")
            and not validate_contract_item(item)
        ]
        if not doc["metadata_valid"]:
            state = "invalid"
        elif current:
            state = "covered"
        elif candidates:
            state = "stale"
        else:
            state = "uncovered"
        counts[state] += 1
        results.append(
            {
                **doc,
                "coverage_state": state,
                "current_research_ids": [i.get("id") for i in current],
                "historical_research_ids": [i.get("id") for i in candidates],
                "required_boundaries": {
                    "research_contract": CONTRACT,
                    "identity_layer": "kueper-knowledge-graph",
                    "real_science_route": "kueper.com/KUE-SCI",
                    "consumer": "noxiagame",
                    "flag_noxia_impact": True,
                    "auto_update_noxia": False,
                    "balancing_is_out_of_scope": True,
                },
            }
        )

    return {
        "contract": CONTRACT,
        "ota_root": str(ota_root),
        "objects_total": len(docs),
        "counts": dict(sorted(counts.items())),
        "metadata_errors": metadata_errors,
        "contract_errors": contract_errors,
        "objects": results,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ota-root", type=Path, required=True)
    p.add_argument("--queue-dir", type=Path, default=Path("research/queue"))
    p.add_argument("--output", type=Path)
    p.add_argument("--strict", action="store_true", help="fail on invalid metadata or unsafe contract items")
    args = p.parse_args()
    report = audit(args.ota_root, args.queue_dir)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if args.strict and (report["metadata_errors"] or report["contract_errors"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
