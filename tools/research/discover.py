#!/usr/bin/env python3
"""Discover high-value knowledge gaps in eligible KUEPER projects.

The discovery agent reads one weighted rotating project per run and writes a local JSON
proposal. Validated proposals are persisted as research queue items in kueper-ecosystem.
Discovery itself does not change project repositories or canonical knowledge.
"""
from __future__ import annotations
import base64, datetime as dt, hashlib, json, os, shutil, subprocess, tempfile, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from typing import Any

API="https://api.github.com"
ROOT=Path(__file__).resolve().parents[2]
POLICY=json.loads((ROOT/"research/policy.json").read_text(encoding="utf-8"))
REGISTRY=json.loads((ROOT/"registry/projects.json").read_text(encoding="utf-8"))
CONTROL="thomaspeterkueper/kueper-ecosystem"
ROTATION_WEIGHT_SCALE=20
PRIOR_RESEARCH_MAX_TOPICS=20

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

def run(cmd:list[str],cwd:Path|None=None):
    cp=subprocess.run(cmd,cwd=str(cwd) if cwd else None,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if cp.returncode:raise RuntimeError(cp.stdout)
    return cp.stdout

def projects()->dict[str,dict[str,Any]]:return {p["id"]:p for p in REGISTRY["projects"] if p.get("enabled",True)}
def auth_url(repo:str,token:str)->str:return f"https://x-access-token:{urllib.parse.quote(token,safe='')}@github.com/{repo}.git"

def weighted_rotation_choice(entries:list[dict[str,Any]],day_ordinal:int)->dict[str,Any]:
    """Deterministic smooth weighted round-robin choice for a UTC calendar day."""
    if not entries:raise RuntimeError("eligible_projects is empty")
    weights=[max(1,round(float(entry.get("weight",1.0))*ROTATION_WEIGHT_SCALE)) for entry in entries]
    total=sum(weights);slot=day_ordinal%total;current=[0]*len(entries);chosen=0
    for _ in range(slot+1):
        for i,weight in enumerate(weights):current[i]+=weight
        chosen=max(range(len(entries)),key=lambda i:current[i])
        current[chosen]-=total
    return entries[chosen]

def queue_history(token:str)->list[dict[str,Any]]:
    """Load existing queue metadata once for exact and semantic duplicate control."""
    try:items=gh(token,"GET",f"/repos/{CONTROL}/contents/research/queue?ref=main")
    except Exception:return []
    out=[]
    for item in items if isinstance(items,list) else []:
        if item.get("type")!="file" or not item.get("name","").endswith(".json"):continue
        try:
            payload=gh(token,"GET",f"/repos/{CONTROL}/contents/{item['path']}?ref=main")
            raw=base64.b64decode(payload.get("content","")).decode()
            data=json.loads(raw)
            if isinstance(data,dict):out.append(data)
        except Exception:pass
    return out

def prior_topics(history:list[dict[str,Any]],project_id:str)->list[dict[str,Any]]:
    same=[item for item in history if item.get("source_project")==project_id]
    same.sort(key=lambda item:item.get("created","") or "",reverse=True)
    return [
        {"id":item.get("id"),"status":item.get("status"),"title":item.get("title"),"question":item.get("question")}
        for item in same[:PRIOR_RESEARCH_MAX_TOPICS]
    ]

def prompt(project:dict[str,Any],langs:list[str],profile_name:str,profile:dict[str,Any],previous:list[dict[str,Any]])->str:
    profile_rules=json.dumps(profile,ensure_ascii=False)
    previous_json=json.dumps(previous,ensure_ascii=False,indent=2)
    claim_classes=json.dumps(profile.get("claim_classes",{}),ensure_ascii=False)
    allowed_routes=json.dumps(profile.get("allowed_publication_routes",[]),ensure_ascii=False)
    return f'''You are the knowledge-gap analyst for the KUEPER ecosystem. Inspect this repository deeply but DO NOT change it.
Repository: {project['repository']}
Project role: {project.get('role')}
Potential research languages: {', '.join(langs)}
Evidence profile: {profile_name}
Evidence profile rules: {profile_rules}
Claim classes for this profile: {claim_classes}
Allowed publication-route hints: {allowed_routes}

Previous research topics for this project (may be in different languages):
{previous_json}

Find at most 3 concrete external-knowledge gaps whose resolution would materially improve current work in this repository, its plausibility, its worldbuilding, its educational quality, or reuse across KUEPER projects.
Do not invent speculative nice-to-haves. Prefer gaps visibly grounded in existing files, TODOs, assertions, worldbuilding assumptions, scientific claims, historical/linguistic questions, or dependencies.

CRITICAL pre-research classification rule:
- Classify the material claim(s) BEFORE proposing external research.
- When the evidence profile defines claim classes, use those exact class keys. For OTA this means preserving R/T/H/S/F/W/R-Anker/OFFEN distinctions rather than flattening them into one scientific claim.
- Set `external_research_required` to true only if an externally checkable claim, premise, constraint, historical attestation, scientific anchor, or falsifiability question actually needs outside evidence.
- Pure fictional canon or work-setting claims must NOT be sent to Exa/web research merely to "validate" canon. If a proposed gap is only F/W and has no real-world anchor, omit it.
- For T/H/S, external research may test premises, constraints, counterevidence or falsifiability, but source count must not be treated as proof of the model/speculation.
- `real_world_anchor` should name the external part that is actually being researched, or be null.
- `publication_route_hint` is advisory only. If a standalone real-world scientific e-paper could result, use `real_scientific_epaper`; archive/canon material stays `fictional_archive_document`. Never imply that this discovery step publishes anything.

CRITICAL novelty rule:
- Do NOT propose a research question that is semantically the same as a previous topic merely rephrased, translated, broadened, or cosmetically narrowed.
- A genuine follow-up to prior research is allowed only when it addresses a materially unresolved dimension. In that case list the prior IDs in `related_research_ids` and explain in `novelty_reason` exactly what the new research adds that the prior candidate did not answer.
- If a previous candidate already answers the gap sufficiently, omit the gap entirely.

For each gap score 0..1:
- project_relevance
- cross_project_reuse
- uncertainty
- evidence_potential
Calculate relevance_score as their arithmetic mean.
Only include score >= {POLICY['minimum_relevance_score']}.
Choose source languages based on the topic, not quota. Local/primary-language sources may be useful but language itself is never evidence quality.

Write ONLY `.kueper-discovery.json` with this JSON structure:
{{"gaps":[{{"title":"...","question":"...","why_now":"...","project_id":"{project['id']}","suggested_languages":["en"],"claim_classes":["R"],"external_research_required":true,"real_world_anchor":"... or null","publication_route_hint":"... or null","related_research_ids":[],"novelty_reason":"","project_relevance":0.0,"cross_project_reuse":0.0,"uncertainty":0.0,"evidence_potential":0.0,"relevance_score":0.0}}]}}
Do not edit any other file.
'''

def main()->int:
    token=os.environ.get("KUEPER_BOT_TOKEN")
    if not token:raise SystemExit("KUEPER_BOT_TOKEN required")
    eligible=POLICY["eligible_projects"];pmap=projects()
    utc_day=dt.datetime.now(dt.timezone.utc).date();choice=weighted_rotation_choice(eligible,utc_day.toordinal());project=pmap[choice["id"]]
    profile_name=choice.get("evidence_profile","general");profile=POLICY.get("evidence_profiles",{}).get(profile_name,POLICY.get("evidence_profiles",{}).get("general",{}))
    history=queue_history(token);previous=prior_topics(history,project["id"]);existing={item.get("fingerprint","") for item in history}
    prior_ids={item.get("id") for item in history if item.get("source_project")==project["id"] and item.get("id")}
    allowed_claims=set(profile.get("claim_classes",{}));allowed_routes=set(profile.get("allowed_publication_routes",[]))
    root=Path(tempfile.mkdtemp(prefix="kueper-research-discovery-"));results=[]
    try:
        run(["git","clone","--quiet","--depth","1",auth_url(project["repository"],token),str(root)])
        cmd=os.environ.get("KUEPER_DISCOVERY_AGENT_CMD","codex exec --full-auto").split()
        run(cmd+[prompt(project,choice.get("languages",POLICY["default_languages"]),profile_name,profile,previous)],cwd=root)
        f=root/".kueper-discovery.json"
        if not f.exists():raise RuntimeError("agent did not create .kueper-discovery.json")
        data=json.loads(f.read_text(encoding="utf-8"))
        for gap in data.get("gaps",[])[:POLICY["max_discoveries_per_run"]]:
            if gap.get("project_id")!=project["id"]:continue
            score=float(gap.get("relevance_score",0))
            if score<float(POLICY["minimum_relevance_score"]):continue
            claim_classes=[x for x in gap.get("claim_classes",[]) if isinstance(x,str)]
            if profile.get("require_claim_classification"):
                if not claim_classes or any(x not in allowed_claims for x in claim_classes):continue
                if gap.get("external_research_required") is not True:continue
            route_hint=gap.get("publication_route_hint")
            if route_hint is not None and allowed_routes and route_hint not in allowed_routes:continue
            langs=[x for x in gap.get("suggested_languages",[]) if isinstance(x,str)][:POLICY["max_languages_per_topic"]]
            seed=f"{project['id']}|{gap.get('title')}|{gap.get('question')}".lower().strip();fp=hashlib.sha256(seed.encode()).hexdigest()[:16]
            if fp in existing:continue
            related=[rid for rid in gap.get("related_research_ids",[]) if isinstance(rid,str) and rid in prior_ids]
            novelty=str(gap.get("novelty_reason","") or "").strip()
            if gap.get("related_research_ids") and not related:continue
            if related and len(novelty)<20:continue
            now=dt.datetime.now(dt.timezone.utc);rid=f"RES-{now.strftime('%Y%m%d')}-{fp[:8].upper()}"
            item={"id":rid,"status":"queued","created":now.replace(microsecond=0).isoformat(),"source_project":project["id"],"source_repository":project["repository"],"title":gap.get("title"),"question":gap.get("question"),"why_now":gap.get("why_now"),"languages":langs or POLICY["default_languages"],"evidence_profile":profile_name,"claim_classes":claim_classes,"external_research_required":gap.get("external_research_required",True),"real_world_anchor":gap.get("real_world_anchor"),"publication_route_hint":route_hint,"project_weight":float(choice.get("weight",1.0)),"relevance_score":score,"scores":{k:gap.get(k) for k in ("project_relevance","cross_project_reuse","uncertainty","evidence_potential")},"related_research_ids":related,"novelty_reason":novelty or None,"fingerprint":fp}
            content=base64.b64encode((json.dumps(item,indent=2,ensure_ascii=False)+"\n").encode()).decode()
            gh(token,"PUT",f"/repos/{CONTROL}/contents/research/queue/{rid}.json",{"message":f"research: queue {rid}","content":content,"branch":"main"})
            existing.add(fp);results.append(item)
    finally:shutil.rmtree(root,ignore_errors=True)
    print(json.dumps({"project":project["id"],"project_weight":choice.get("weight",1.0),"evidence_profile":profile_name,"prior_topics_supplied":len(previous),"queued":len(results),"items":results},indent=2,ensure_ascii=False));return 0

if __name__=="__main__":raise SystemExit(main())
