#!/usr/bin/env python3
"""Execute queued KUEPER research topics and publish evidence-marked KG candidates.

Research results are staging material only. They may be auto-merged into the Knowledge
Graph's `research/candidates/` area when structural evidence gates pass, but never
become canonical entities/relations automatically.
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

def research_prompt(item:dict[str,Any])->str:
    langs=", ".join(item.get("languages") or POLICY["default_languages"])
    return f'''You are the evidence research agent for the KUEPER ecosystem.

Research ID: {item['id']}
Source project: {item['source_project']}
Question: {item['question']}
Why now: {item.get('why_now','')}
Requested source languages: {langs}

Use live web search. Research the question rigorously. Languages are discovery channels, NOT evidence rankings. Prefer primary sources, peer-reviewed work, official institutions, and academic publishers. Search in the languages that materially improve coverage; do not force every language if it adds no value. Compare conflicting evidence.

You MUST distinguish established findings, inference, open/contested points, and implications for the source project. Do not convert fictional canon into real-world evidence or real-world evidence into fictional canon.

Create exactly two files in the checkout:
1. `.research-result.json` containing:
{{"evidence_score":0.0,"source_count":0,"distinct_domains":0,"languages_used":["en"],"uncertainty":"low|medium|high","candidate_filename":"{item['id']}.md"}}
2. `research/candidates/{item['id']}.md` with sections:
# title
Metadata (Research ID, source project, status: candidate/non-canonical, researched date)
## Forschungsfrage
## Kurzfazit
## Befundlage
## Gegenbefunde und Unsicherheit
## Claim-Source-Mapping
For every material claim, map it to one or more numbered sources.
## Quellen
For each source include title, author/institution, publication date if available, URL, source language, source type.
## Relevanz für KUEPER-Projekte
Clearly separate real-world implications from possible fictional/worldbuilding use.
## Offene Fragen

Evidence score guide: 0.9+ multiple strong primary/peer-reviewed sources; 0.75 solid convergent evidence; 0.65 useful but with limitations; below 0.65 insufficient for candidate staging.
Never fabricate a citation, URL, publication, author, translation, or quote.
Do not edit canonical KG entities, relations, mappings, schemas, external tasks, or any other file.
'''

def validate_result(root:Path,item:dict[str,Any])->dict[str,Any]:
    jf=root/".research-result.json";candidate=root/POLICY["candidate_path"]/f"{item['id']}.md"
    if not jf.exists() or not candidate.exists():raise RuntimeError("research agent did not create required result files")
    meta=json.loads(jf.read_text(encoding="utf-8"));score=float(meta.get("evidence_score",0));src=int(meta.get("source_count",0));domains=int(meta.get("distinct_domains",0))
    text=candidate.read_text(encoding="utf-8");urls=re.findall(r"https?://[^\s)>]+",text)
    if score<float(POLICY["minimum_evidence_score_for_candidate"]):raise RuntimeError(f"evidence score too low: {score}")
    if src<2 or domains<2 or len(set(urls))<2:raise RuntimeError("candidate requires >=2 sources from >=2 domains with URLs")
    required=["## Forschungsfrage","## Befundlage","## Gegenbefunde und Unsicherheit","## Claim-Source-Mapping","## Quellen","## Relevanz für KUEPER-Projekte","## Offene Fragen"]
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
        default=repo_info(token,TARGET)["default_branch"]
        run(["git","clone","--quiet","--branch",default,"--single-branch",auth_url(TARGET,token),str(root)])
        run(["git","checkout","-b",branch],cwd=root)
        cmd=shlex.split(os.environ.get("KUEPER_RESEARCH_AGENT_CMD",'codex exec --full-auto -c web_search="live"'))
        cp=run(cmd+[research_prompt(item)],cwd=root,check=False)
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
        pr=gh(token,"POST",f"/repos/{TARGET}/pulls",{"title":f"[Research] {item['id']}: {item['title']}","head":branch,"base":default,"body":f"Multilingual evidence candidate for `{item['source_project']}`. Evidence score: `{meta.get('evidence_score')}`. This PR adds only non-canonical staging material under `{POLICY['candidate_path']}/`; it does not modify canonical KG data.","draft":False})
        merge="review-required"
        if POLICY.get("auto_merge_candidates",False):
            env=os.environ.copy();env["GH_TOKEN"]=token
            cp=run(["gh","pr","merge",pr["html_url"],"--auto","--squash","--delete-branch"],cwd=root,check=False,env=env)
            merge="auto-merge-queued" if cp.returncode==0 else "auto-merge-unavailable"
        update_queue(token,payload,item,"candidate-pr",pr["html_url"])
        return {"id":item["id"],"result":"candidate-pr","pr":pr["html_url"],"merge":merge,"evidence_score":meta.get("evidence_score"),"languages_used":meta.get("languages_used")}
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
