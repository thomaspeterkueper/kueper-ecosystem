#!/usr/bin/env python3
"""KUEPER Ecosystem autonomous task loop v2.

Scans registered repositories for canonical open External Tasks, executes selected
work in the responsible target repository, and publishes changes through PRs.
Project agents may emit structured cross-repository follow-up envelopes into
`.kueper/outbox/`; the control plane routes those envelopes on the next sweep.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

API = "https://api.github.com"
ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "registry" / "projects.json"
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
REVIEW_ONLY_PREFIXES = (".github/", "migrations/", "supabase/migrations/", "infra/", "terraform/", "auth/", "security/")
REVIEW_ONLY_FILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "vercel.json"}

class LoopError(RuntimeError): pass

@dataclass(frozen=True)
class Project:
    id: str; name: str; repository: str; code: str; enabled: bool

@dataclass(frozen=True)
class Task:
    project: Project; path: str; filename: str; content: str; id: str; title: str
    status: str; source: str; target: str; priority: str; created: str

def run(cmd: list[str], *, cwd: Path | None=None, env: dict[str,str] | None=None, check: bool=True, capture: bool=True):
    cp=subprocess.run(cmd,cwd=str(cwd) if cwd else None,env=env,text=True,stdout=subprocess.PIPE if capture else None,stderr=subprocess.STDOUT if capture else None,check=False)
    if check and cp.returncode!=0: raise LoopError(f"command failed ({cp.returncode}): {' '.join(cmd)}\n{cp.stdout or ''}")
    return cp

def gh_request(token:str, method:str, path:str, body:dict[str,Any]|None=None)->Any:
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(API+path,data=data,method=method)
    req.add_header("Authorization",f"Bearer {token}"); req.add_header("Accept","application/vnd.github+json"); req.add_header("X-GitHub-Api-Version","2022-11-28")
    if data is not None: req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req) as response:
            raw=response.read(); return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        payload=exc.read().decode(errors="replace"); raise LoopError(f"GitHub {method} {path}: HTTP {exc.code}: {payload}") from exc

def repo_info(token,repo): return gh_request(token,"GET",f"/repos/{repo}")
def branch_head(token,repo,branch): return gh_request(token,"GET",f"/repos/{repo}/git/ref/heads/{urllib.parse.quote(branch,safe='')}")["object"]["sha"]
def contents(token,repo,path,ref):
    enc="/".join(urllib.parse.quote(p,safe="") for p in path.split("/"))
    try: return gh_request(token,"GET",f"/repos/{repo}/contents/{enc}?ref={urllib.parse.quote(ref,safe='')}")
    except LoopError as exc:
        if "HTTP 404" in str(exc): return None
        raise

def decode_content(payload):
    import base64
    return base64.b64decode(payload.get("content","")).decode()
def parse_scalar(raw):
    raw=raw.strip()
    if not raw:return ""
    if raw.startswith("[") and raw.endswith("]"): return [x.strip().strip("'\"") for x in raw[1:-1].split(",") if x.strip()]
    if raw.lower() in {"true","false"}:return raw.lower()=="true"
    return raw.strip("'\"")
def parse_frontmatter(text):
    if not text.startswith("---\n"):return {}
    end=text.find("\n---\n",4)
    if end<0:return {}
    out={}
    for line in text[4:end].splitlines():
        if line.strip() and not line.lstrip().startswith("#") and ":" in line:
            k,v=line.split(":",1);out[k.strip()]=parse_scalar(v)
    return out

def system_code_map(): return {"ecosystem":"ECO","knowledge-graph":"KG","ssf":"SSF","noxia":"NOXIA","noxia-universe":"NXU","mishkenaz":"MISH","omnizedenz":"OMNI","avi-modell":"AVI","contracomology":"CONTRA","kueper-archive-schema":"ARCH","endia":"ENDIA","zereya":"ZEREYA","davaru":"DAVARU","fluide-hermeneutik":"FLHERM","resonanz-ethik":"RESETH","kueper-com":"KUE","ota":"OTA","thomas-kueper-de":"TKD","buecherwelten":"BW"}
def load_projects():
    reg=json.loads(REGISTRY.read_text(encoding="utf-8"));codes=system_code_map();out=[]
    for p in reg["projects"]:
        if p["id"] in codes:out.append(Project(p["id"],p["name"],p["repository"],codes[p["id"]],p.get("enabled",True)))
    return out

def list_open_tasks(token,project):
    if not project.enabled:return []
    branch=repo_info(token,project.repository)["default_branch"];listing=contents(token,project.repository,"external-tasks/open",branch)
    if not isinstance(listing,list):return []
    tasks=[]
    for item in listing:
        if item.get("type")!="file" or not item.get("name","").endswith(".md"):continue
        payload=contents(token,project.repository,item["path"],branch)
        if not isinstance(payload,dict):continue
        text=decode_content(payload);fm=parse_frontmatter(text)
        if fm.get("status")!="open":continue
        if fm.get("target")!=project.code:
            print(f"WARN {project.repository}:{item['path']} target={fm.get('target')} expected={project.code}");continue
        tid=str(fm.get("id") or Path(item["name"]).stem)
        tasks.append(Task(project,item["path"],item["name"],text,tid,str(fm.get("title") or tid),"open",str(fm.get("source") or "UNKNOWN"),str(fm.get("target") or project.code),str(fm.get("priority") or "medium").lower(),str(fm.get("created") or "9999-12-31")))
    return tasks

def task_sort_key(t):return (PRIORITY_ORDER.get(t.priority,2),t.created,t.id)
def branch_name(t):return f"ecosystem/{re.sub(r'[^a-z0-9-]+','-',t.id.lower()).strip('-')}"[:120]
def existing_open_pr(token,repo,branch):
    owner=repo.split("/",1)[0];q=urllib.parse.urlencode({"state":"open","head":f"{owner}:{branch}","per_page":5});prs=gh_request(token,"GET",f"/repos/{repo}/pulls?{q}");return prs[0] if prs else None

def build_prompt(task,base_sha):
    depth=parse_frontmatter(task.content).get("routing_depth",0)
    try: next_depth=int(depth)+1
    except Exception: next_depth=1
    return f'''You are the autonomous project owner for repository {task.project.repository}.

External task: {task.id} — {task.title}
Base commit verified before execution: {base_sha}

MANDATORY LOOP
1. Read the repository before changing anything. Read AGENTS.md if present.
2. Re-evaluate whether the request is still sensible against the current repository state.
3. If clear, consistent, and locally owned, implement the smallest complete solution.
4. Run relevant tests/build/lint. Fix failures caused by your change.
5. Update the task lifecycle file: successful -> external-tasks/done + status done; material uncertainty/dependency -> external-tasks/parked + status parked + exact `## Rückfrage`. Never guess.
6. If this work reveals a concrete need owned by ANOTHER registered KUEPER repository, create ONE structured JSON envelope per distinct need under `.kueper/outbox/`. Do not edit the other repository. Filename: `<parent-task>--<target>--<short-slug>.json`.
   Required JSON fields: target, title, reason, requested_change, expected_result. Optional: priority, affects. Always set `parent_task` to `{task.id}` and `depth` to {next_depth}.
   Only emit a follow-up when the current task cannot or should not own that work. Do not create speculative, nice-to-have, duplicate, self-targeted, or circular requests. Maximum useful follow-ups from this task: 3.
7. Never put secrets in files/logs. Do not weaken tests to get green status.
8. Finish with only intentional changes.

Registered target codes: {', '.join(sorted(system_code_map().values()))}

Task document:

{task.content}
'''

def changed_files(repo_dir):
    out=run(["git","status","--porcelain"],cwd=repo_dir).stdout or "";files=[]
    for line in out.splitlines():
        p=line[3:].strip();p=p.split(" -> ",1)[1] if " -> " in p else p
        if p:files.append(p)
    return files

def requires_review(paths,task):
    reasons=[]
    if task.priority=="critical":reasons.append("critical-priority")
    for p in paths:
        if p in REVIEW_ONLY_FILES or any(p.startswith(x) for x in REVIEW_ONLY_PREFIXES):reasons.append(p)
    return bool(reasons),sorted(set(reasons))
def authenticated_clone_url(repo,token):return f"https://x-access-token:{urllib.parse.quote(token,safe='')}@github.com/{repo}.git"

def process_task(token,task,agent_cmd,work_root,auto_merge):
    info=repo_info(token,task.project.repository);default_branch=info["default_branch"];observed=branch_head(token,task.project.repository,default_branch);bname=branch_name(task)
    existing=existing_open_pr(token,task.project.repository,bname)
    if existing:return {"task":task.id,"result":"already-in-progress","pr":existing.get("html_url")}
    run_dir=Path(tempfile.mkdtemp(prefix=f"{task.project.id}-",dir=str(work_root)))
    try:
        run(["git","clone","--quiet","--branch",default_branch,"--single-branch",authenticated_clone_url(task.project.repository,token),str(run_dir)])
        local=run(["git","rev-parse","HEAD"],cwd=run_dir).stdout.strip();current=branch_head(token,task.project.repository,default_branch)
        if local!=observed or current!=observed:return {"task":task.id,"result":"rescan-and-replan","observed":observed,"current":current}
        run(["git","checkout","-b",bname],cwd=run_dir);agent=run(shlex.split(agent_cmd)+[build_prompt(task,observed)],cwd=run_dir,env=os.environ.copy(),check=False)
        if agent.returncode!=0:return {"task":task.id,"result":"agent-failed","exit":agent.returncode,"output_tail":(agent.stdout or "")[-4000:]}
        paths=changed_files(run_dir)
        if not paths:return {"task":task.id,"result":"no-change"}
        forbidden=[p for p in paths if p==".env" or p.startswith(".env.") or "credentials" in p.lower()]
        if forbidden:return {"task":task.id,"result":"blocked-sensitive-files","files":forbidden}
        run(["git","config","user.name","KUEPER Ecosystem Bot"],cwd=run_dir);run(["git","config","user.email","ecosystem-bot@users.noreply.github.com"],cwd=run_dir);run(["git","add","-A"],cwd=run_dir);run(["git","commit","-m",f"chore(loop): execute {task.id}"],cwd=run_dir);run(["git","push","--quiet","origin",bname],cwd=run_dir)
        pr=gh_request(token,"POST",f"/repos/{task.project.repository}/pulls",{"title":f"[Loop] {task.id}: {task.title}","head":bname,"base":default_branch,"body":f"Autonomously executed `{task.id}` from `{task.source}`. Base HEAD: `{observed}`. Structured cross-repo follow-ups, if any, are emitted only to `.kueper/outbox/` for central routing.","draft":False})
        review,reasons=requires_review(paths,task);merge="review-required"
        if auto_merge and not review:
            env=os.environ.copy();env["GH_TOKEN"]=token;cp=run(["gh","pr","merge",pr["html_url"],"--auto","--squash","--delete-branch"],cwd=run_dir,env=env,check=False);merge="auto-merge-queued" if cp.returncode==0 else "auto-merge-unavailable"
        return {"task":task.id,"result":"pr-created","pr":pr["html_url"],"merge":merge,"review_reasons":reasons,"changed_files":paths}
    finally:shutil.rmtree(run_dir,ignore_errors=True)

def main():
    token=os.environ.get("KUEPER_BOT_TOKEN");api_key=os.environ.get("OPENAI_API_KEY")
    if not token:print("KUEPER_BOT_TOKEN is required",file=sys.stderr);return 2
    if not api_key:print("OPENAI_API_KEY is required",file=sys.stderr);return 2
    max_tasks=max(1,int(os.environ.get("KUEPER_MAX_TASKS","3")));auto_merge=os.environ.get("KUEPER_AUTO_MERGE","true").lower() in {"1","true","yes","on"};agent_cmd=os.environ.get("KUEPER_AGENT_CMD","codex exec --full-auto");work_root=Path(os.environ.get("KUEPER_WORKDIR","/tmp/kueper-ecosystem-loop"));work_root.mkdir(parents=True,exist_ok=True)
    tasks=[]
    for project in load_projects():
        try:tasks.extend(list_open_tasks(token,project))
        except Exception as exc:print(f"ERROR scan {project.repository}: {exc}",file=sys.stderr)
    tasks.sort(key=task_sort_key);selected=tasks[:max_tasks];results=[]
    for task in selected:
        try:results.append(process_task(token,task,agent_cmd,work_root,auto_merge))
        except Exception as exc:results.append({"task":task.id,"result":"error","error":str(exc)})
    print(json.dumps({"generated_at":dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),"open_tasks_seen":len(tasks),"tasks_selected":len(selected),"results":results},indent=2,ensure_ascii=False));return 0 if not any(r.get("result")=="error" for r in results) else 1

if __name__=="__main__":raise SystemExit(main())
