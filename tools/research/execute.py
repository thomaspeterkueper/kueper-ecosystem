#!/usr/bin/env python3
"""Execute queued KUEPER research topics and publish evidence-marked KG candidates.

Research results are staging material only. Structural evidence gates may create a
candidate PR, but the executor never merges or enables auto-merge. Merge eligibility
belongs to a separate review-aware reconciliation step.
"""
from __future__ import annotations
import base64, datetime as dt, json, os, re, shlex, shutil, subprocess, tempfile, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from typing import Any

API="https://api.github.com"
ROOT=Path(__file__).resolve().parents[2]
POLICY=json.loads((ROOT/"research/policy.json").read_text(encoding="utf-8"))
CONTROL="thomaspeterkueper/kueper-ecosystem"
TARGET=POLICY["target_repository"]

def gh(token:str,method:str,path:str,body:dict[str,Any]|None=None)->Any:
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(API+path,data=data,method=method)
    req.add_header("Authorization",f"Bearer {token}");req.add_header("Accept","application/vnd.github+json");req.add_header("X-GitHub-Api-Version","2022-11-28")
    if data is not None:req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req) as r:
            raw=r.read();return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub HTTP {exc.code}: {exc.read().decode(errors='replace')}") from exc

def run(cmd:list[str],cwd:Path|None=None,check=True,env:dict[str,str]|None=None):
    cp=subprocess.run(cmd,cwd=str(cwd) if cwd else None,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if check and cp.returncode:raise RuntimeError(cp.stdout)
    return cp

def auth_url(repo,token):return f"https://x-access-token:{urllib.parse.quote(token,safe='')}@github.com/{repo}.git"
def repo_info(token,repo):return gh(token,"GET",f"/repos/{repo}")

def evidence_profile(item:dict[str,Any])->tuple[str,dict[str,Any]]:
    name=item.get("evidence_profile")
    if not name:
        entry=next((p for p in POLICY.get("eligible_projects",[]) if p.get("id")==item.get("source_project")),{})
        name=entry.get("evidence_profile","general")
    profiles=POLICY.get("evidence_profiles",{})
    return name,profiles.get(name,profiles.get("general",{}))

def publication_route(profile:dict[str,Any],hint:str|None=None)->tuple[str|None,dict[str,Any]]:
    allowed=profile.get("allowed_publication_routes",[])
    route_id=hint or profile.get("default_publication_route")
    if route_id and allowed and route_id not in allowed:raise RuntimeError(f"publication route {route_id} is not allowed for evidence profile")
    route=(POLICY.get("publication_routing",{}) or {}).get(route_id,{}) if route_id else {}
    if route_id and not route:raise RuntimeError(f"publication route {route_id} is not defined")
    return route_id,route

def validate_source_contract(item:dict[str,Any])->tuple[str,dict[str,Any]]:
    """Fail closed when an evidence profile requires an exact source document."""
    profile_name,profile=evidence_profile(item)
    if profile.get("require_source_path"):
        if not item.get("source_path"):
            raise RuntimeError(f"queued item {item.get('id')} requires source_path for evidence profile {profile_name}")
        if not item.get("source_repository"):
            raise RuntimeError(f"queued item {item.get('id')} requires source_repository for evidence profile {profile_name}")
    if profile.get("pin_source_revision"):
        if not item.get("source_ref"):
            raise RuntimeError(f"queued item {item.get('id')} requires pinned source_ref for evidence profile {profile_name}")
        if not item.get("source_blob_sha"):
            raise RuntimeError(f"queued item {item.get('id')} requires pinned source_blob_sha for evidence profile {profile_name}")
    return profile_name,profile

def source_document_context(token:str,item:dict[str,Any])->dict[str,Any]|None:
    """Fetch and verify the exact declared source document before external research."""
    validate_source_contract(item)
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

def queue(token)->list[tuple[dict[str,Any],dict[str,Any]]]:
    try:items=gh(token,"GET",f"/repos/{CONTROL}/contents/research/queue?ref=main")
    except Exception:return []
    out=[]
    for item in items if isinstance(items,list) else []:
        if item.get("type")!="file" or not item.get("name","").endswith(".json"):continue
        payload=gh(token,"GET",f"/repos/{CONTROL}/contents/{item['path']}?ref=main")
        try:data=json.loads(base64.b64decode(payload.get("content","")).decode())
        except Exception:continue
        if data.get("status")=="queued":out.append((data,payload))
    return sorted(out,key=lambda x:(-float(x[0].get("relevance_score",0)),x[0].get("created","")))

def research_prompt(item:dict[str,Any],source_context:dict[str,Any]|None=None)->str:
    langs=", ".join(item.get("languages") or POLICY["default_languages"])
    profile_name,profile=evidence_profile(item)
    profile_rules=json.dumps(profile,ensure_ascii=False)
    claim_classes=item.get("claim_classes") or []
    if profile.get("require_claim_classification") and not claim_classes:
        raise RuntimeError(f"queued item {item.get('id')} lacks required pre-research claim classification")
    allowed_claims=set(profile.get("claim_classes",{}))
    if allowed_claims and any(c not in allowed_claims for c in claim_classes):
        raise RuntimeError(f"queued item {item.get('id')} contains invalid claim class for {profile_name}")
    route_id,route=publication_route(profile,item.get("publication_route_hint"))
    route_json=json.dumps(route,ensure_ascii=False) if route else "{}"
    claim_json=json.dumps(claim_classes,ensure_ascii=False)
    real_anchor=item.get("real_world_anchor") or "none specified"
    if source_context:
        source_block=(
            f"Source document repository: {source_context['repository']}\n"
            f"Source document path: {source_context['path']}\n"
            f"Source document ref: {source_context['ref']}\n"
            f"Source document blob SHA: {source_context.get('sha') or 'unknown'}\n\n"
            "--- BEGIN DECLARED SOURCE DOCUMENT ---\n"
            f"{source_context['text']}\n"
            "--- END DECLARED SOURCE DOCUMENT ---"
        )
    else:
        source_block="No single declared source document was supplied for this research item."
    required_sections=[]
    if profile.get("require_claim_classification"):required_sections.append("## Claim-Klassifikation")
    if profile.get("require_freshness_check") or profile.get("require_conflict_check"):required_sections.append("## Aktualität und Widerspruchsprüfung")
    if route_id:required_sections.append("## Publikationsroute")
    extra_sections="\n".join(required_sections)
    return f'''You are the evidence research agent for the KUEPER ecosystem.

Research ID: {item['id']}
Source project: {item['source_project']}
Question: {item['question']}
Why now: {item.get('why_now','')}
Requested source languages: {langs}
Evidence profile: {profile_name}
Evidence profile rules: {profile_rules}
Preclassified claim classes: {claim_json}
Real-world anchor: {real_anchor}
Publication route hint: {route_id or 'none'}
Publication route contract: {route_json}

## Declared source document context
{source_block}

If a declared source document is present above, it is authoritative for what that source document actually says. Audit and classify claims from that exact text. Do not claim that the document is unavailable, and do not reconstruct its contents from adjacent ecosystem documents. Adjacent documents may be used only as explicitly identified secondary ecosystem context.

The claim classification above was made BEFORE external research. Preserve it unless the evidence shows that the external part was misclassified; if you change it, explain why. Use live web search only for externally checkable claims, premises, constraints, historical attestations, scientific anchors, or falsifiability questions. Do not use web evidence to validate fictional canon or authorial/work settings.

Research the question rigorously. Languages are discovery channels, NOT evidence rankings. Apply the evidence profile above before the general defaults. Prefer primary sources, peer-reviewed work, official institutions, and academic publishers. Search in the languages that materially improve coverage; do not force every language if it adds no value. Compare conflicting evidence.

You MUST distinguish established findings, inference, open/contested points, and implications for the source project. For profiles with explicit claim classes, assess evidence according to those classes. Source count may support externally checkable claims; it cannot convert a model postulate, speculative extension, fictional statement or interpretation into an established fact.

When freshness checking is required, look for later papers, corrected/updated datasets, null results, retractions/corrections, and material new evidence that could change the conclusion. When conflict checking is required, search for serious counterevidence and explain unresolved contradictions.

Publication routing is advisory and review-gated. A real-world scientific e-paper belongs in kueper.com under the KUE-SCI publication layer (`src/content/kue/sci`) after review. OTA remains the in-universe/archive layer for fictional canon and mixed archive documents. Never publish or edit either destination automatically from this research task; only recommend a route when appropriate.

Create exactly two files in the checkout:
1. `.research-result.json` containing:
{{"evidence_score":0.0,"source_count":0,"distinct_domains":0,"languages_used":["en"],"uncertainty":"low|medium|high","evidence_profile":"{profile_name}","claim_classes_used":{claim_json},"publication_recommendation":"{route_id or ''}","candidate_filename":"{item['id']}.md"}}
2. `research/candidates/{item['id']}.md` with sections:
# title
Metadata (Research ID, source project, evidence profile, preclassified claim classes, publication recommendation, status: candidate/non-canonical, researched date)
## Forschungsfrage
## Kurzfazit
{extra_sections}
## Befundlage
## Gegenbefunde und Unsicherheit
## Claim-Source-Mapping
For every material externally checkable claim, map it to one or more numbered sources. Do not invent evidence requirements for F/W-only canon statements.
## Quellen
For each source include title, author/institution, publication date if available, URL, source language, source type, and peer-review/preprint status when relevant.
## Relevanz für KUEPER-Projekte
Clearly separate real-world implications from theoretical, speculative, fictional and worldbuilding use.
## Offene Fragen

In `## Publikationsroute`, if present, state whether the researched result should remain archive support or whether a standalone real-world scientific e-paper is justified. If recommending `real_scientific_epaper`, describe the separable real-science scope that could become KUE-SCI and explicitly exclude OTA/canon framing from that publication.

Evidence score guide: 0.9+ multiple strong primary/peer-reviewed sources; 0.78 publication-grade convergent evidence with active counterevidence check; 0.75 solid convergent evidence; 0.65 useful but with limitations; below profile threshold insufficient for candidate staging.
Never fabricate a citation, URL, publication, author, translation, or quote.
Do not edit canonical KG entities, relations, mappings, schemas, external tasks, publication repositories, or any other file.
'''

def validate_result(root:Path,item:dict[str,Any])->dict[str,Any]:
    jf=root/".research-result.json";candidate=root/POLICY["candidate_path"]/f"{item['id']}.md"
    if not jf.exists() or not candidate.exists():raise RuntimeError("research agent did not create required result files")
    profile_name,profile=evidence_profile(item)
    meta=json.loads(jf.read_text(encoding="utf-8"));score=float(meta.get("evidence_score",0));src=int(meta.get("source_count",0));domains=int(meta.get("distinct_domains",0))
    text=candidate.read_text(encoding="utf-8");urls=re.findall(r"https?://[^\s)>]+",text)
    min_score=float(profile.get("minimum_evidence_score",POLICY["minimum_evidence_score_for_candidate"]));min_sources=int(profile.get("minimum_sources",2));min_domains=int(profile.get("minimum_domains",2));min_urls=int(profile.get("minimum_urls",2))
    if score<min_score:raise RuntimeError(f"evidence score too low for {profile_name}: {score} < {min_score}")
    if src<min_sources or domains<min_domains or len(set(urls))<min_urls:raise RuntimeError(f"candidate for {profile_name} requires >={min_sources} sources, >={min_domains} domains and >={min_urls} URLs")
    if profile.get("require_strong_source"):
        markers=[str(x).lower() for x in profile.get("strong_source_markers",[])]
        if markers and not any(marker in text.lower() for marker in markers):raise RuntimeError(f"candidate for {profile_name} lacks a strong source type marker")
    if meta.get("evidence_profile") not in (None,profile_name):raise RuntimeError(f"agent reported mismatched evidence profile: {meta.get('evidence_profile')} != {profile_name}")
    preclassified=item.get("claim_classes") or []
    if profile.get("require_claim_classification"):
        used=meta.get("claim_classes_used") or []
        if not isinstance(used,list) or not used:raise RuntimeError(f"candidate for {profile_name} lacks claim_classes_used")
        allowed=set(profile.get("claim_classes",{}))
        if allowed and any(x not in allowed for x in used):raise RuntimeError(f"candidate for {profile_name} reports invalid claim class")
        if preclassified and not set(preclassified).intersection(used):raise RuntimeError(f"candidate claim classification no longer overlaps pre-research classification")
    route_id,_=publication_route(profile,item.get("publication_route_hint"))
    recommendation=meta.get("publication_recommendation") or route_id
    allowed_routes=profile.get("allowed_publication_routes",[])
    if allowed_routes and recommendation not in allowed_routes:raise RuntimeError(f"publication recommendation {recommendation!r} is not allowed for {profile_name}")
    required=["## Forschungsfrage","## Befundlage","## Gegenbefunde und Unsicherheit","## Claim-Source-Mapping","## Quellen","## Relevanz für KUEPER-Projekte","## Offene Fragen"]
    if profile.get("require_claim_classification"):required.append("## Claim-Klassifikation")
    if profile.get("require_freshness_check") or profile.get("require_conflict_check"):required.append("## Aktualität und Widerspruchsprüfung")
    if route_id:required.append("## Publikationsroute")
    missing=[x for x in required if x not in text]
    if missing:raise RuntimeError(f"missing candidate sections: {missing}")
    return meta

def update_queue(token:str,payload:dict[str,Any],item:dict[str,Any],status:str,pr_url:str|None=None,error:str|None=None):
    changed=dict(item);changed["status"]=status;changed["updated_at"]=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    if pr_url:changed["candidate_pr"]=pr_url
    if error:changed["last_error"]=error[-1500:]
    content=base64.b64encode((json.dumps(changed,indent=2,ensure_ascii=False)+"\n").encode()).decode()
    gh(token,"PUT",f"/repos/{CONTROL}/contents/research/queue/{item['id']}.json",{"message":f"research: mark {item['id']} {status}","content":content,"sha":payload["sha"],"branch":"main"})

def execute(token:str,item:dict[str,Any],payload:dict[str,Any])->dict[str,Any]:
    root=Path(tempfile.mkdtemp(prefix=f"research-{item['id']}-"));branch=f"research/{item['id'].lower()}"
    try:
        if item.get("external_research_required") is False:raise RuntimeError("queued item was classified as not requiring external research")
        source_context=source_document_context(token,item)
        default=repo_info(token,TARGET)["default_branch"]
        run(["git","clone","--quiet","--branch",default,"--single-branch",auth_url(TARGET,token),str(root)])
        run(["git","checkout","-b",branch],cwd=root)
        cmd=shlex.split(os.environ.get("KUEPER_RESEARCH_AGENT_CMD",'codex exec --full-auto -c web_search="live"'))
        cp=run(cmd+[research_prompt(item,source_context)],cwd=root,check=False)
        if cp.returncode:raise RuntimeError((cp.stdout or "")[-4000:])
        meta=validate_result(root,item);(root/".research-result.json").unlink()
        changed=run(["git","status","--porcelain","--untracked-files=all"],cwd=root).stdout or "";paths=[]
        for line in changed.splitlines():
            p=line[3:].strip();p=p.split(" -> ",1)[1] if " -> " in p else p
            if p:paths.append(p)
        allowed=f"{POLICY['candidate_path']}/{item['id']}.md"
        if paths!=[allowed]:raise RuntimeError(f"research agent changed forbidden files: {paths}")
        run(["git","config","user.name","KUEPER Research Bot"],cwd=root);run(["git","config","user.email","research-bot@users.noreply.github.com"],cwd=root)
        run(["git","add",allowed],cwd=root);run(["git","commit","-m",f"research: candidate {item['id']}"],cwd=root);run(["git","push","--quiet","origin",branch],cwd=root)
        pr=gh(token,"POST",f"/repos/{TARGET}/pulls",{"title":f"[Research] {item['id']}: {item['title']}","head":branch,"base":default,"body":f"Multilingual evidence candidate for `{item['source_project']}` using evidence profile `{evidence_profile(item)[0]}`. Evidence score: `{meta.get('evidence_score')}`. Publication recommendation: `{meta.get('publication_recommendation') or 'none'}`. This PR adds only non-canonical staging material under `{POLICY['candidate_path']}/`; it does not modify canonical KG data or publish to OTA/kueper.com. Merge remains review-gated and is never enabled by the research executor.","draft":False})
        merge="review-required"
        update_queue(token,payload,item,"candidate-pr",pr["html_url"])
        return {"id":item["id"],"result":"candidate-pr","pr":pr["html_url"],"merge":merge,"evidence_score":meta.get("evidence_score"),"languages_used":meta.get("languages_used"),"publication_recommendation":meta.get("publication_recommendation")}
    except Exception as exc:
        try:update_queue(token,payload,item,"needs-review",error=str(exc))
        except Exception:pass
        return {"id":item["id"],"result":"needs-review","error":str(exc)}
    finally:shutil.rmtree(root,ignore_errors=True)

def main()->int:
    token=os.environ.get("KUEPER_BOT_TOKEN")
    if not token:raise SystemExit("KUEPER_BOT_TOKEN required")
    items=queue(token)[:int(POLICY["max_research_topics_per_run"])]
    results=[execute(token,item,payload) for item,payload in items]
    print(json.dumps({"selected":len(items),"results":results},indent=2,ensure_ascii=False));return 0

if __name__=="__main__":raise SystemExit(main())
