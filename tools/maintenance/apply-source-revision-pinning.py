#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path.cwd()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one occurrence, found {count}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Policy: OTA document audits must carry an exact source file and revision.
# ---------------------------------------------------------------------------
policy_path = ROOT / "research/policy.json"
policy = json.loads(policy_path.read_text(encoding="utf-8"))
policy["schema_version"] = "1.4.0"
ota = policy["evidence_profiles"]["ota-archive-evidence"]
ota["require_source_path"] = True
ota["pin_source_revision"] = True
ota["scout_guidance"] = (
    "Classify the claim before searching. Each OTA research gap must be anchored to exactly one "
    "repository source document; preserve its path and pinned Git revision. Apply external evidence "
    "rigorously to R/real anchors; for T/H/S, test premises, constraints, counterevidence and "
    "falsifiability without treating source count as validation. Never use external search to validate "
    "F or W canon. Check whether newer evidence changes the result and surface material contradictions. "
    "If a standalone real-world scientific e-paper is warranted, recommend the real_scientific_epaper "
    "route to kueper.com/KUE-SCI; keep archive/canon framing in OTA."
)
policy_path.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Discovery: require and validate source_path for profiles that need it, then
# pin commit + blob SHA into the queue item.
# ---------------------------------------------------------------------------
discover_path = ROOT / "tools/research/discover.py"
discover = discover_path.read_text(encoding="utf-8")

discover = replace_once(
    discover,
    "- `publication_route_hint` is advisory only. If a standalone real-world scientific e-paper could result, use `real_scientific_epaper`; archive/canon material stays `fictional_archive_document`. Never imply that this discovery step publishes anything.\n",
    "- `publication_route_hint` is advisory only. If a standalone real-world scientific e-paper could result, use `real_scientific_epaper`; archive/canon material stays `fictional_archive_document`. Never imply that this discovery step publishes anything.\n"
    "- `source_path` names the exact repository-relative file that contains the claim being audited. When the evidence profile requires a source path, every proposed gap MUST point to exactly one tracked file. Do not use a directory, glob, URL, generated description, or a second document as a substitute.\n",
    "discovery source-path guidance",
)

discover = replace_once(
    discover,
    '{{"gaps":[{{"title":"...","question":"...","why_now":"...","project_id":"{project[\'id\']}","suggested_languages":["en"],"claim_classes":["R"],"external_research_required":true,"real_world_anchor":"... or null","publication_route_hint":"... or null","related_research_ids":[],"novelty_reason":"","project_relevance":0.0,"cross_project_reuse":0.0,"uncertainty":0.0,"evidence_potential":0.0,"relevance_score":0.0}}]}}',
    '{{"gaps":[{{"title":"...","question":"...","why_now":"...","project_id":"{project[\'id\']}","source_path":"path/to/exact/source.md or null","suggested_languages":["en"],"claim_classes":["R"],"external_research_required":true,"real_world_anchor":"... or null","publication_route_hint":"... or null","related_research_ids":[],"novelty_reason":"","project_relevance":0.0,"cross_project_reuse":0.0,"uncertainty":0.0,"evidence_potential":0.0,"relevance_score":0.0}}]}}',
    "discovery output schema",
)

discover = replace_once(
    discover,
    '        run(["git","clone","--quiet","--depth","1",auth_url(project["repository"],token),str(root)])\n        cmd=os.environ.get("KUEPER_DISCOVERY_AGENT_CMD","codex exec --full-auto").split()\n',
    '        run(["git","clone","--quiet","--depth","1",auth_url(project["repository"],token),str(root)])\n        source_ref=run(["git","rev-parse","HEAD"],cwd=root).strip()\n        cmd=os.environ.get("KUEPER_DISCOVERY_AGENT_CMD","codex exec --full-auto").split()\n',
    "discovery source ref",
)

discover = replace_once(
    discover,
    '            route_hint=gap.get("publication_route_hint")\n            if route_hint is not None and allowed_routes and route_hint not in allowed_routes:continue\n            langs=[x for x in gap.get("suggested_languages",[]) if isinstance(x,str)][:POLICY["max_languages_per_topic"]]\n',
    '            route_hint=gap.get("publication_route_hint")\n            if route_hint is not None and allowed_routes and route_hint not in allowed_routes:continue\n            source_path=str(gap.get("source_path") or "").strip().replace("\\\\","/") or None\n            source_blob_sha=None\n            if source_path:\n                candidate=(root/source_path).resolve();root_resolved=root.resolve()\n                if candidate==root_resolved or root_resolved not in candidate.parents or not candidate.is_file():continue\n                try:\n                    run(["git","ls-files","--error-unmatch","--",source_path],cwd=root)\n                    source_blob_sha=run(["git","rev-parse",f"HEAD:{source_path}"],cwd=root).strip()\n                except Exception:\n                    continue\n            if profile.get("require_source_path") and not source_path:continue\n            if profile.get("pin_source_revision") and source_path and not source_blob_sha:continue\n            langs=[x for x in gap.get("suggested_languages",[]) if isinstance(x,str)][:POLICY["max_languages_per_topic"]]\n',
    "discovery source-path validation",
)

discover = replace_once(
    discover,
    '            item={"id":rid,"status":"queued","created":now.replace(microsecond=0).isoformat(),"source_project":project["id"],"source_repository":project["repository"],"title":gap.get("title"),"question":gap.get("question"),"why_now":gap.get("why_now"),"languages":langs or POLICY["default_languages"],"evidence_profile":profile_name,"claim_classes":claim_classes,"external_research_required":gap.get("external_research_required",True),"real_world_anchor":gap.get("real_world_anchor"),"publication_route_hint":route_hint,"project_weight":float(choice.get("weight",1.0)),"relevance_score":score,"scores":{k:gap.get(k) for k in ("project_relevance","cross_project_reuse","uncertainty","evidence_potential")},"related_research_ids":related,"novelty_reason":novelty or None,"fingerprint":fp}\n',
    '            item={"id":rid,"status":"queued","created":now.replace(microsecond=0).isoformat(),"source_project":project["id"],"source_repository":project["repository"],"source_path":source_path,"source_ref":source_ref if source_path else None,"source_blob_sha":source_blob_sha,"title":gap.get("title"),"question":gap.get("question"),"why_now":gap.get("why_now"),"languages":langs or POLICY["default_languages"],"evidence_profile":profile_name,"claim_classes":claim_classes,"external_research_required":gap.get("external_research_required",True),"real_world_anchor":gap.get("real_world_anchor"),"publication_route_hint":route_hint,"project_weight":float(choice.get("weight",1.0)),"relevance_score":score,"scores":{k:gap.get(k) for k in ("project_relevance","cross_project_reuse","uncertainty","evidence_potential")},"related_research_ids":related,"novelty_reason":novelty or None,"fingerprint":fp}\n',
    "discovery queue source metadata",
)

discover_path.write_text(discover, encoding="utf-8")


# ---------------------------------------------------------------------------
# Executor: prefer pinned source_ref; verify blob SHA; only fall back to current
# default branch for legacy/manual queue items without a pinned revision.
# ---------------------------------------------------------------------------
execute_path = ROOT / "tools/research/execute.py"
execute = execute_path.read_text(encoding="utf-8")

old_source = '''def source_document_context(token:str,item:dict[str,Any])->dict[str,Any]|None:
    """Fetch the exact declared source document before external research.

    A declared source_path is a hard contract: if it cannot be loaded from the
    declared source repository's real default branch, research fails closed.
    """
    source_path=item.get("source_path")
    if not source_path:return None
    source_repo=item.get("source_repository")
    if not source_repo:raise RuntimeError(f"queued item {item.get('id')} declares source_path but no source_repository")
    info=repo_info(token,source_repo);default=info.get("default_branch")
    if not default:raise RuntimeError(f"cannot resolve default branch for source repository {source_repo}")
    encoded_path=urllib.parse.quote(str(source_path),safe='/');encoded_ref=urllib.parse.quote(str(default),safe='')
    payload=gh(token,"GET",f"/repos/{source_repo}/contents/{encoded_path}?ref={encoded_ref}")
    if not isinstance(payload,dict) or payload.get("type")!="file" or not payload.get("content"):
        raise RuntimeError(f"declared source document is not a readable file: {source_repo}@{default}:{source_path}")
    try:text=base64.b64decode(payload["content"]).decode("utf-8")
    except Exception as exc:raise RuntimeError(f"cannot decode declared source document {source_repo}:{source_path}: {exc}") from exc
    if not text.strip():raise RuntimeError(f"declared source document is empty: {source_repo}:{source_path}")
    return {"repository":source_repo,"path":str(source_path),"ref":str(default),"sha":payload.get("sha"),"text":text}
'''
new_source = '''def source_document_context(token:str,item:dict[str,Any])->dict[str,Any]|None:
    """Fetch the exact declared source document before external research.

    A declared source_path is a hard contract. New discovery items pin both the
    source commit and blob SHA so a later research run audits the exact version
    that triggered the gap. Legacy/manual items may fall back to the repository's
    current default branch, but still fail closed if the file cannot be loaded.
    """
    source_path=item.get("source_path")
    if not source_path:return None
    source_repo=item.get("source_repository")
    if not source_repo:raise RuntimeError(f"queued item {item.get('id')} declares source_path but no source_repository")
    source_ref=item.get("source_ref")
    if not source_ref:
        info=repo_info(token,source_repo);source_ref=info.get("default_branch")
    if not source_ref:raise RuntimeError(f"cannot resolve source ref for repository {source_repo}")
    encoded_path=urllib.parse.quote(str(source_path),safe='/');encoded_ref=urllib.parse.quote(str(source_ref),safe='')
    payload=gh(token,"GET",f"/repos/{source_repo}/contents/{encoded_path}?ref={encoded_ref}")
    if not isinstance(payload,dict) or payload.get("type")!="file" or not payload.get("content"):
        raise RuntimeError(f"declared source document is not a readable file: {source_repo}@{source_ref}:{source_path}")
    expected_blob=item.get("source_blob_sha")
    actual_blob=payload.get("sha")
    if expected_blob and actual_blob!=expected_blob:
        raise RuntimeError(f"source blob mismatch for {source_repo}@{source_ref}:{source_path}: {actual_blob} != {expected_blob}")
    try:text=base64.b64decode(payload["content"]).decode("utf-8")
    except Exception as exc:raise RuntimeError(f"cannot decode declared source document {source_repo}:{source_path}: {exc}") from exc
    if not text.strip():raise RuntimeError(f"declared source document is empty: {source_repo}:{source_path}")
    return {"repository":source_repo,"path":str(source_path),"ref":str(source_ref),"sha":actual_blob,"text":text}
'''
execute = replace_once(execute, old_source, new_source, "executor pinned source context")
execute_path.write_text(execute, encoding="utf-8")


# ---------------------------------------------------------------------------
# CI: lock the OTA source-document contract into the permanent config check.
# ---------------------------------------------------------------------------
check_path = ROOT / ".github/workflows/research-config-check.yml"
check = check_path.read_text(encoding="utf-8")
check = replace_once(
    check,
    "          assert policy['auto_canonicalize'] is False\n          profiles = policy['evidence_profiles']\n",
    "          assert policy['auto_canonicalize'] is False\n          profiles = policy['evidence_profiles']\n          ota_profile = profiles['ota-archive-evidence']\n          assert ota_profile.get('require_source_path') is True\n          assert ota_profile.get('pin_source_revision') is True\n          discover_source = (root / 'tools/research/discover.py').read_text(encoding='utf-8')\n          execute_source = (root / 'tools/research/execute.py').read_text(encoding='utf-8')\n          assert 'source_blob_sha' in discover_source and 'source_ref' in discover_source\n          assert 'source blob mismatch' in execute_source and 'source_ref' in execute_source\n",
    "config source pin assertions",
)
check_path.write_text(check, encoding="utf-8")

print("Applied source-path + source-revision pinning for OTA research discovery/execution")
