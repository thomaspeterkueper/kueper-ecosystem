#!/usr/bin/env python3
"""Delete source outbox envelopes after they have been successfully routed or deduplicated.

Auditability remains in the canonical External Task via routing_fingerprint/parent_task.
Invalid/unroutable envelopes are intentionally retained for inspection.
"""
from __future__ import annotations
import base64, hashlib, json, os, re, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from typing import Any

API="https://api.github.com"
ROOT=Path(__file__).resolve().parents[2]
REG=json.loads((ROOT/"registry/projects.json").read_text(encoding="utf-8"))
CODES={"ecosystem":"ECO","knowledge-graph":"KG","ssf":"SSF","noxia":"NOXIA","noxia-universe":"NXU","mishkenaz":"MISH","omnizedenz":"OMNI","avi-modell":"AVI","contracomology":"CONTRA","kueper-archive-schema":"ARCH","endia":"ENDIA","zereya":"ZEREYA","davaru":"DAVARU","fluide-hermeneutik":"FLHERM","resonanz-ethik":"RESETH","kueper-com":"KUE","ota":"OTA","thomas-kueper-de":"TKD"}

def gh(token:str,method:str,path:str,body:dict[str,Any]|None=None):
    data=None if body is None else json.dumps(body).encode();req=urllib.request.Request(API+path,data=data,method=method)
    req.add_header("Authorization",f"Bearer {token}");req.add_header("Accept","application/vnd.github+json");req.add_header("X-GitHub-Api-Version","2022-11-28")
    if data is not None:req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req) as r:
            raw=r.read();return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        if exc.code==404:return None
        raise RuntimeError(exc.read().decode(errors="replace")) from exc

def default(token,repo):return gh(token,"GET",f"/repos/{repo}")["default_branch"]
def enc(path):return "/".join(urllib.parse.quote(x,safe="") for x in path.split("/"))
def get(token,repo,path,ref):return gh(token,"GET",f"/repos/{repo}/contents/{enc(path)}?ref={urllib.parse.quote(ref,safe='')}")
def decode(p):return base64.b64decode(p.get("content","")).decode()
def fp(source,target,title,change):return hashlib.sha256("|".join(x.strip().lower() for x in (source,target,title,change)).encode()).hexdigest()[:16]

def targets():
    out={}
    for p in REG["projects"]:
        if p.get("enabled",True) and p["id"] in CODES:out[CODES[p["id"]]]=p
    return out

def routed_fingerprints(token,target):
    branch=default(token,target["repository"]);found=set()
    for state in ("open","parked","done","rejected"):
        listing=get(token,target["repository"],f"external-tasks/{state}",branch)
        for item in listing if isinstance(listing,list) else []:
            if item.get("type")!="file" or not item.get("name","").endswith(".md"):continue
            p=get(token,target["repository"],item["path"],branch)
            if isinstance(p,dict):
                m=re.search(r"^routing_fingerprint:\s*['\"]?([0-9a-f]+)",decode(p),re.M)
                if m:found.add(m.group(1))
    return found

def main():
    token=os.environ.get("KUEPER_BOT_TOKEN")
    if not token:raise SystemExit("KUEPER_BOT_TOKEN required")
    by_code=targets();results=[]
    for p in REG["projects"]:
        if not p.get("enabled",True) or p["id"] not in CODES:continue
        source=CODES[p["id"]];repo=p["repository"];branch=default(token,repo);listing=get(token,repo,".kueper/outbox",branch)
        for item in listing if isinstance(listing,list) else []:
            if item.get("type")!="file" or not item.get("name","").endswith(".json"):continue
            payload=get(token,repo,item["path"],branch)
            if not isinstance(payload,dict):continue
            try:env=json.loads(decode(payload))
            except Exception:continue
            target=by_code.get(env.get("target"))
            if not target:continue
            fingerprint=fp(source,target and CODES[target["id"]],str(env.get("title",'')),str(env.get("requested_change",'')))
            if fingerprint not in routed_fingerprints(token,target):continue
            gh(token,"DELETE",f"/repos/{repo}/contents/{enc(item['path'])}",{"message":f"chore(loop): consume routed envelope {item['name']}","sha":payload["sha"],"branch":branch})
            results.append({"source":repo,"file":item["path"],"result":"consumed","fingerprint":fingerprint})
    print(json.dumps({"consumed":len(results),"results":results},indent=2,ensure_ascii=False));return 0

if __name__=="__main__":raise SystemExit(main())
