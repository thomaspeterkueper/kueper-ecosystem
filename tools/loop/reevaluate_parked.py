#!/usr/bin/env python3
"""Re-evaluate parked External Tasks and reopen them when blockers disappear.

This loop never implements the task. It only asks whether the current repository state
now provides the missing prerequisite. Human-decision blockers stay parked.
"""
from __future__ import annotations

import base64
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.github.com"
ROOT = Path(__file__).resolve().parents[2]
REGISTRY = json.loads((ROOT / "registry/projects.json").read_text(encoding="utf-8"))
MAX_ITEMS = int(os.environ.get("KUEPER_MAX_PARKED_REEVALUATIONS", "3"))
CODES = {
    "ecosystem":"ECO","knowledge-graph":"KG","ssf":"SSF","noxia":"NOXIA",
    "noxia-universe":"NXU","mishkenaz":"MISH","omnizedenz":"OMNI","avi-modell":"AVI",
    "contracomology":"CONTRA","kueper-archive-schema":"ARCH","endia":"ENDIA","zereya":"ZEREYA",
    "davaru":"DAVARU","fluide-hermeneutik":"FLHERM","resonanz-ethik":"RESETH",
    "kueper-com":"KUE","ota":"OTA","thomas-kueper-de":"TKD","buecherwelten":"BW"
}

def gh(token:str, method:str, path:str, body:dict[str,Any]|None=None)->Any:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None: req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode(errors="replace")
        raise RuntimeError(f"GitHub {method} {path}: HTTP {exc.code}: {payload}") from exc

def run(cmd:list[str], cwd:Path|None=None, check=True):
    cp = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if check and cp.returncode: raise RuntimeError(cp.stdout)
    return cp

def auth_url(repo, token): return f"https://x-access-token:{urllib.parse.quote(token,safe='')}@github.com/{repo}.git"
def default_branch(token, repo): return gh(token,"GET",f"/repos/{repo}")["default_branch"]
def get_content(token, repo, path, ref):
    enc = "/".join(urllib.parse.quote(x,safe="") for x in path.split("/"))
    try: return gh(token,"GET",f"/repos/{repo}/contents/{enc}?ref={urllib.parse.quote(ref,safe='')}")
    except RuntimeError as exc:
        if "HTTP 404" in str(exc): return None
        raise

def decode(payload): return base64.b64decode(payload.get("content","")).decode()
def projects():
    return [p for p in REGISTRY["projects"] if p.get("enabled",True) and p["id"] in CODES]

def parked_tasks(token):
    out=[];errors=[]
    for p in projects():
        try:
            repo=p["repository"];branch=default_branch(token,repo)
            listing=get_content(token,repo,"external-tasks/parked",branch)
            for item in listing if isinstance(listing,list) else []:
                if item.get("type")!="file" or not item.get("name","").endswith(".md"): continue
                payload=get_content(token,repo,item["path"],branch)
                if isinstance(payload,dict): out.append((p,branch,item,payload,decode(payload)))
        except Exception as exc:
            # Ein fehlgeschlagenes Projekt (z. B. privates Repository ohne
            # Token-Zugriff, HTTP 404) darf den gesamten Sweep nicht abbrechen.
            errors.append({"repository":p["repository"],"result":"error","error":str(exc)})
            print(f"ERROR scan {p['repository']}: {exc}", file=sys.stderr)
    return out,errors

def prompt(repo:str, task:str)->str:
    return f'''You are the parked-task gate for repository `{repo}`.

Read the CURRENT repository before deciding. Do not modify project files.
A parked External Task is included below.

Determine only whether the blocker that caused parking has disappeared.
Return `.parked-assessment.json` exactly as JSON:
{{"ready":true|false,"human_decision_required":true|false,"reason":"specific current-state reason"}}

Rules:
- ready=true only when the repository now contains the prerequisite needed to execute the task correctly.
- if the task is blocked on an explicit owner/creative/architectural decision, set human_decision_required=true and ready=false.
- absence of evidence is not readiness.
- do not implement the task.
- do not edit any file except `.parked-assessment.json`.

PARKED TASK
-----------
{task}
'''

def move_to_open(token, repo, branch, item, payload, text):
    updated=text.replace("status: parked","status: open",1)
    marker="\n## Automatische Wiederaufnahme\n\nDer Parked-Reevaluation-Loop hat festgestellt, dass die zuvor fehlende interne Voraussetzung im aktuellen Repository-Zustand vorhanden ist.\n"
    if "## Automatische Wiederaufnahme" not in updated: updated += marker
    open_path=f"external-tasks/open/{item['name']}"
    gh(token,"PUT",f"/repos/{repo}/contents/{open_path}",{
        "message":f"chore(tasks): reopen {item['name']}",
        "content":base64.b64encode(updated.encode()).decode(),"branch":branch
    })
    enc="/".join(urllib.parse.quote(x,safe="") for x in item["path"].split("/"))
    gh(token,"DELETE",f"/repos/{repo}/contents/{enc}",{
        "message":f"chore(tasks): move {item['name']} back to open","sha":payload["sha"],"branch":branch
    })

def assess(token,p,branch,item,payload,text):
    root=Path(tempfile.mkdtemp(prefix=f"parked-{p['id']}-"))
    try:
        run(["git","clone","--quiet","--branch",branch,"--single-branch",auth_url(p["repository"],token),str(root)])
        cmd=shlex.split(os.environ.get("KUEPER_PARKED_AGENT_CMD","codex exec --full-auto"))
        cp=run(cmd+[prompt(p["repository"],text)],cwd=root,check=False)
        if cp.returncode: return {"task":item["name"],"result":"assessment-failed","error":(cp.stdout or "")[-2000:]}
        jf=root/".parked-assessment.json"
        if not jf.exists(): return {"task":item["name"],"result":"assessment-missing"}
        data=json.loads(jf.read_text(encoding="utf-8"))
        if data.get("ready") is True and data.get("human_decision_required") is not True:
            move_to_open(token,p["repository"],branch,item,payload,text)
            return {"task":item["name"],"result":"reopened","reason":data.get("reason")}
        return {"task":item["name"],"result":"still-parked","human_decision_required":bool(data.get("human_decision_required")),"reason":data.get("reason")}
    finally:
        shutil.rmtree(root,ignore_errors=True)

def main():
    token=os.environ.get("KUEPER_BOT_TOKEN")
    if not token: raise SystemExit("KUEPER_BOT_TOKEN required")
    tasks,project_errors=parked_tasks(token)
    tasks=tasks[:MAX_ITEMS]
    results=list(project_errors)
    for args in tasks:
        try: results.append(assess(token,*args))
        except Exception as exc: results.append({"task":args[2].get("name"),"result":"error","error":str(exc)})
    print(json.dumps({"selected":len(tasks),"results":results},indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__": raise SystemExit(main())
