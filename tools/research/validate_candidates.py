#!/usr/bin/env python3
"""Validate merged research candidates against KUEPER consumer projects.

The validator never edits canon. It compares non-canonical research candidates with
relevant project repositories and, when action is justified, creates canonical External
Tasks asking the responsible project to review/adapt its own Source of Truth.
"""
from __future__ import annotations
import base64, datetime as dt, hashlib, json, os, re, shlex, shutil, subprocess, tempfile, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from typing import Any

API="https://api.github.com"
ROOT=Path(__file__).resolve().parents[2]
REGISTRY=json.loads((ROOT/"registry/projects.json").read_text(encoding="utf-8"))
POLICY=json.loads((ROOT/"research/policy.json").read_text(encoding="utf-8"))
CONTROL="thomaspeterkueper/kueper-ecosystem"
KG=POLICY["target_repository"]
MAX_ITEMS=int(os.environ.get("KUEPER_MAX_CANDIDATE_VALIDATIONS","3"))
CODES={"ecosystem":"ECO","knowledge-graph":"KG","ssf":"SSF","noxia":"NOXIA","noxia-universe":"NXU","mishkenaz":"MISH","omnizedenz":"OMNI","avi-modell":"AVI","contracomology":"CONTRA","kueper-archive-schema":"ARCH","endia":"ENDIA","zereya":"ZEREYA","davaru":"DAVARU","fluide-hermeneutik":"FLHERM","resonanz-ethik":"RESETH","kueper-com":"KUE","ota":"OTA","thomas-kueper-de":"TKD"}

def gh(token:str,method:str,path:str,body:dict[str,Any]|None=None)->Any:
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(API+path,data=data,method=method)
    req.add_header("Authorization",f"Bearer {token}");req.add_header("Accept","application/vnd.github+json");req.add_header("X-GitHub-Api-Version","2022-11-28")
    if data is not None:req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req) as r:
            raw=r.read();return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        payload=exc.read().decode(errors="replace");raise RuntimeError(f"GitHub HTTP {exc.code}: {payload}") from exc

def run(cmd:list[str],cwd:Path|None=None,check=True):
    cp=subprocess.run(cmd,cwd=str(cwd) if cwd else None,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if check and cp.returncode:raise RuntimeError(cp.stdout)
    return cp

def auth_url(repo,token):return f"https://x-access-token:{urllib.parse.quote(token,safe='')}@github.com/{repo}.git"
def project_map():return {p["id"]:p for p in REGISTRY["projects"] if p.get("enabled",True) and p["id"] in CODES}
def repo_default(token,repo):return gh(token,"GET",f"/repos/{repo}")["default_branch"]

def get_content(token,repo,path,ref):
    enc="/".join(urllib.parse.quote(x,safe="") for x in path.split("/"))
    try:return gh(token,"GET",f"/repos/{repo}/contents/{enc}?ref={urllib.parse.quote(ref,safe='')}")
    except RuntimeError as exc:
        if "HTTP 404" in str(exc):return None
        raise

def queue(token):
    try:items=gh(token,"GET",f"/repos/{CONTROL}/contents/research/queue?ref=main")
    except Exception:return []
    out=[]
    for item in items if isinstance(items,list) else []:
        if item.get("type")!="file" or not item.get("name","").endswith(".json"):continue
        payload=gh(token,"GET",f"/repos/{CONTROL}/contents/{item['path']}?ref=main")
        try:data=json.loads(base64.b64decode(payload.get("content","")).decode())
        except Exception:continue
        if data.get("status")=="candidate-pr":out.append((data,payload))
    return sorted(out,key=lambda x:x[0].get("updated_at",x[0].get("created","")))

def candidate_text(token,item):
    branch=repo_default(token,KG);path=f"{POLICY['candidate_path']}/{item['id']}.md";payload=get_content(token,KG,path,branch)
    if not isinstance(payload,dict):return None
    return base64.b64decode(payload.get("content","")).decode()

def assessment_prompt(item:dict[str,Any],candidate:str,projects:dict[str,dict[str,Any]])->str:
    allowed=", ".join(f"{pid}={CODES[pid]}" for pid in sorted(projects))
    return f'''You are the KUEPER research-to-canon validation agent. You are working in the repository of the primary consumer project `{item['source_project']}`.

A non-canonical evidence candidate has been merged into the Knowledge Graph staging area.
Research ID: {item['id']}

Your job is NOT to edit canon and NOT to implement changes. Compare the candidate with the current repository and determine whether it creates a concrete action for one or more registered KUEPER projects.

Possible action types:
- `conflict`: current project/canon materially contradicts stronger real-world evidence; owner should decide whether deviation is intentional or should change.
- `enrichment`: evidence can materially deepen an existing element without forcing canon.
- `verification`: the candidate exposes an unresolved assertion that should be checked before further work.
- `none`: no useful project action now.

Do not create tasks for trivia, generic inspiration, aesthetic preferences, or facts not connected to current project content. Fiction may intentionally depart from reality. Never label such departure an error without context.

Registered project IDs/codes: {allowed}
Maximum actions: 3.

Write only `.canon-assessment.json`:
{{
  "research_id":"{item['id']}",
  "summary":"...",
  "actions":[
    {{"target_project_id":"{item['source_project']}","type":"conflict|enrichment|verification","title":"...","reason":"...","requested_change":"...","expected_result":"...","priority":"low|medium|high"}}
  ]
}}
If there is no justified action, use an empty actions array. Do not edit any repository file other than `.canon-assessment.json`.

RESEARCH CANDIDATE
------------------
{candidate}
'''

def task_exists(token,target:dict[str,Any],research_id:str,title:str)->bool:
    branch=repo_default(token,target["repository"])
    needle=research_id.lower();title_n=title.lower()
    for state in ("open","parked","done"):
        listing=get_content(token,target["repository"],f"external-tasks/{state}",branch)
        if not isinstance(listing,list):continue
        for entry in listing:
            if entry.get("type")!="file" or not entry.get("name","").endswith(".md"):continue
            payload=get_content(token,target["repository"],entry["path"],branch)
            if isinstance(payload,dict):
                text=base64.b64decode(payload.get("content","")).decode(errors="replace").lower()
                if needle in text and title_n in text:return True
    return False

def next_task_id(token,target:dict[str,Any],date:str)->tuple[str,str]:
    branch=repo_default(token,target["repository"]);prefix=f"EXT-KG-{CODES[target['id']]}-{date.replace('-','')}-";nums=[]
    for state in ("open","parked","done","rejected"):
        listing=get_content(token,target["repository"],f"external-tasks/{state}",branch)
        if not isinstance(listing,list):continue
        for e in listing:
            m=re.match(re.escape(prefix)+r"(\d{3})\.md$",e.get("name",""))
            if m:nums.append(int(m.group(1)))
    return f"{prefix}{max(nums,default=0)+1:03d}",branch

def create_task(token,item,action,target):
    if task_exists(token,target,item["id"],action["title"]):return {"result":"duplicate","target":target["id"]}
    today=dt.date.today().isoformat();ident,branch=next_task_id(token,target,today);code=CODES[target["id"]]
    priority=action.get("priority","medium") if action.get("priority") in {"low","medium","high"} else "medium"
    content=f'''---
id: {ident}
title: {action['title']}
status: open
source: KG
target: {code}
created: {today}
requested_by: research-validation-loop
priority: {priority}
affects: [KG, {code}]
---

## Anlass

Research Candidate `{item['id']}` wurde gegen den aktuellen Projektstand geprüft. Bewertung: **{action['type']}**.

{action['reason']}

## Gewünschte Änderung

{action['requested_change']}

## Begründung

Die Evidenz liegt als nicht-kanonischer Research Candidate im Knowledge Graph. Die fachliche Entscheidung über eine Übernahme, bewusste Abweichung oder Anpassung bleibt beim Zielprojekt.

## Betroffene Repositories

- `kueper-knowledge-graph`
- `{target['repository']}`

## Erwartetes Ergebnis

{action['expected_result']}

## Hinweise

Research ID: `{item['id']}`. Dieser Request darf den Kanon nicht automatisch ändern; das Zielprojekt entscheidet im eigenen Kontext.
'''
    path=f"external-tasks/open/{ident}.md";encoded=base64.b64encode(content.encode()).decode()
    gh(token,"PUT",f"/repos/{target['repository']}/contents/{path}",{"message":f"chore(tasks): research validation {ident}","content":encoded,"branch":branch})
    return {"result":"created","id":ident,"target":target["id"],"repository":target["repository"]}

def update_queue(token,payload,item,status,assessment=None,created=None,error=None):
    data=dict(item);data["status"]=status;data["validated_at"]=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    if assessment:data["validation_summary"]=assessment[:1000]
    if created:data["consumer_requests"]=created
    if error:data["validation_error"]=error[-1500:]
    content=base64.b64encode((json.dumps(data,indent=2,ensure_ascii=False)+"\n").encode()).decode()
    gh(token,"PUT",f"/repos/{CONTROL}/contents/research/queue/{item['id']}.json",{"message":f"research: validate {item['id']}","content":content,"sha":payload["sha"],"branch":"main"})

def validate_one(token,item,payload,projects):
    candidate=candidate_text(token,item)
    if candidate is None:return {"id":item["id"],"result":"candidate-not-merged"}
    primary=projects.get(item.get("source_project"))
    if not primary:
        update_queue(token,payload,item,"validation-error",error="unknown source project");return {"id":item["id"],"result":"validation-error"}
    root=Path(tempfile.mkdtemp(prefix=f"validate-{item['id']}-"))
    try:
        run(["git","clone","--quiet","--depth","1",auth_url(primary["repository"],token),str(root)])
        cmd=shlex.split(os.environ.get("KUEPER_VALIDATION_AGENT_CMD","codex exec --full-auto"));cp=run(cmd+[assessment_prompt(item,candidate,projects)],cwd=root,check=False)
        if cp.returncode:raise RuntimeError((cp.stdout or "")[-4000:])
        af=root/".canon-assessment.json"
        if not af.exists():raise RuntimeError("agent did not create .canon-assessment.json")
        assessment=json.loads(af.read_text(encoding="utf-8"));actions=assessment.get("actions",[])[:3];created=[]
        for action in actions:
            pid=action.get("target_project_id")
            if pid not in projects or pid=="knowledge-graph":continue
            if action.get("type") not in {"conflict","enrichment","verification"}:continue
            if not all(isinstance(action.get(k),str) and action[k].strip() for k in ("title","reason","requested_change","expected_result")):continue
            created.append(create_task(token,item,action,projects[pid]))
        status="consumer-requests" if any(x.get("result")=="created" for x in created) else "validated-no-action"
        update_queue(token,payload,item,status,assessment=str(assessment.get("summary","")),created=created)
        return {"id":item["id"],"result":status,"requests":created}
    except Exception as exc:
        try:update_queue(token,payload,item,"validation-error",error=str(exc))
        except Exception:pass
        return {"id":item["id"],"result":"validation-error","error":str(exc)}
    finally:shutil.rmtree(root,ignore_errors=True)

def main()->int:
    token=os.environ.get("KUEPER_BOT_TOKEN")
    if not token:raise SystemExit("KUEPER_BOT_TOKEN required")
    projects=project_map();items=queue(token)[:MAX_ITEMS];results=[validate_one(token,item,payload,projects) for item,payload in items]
    print(json.dumps({"selected":len(items),"results":results},indent=2,ensure_ascii=False));return 0

if __name__=="__main__":raise SystemExit(main())
