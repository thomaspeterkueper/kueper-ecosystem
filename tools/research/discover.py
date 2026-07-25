#!/usr/bin/env python3
"""Discover high-value knowledge gaps in eligible KUEPER projects.

The discovery agent reads one rotating project per run and writes a local JSON proposal.
Validated proposals are persisted as research queue items in kueper-ecosystem. Discovery
itself does not change project repositories or canonical knowledge.
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

def queue_existing(token:str)->set[str]:
    try:items=gh(token,"GET",f"/repos/{CONTROL}/contents/research/queue?ref=main")
    except Exception:return set()
    out=set()
    for item in items if isinstance(items,list) else []:
        if item.get("name","").endswith(".json"):
            payload=gh(token,"GET",f"/repos/{CONTROL}/contents/{item['path']}?ref=main")
            raw=base64.b64decode(payload.get("content","")).decode();
            try:out.add(json.loads(raw).get("fingerprint",""))
            except Exception:pass
    return out

def prompt(project:dict[str,Any],langs:list[str])->str:
    return f'''You are the knowledge-gap analyst for the KUEPER ecosystem. Inspect this repository deeply but DO NOT change it.
Repository: {project['repository']}
Project role: {project.get('role')}
Potential research languages: {', '.join(langs)}

Find at most 3 concrete external-knowledge gaps whose resolution would materially improve current work in this repository, its plausibility, its worldbuilding, its educational quality, or reuse across KUEPER projects.
Do not invent speculative nice-to-haves. Prefer gaps visibly grounded in existing files, TODOs, assertions, worldbuilding assumptions, scientific claims, historical/linguistic questions, or dependencies.

For each gap score 0..1:
- project_relevance
- cross_project_reuse
- uncertainty
- evidence_potential
Calculate relevance_score as their arithmetic mean.
Only include score >= {POLICY['minimum_relevance_score']}.
Choose source languages based on the topic, not quota. Local/primary-language sources may be useful but language itself is never evidence quality.

Write ONLY `.kueper-discovery.json` with this JSON structure:
{{"gaps":[{{"title":"...","question":"...","why_now":"...","project_id":"{project['id']}","suggested_languages":["en"],"project_relevance":0.0,"cross_project_reuse":0.0,"uncertainty":0.0,"evidence_potential":0.0,"relevance_score":0.0}}]}}
Do not edit any other file.
'''

def main()->int:
    token=os.environ.get("KUEPER_BOT_TOKEN");
    if not token:raise SystemExit("KUEPER_BOT_TOKEN required")
    eligible=POLICY["eligible_projects"];pmap=projects()
    day=int(dt.datetime.now(dt.timezone.utc).strftime("%Y%j"));choice=eligible[day%len(eligible)];project=pmap[choice["id"]]
    root=Path(tempfile.mkdtemp(prefix="kueper-research-discovery-"))
    results=[]
    try:
        run(["git","clone","--quiet","--depth","1",auth_url(project["repository"],token),str(root)])
        cmd=os.environ.get("KUEPER_DISCOVERY_AGENT_CMD","codex exec --full-auto").split()
        run(cmd+[prompt(project,choice.get("languages",POLICY["default_languages"]))],cwd=root)
        f=root/".kueper-discovery.json"
        if not f.exists():raise RuntimeError("agent did not create .kueper-discovery.json")
        data=json.loads(f.read_text(encoding="utf-8"));existing=queue_existing(token)
        for gap in data.get("gaps",[])[:POLICY["max_discoveries_per_run"]]:
            if gap.get("project_id")!=project["id"]:continue
            score=float(gap.get("relevance_score",0))
            if score<float(POLICY["minimum_relevance_score"]):continue
            langs=[x for x in gap.get("suggested_languages",[]) if isinstance(x,str)][:POLICY["max_languages_per_topic"]]
            seed=f"{project['id']}|{gap.get('title')}|{gap.get('question')}".lower().strip();fp=hashlib.sha256(seed.encode()).hexdigest()[:16]
            if fp in existing:continue
            now=dt.datetime.now(dt.timezone.utc);rid=f"RES-{now.strftime('%Y%m%d')}-{fp[:8].upper()}"
            item={"id":rid,"status":"queued","created":now.replace(microsecond=0).isoformat(),"source_project":project["id"],"source_repository":project["repository"],"title":gap.get("title"),"question":gap.get("question"),"why_now":gap.get("why_now"),"languages":langs or POLICY["default_languages"],"relevance_score":score,"scores":{k:gap.get(k) for k in ("project_relevance","cross_project_reuse","uncertainty","evidence_potential")},"fingerprint":fp}
            content=base64.b64encode((json.dumps(item,indent=2,ensure_ascii=False)+"\n").encode()).decode()
            gh(token,"PUT",f"/repos/{CONTROL}/contents/research/queue/{rid}.json",{"message":f"research: queue {rid}","content":content,"branch":"main"})
            existing.add(fp);results.append(item)
    finally:shutil.rmtree(root,ignore_errors=True)
    print(json.dumps({"project":project["id"],"queued":len(results),"items":results},indent=2,ensure_ascii=False));return 0

if __name__=="__main__":raise SystemExit(main())
