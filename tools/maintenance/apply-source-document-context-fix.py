#!/usr/bin/env python3
from pathlib import Path

path = Path('tools/research/execute.py')
text = path.read_text(encoding='utf-8')

if 'def source_document_context(' in text:
    raise SystemExit('source-document context already applied')

anchor = '''def publication_route(profile:dict[str,Any],hint:str|None=None)->tuple[str|None,dict[str,Any]]:\n    allowed=profile.get("allowed_publication_routes",[])\n    route_id=hint or profile.get("default_publication_route")\n    if route_id and allowed and route_id not in allowed:raise RuntimeError(f"publication route {route_id} is not allowed for evidence profile")\n    route=(POLICY.get("publication_routing",{}) or {}).get(route_id,{}) if route_id else {}\n    if route_id and not route:raise RuntimeError(f"publication route {route_id} is not defined")\n    return route_id,route\n'''
insert = anchor + '''\ndef source_document_context(token:str,item:dict[str,Any])->dict[str,Any]|None:\n    """Fetch the exact declared source document before external research.\n\n    A declared source_path is a hard contract: if it cannot be loaded from the\n    declared source repository's real default branch, research fails closed.\n    """\n    source_path=item.get("source_path")\n    if not source_path:return None\n    source_repo=item.get("source_repository")\n    if not source_repo:raise RuntimeError(f"queued item {item.get('id')} declares source_path but no source_repository")\n    info=repo_info(token,source_repo);default=info.get("default_branch")\n    if not default:raise RuntimeError(f"cannot resolve default branch for source repository {source_repo}")\n    encoded_path=urllib.parse.quote(str(source_path),safe='/');encoded_ref=urllib.parse.quote(str(default),safe='')\n    payload=gh(token,"GET",f"/repos/{source_repo}/contents/{encoded_path}?ref={encoded_ref}")\n    if not isinstance(payload,dict) or payload.get("type")!="file" or not payload.get("content"):\n        raise RuntimeError(f"declared source document is not a readable file: {source_repo}@{default}:{source_path}")\n    try:text=base64.b64decode(payload["content"]).decode("utf-8")\n    except Exception as exc:raise RuntimeError(f"cannot decode declared source document {source_repo}:{source_path}: {exc}") from exc\n    if not text.strip():raise RuntimeError(f"declared source document is empty: {source_repo}:{source_path}")\n    return {"repository":source_repo,"path":str(source_path),"ref":str(default),"sha":payload.get("sha"),"text":text}\n'''
if anchor not in text:
    raise SystemExit('publication_route anchor not found')
text = text.replace(anchor, insert, 1)

old_sig = 'def research_prompt(item:dict[str,Any])->str:\n'
new_sig = 'def research_prompt(item:dict[str,Any],source_context:dict[str,Any]|None=None)->str:\n'
if old_sig not in text:
    raise SystemExit('research_prompt signature anchor not found')
text = text.replace(old_sig, new_sig, 1)

anchor2 = '''    real_anchor=item.get("real_world_anchor") or "none specified"\n    required_sections=[]\n'''
replace2 = '''    real_anchor=item.get("real_world_anchor") or "none specified"\n    if source_context:\n        source_block=(\n            f"Source document repository: {source_context['repository']}\\n"\n            f"Source document path: {source_context['path']}\\n"\n            f"Source document ref: {source_context['ref']}\\n"\n            f"Source document blob SHA: {source_context.get('sha') or 'unknown'}\\n\\n"\n            "--- BEGIN DECLARED SOURCE DOCUMENT ---\\n"\n            f"{source_context['text']}\\n"\n            "--- END DECLARED SOURCE DOCUMENT ---"\n        )\n    else:\n        source_block="No single declared source document was supplied for this research item."\n    required_sections=[]\n'''
if anchor2 not in text:
    raise SystemExit('real_anchor anchor not found')
text = text.replace(anchor2, replace2, 1)

anchor3 = '''Publication route contract: {route_json}\n\nThe claim classification above was made BEFORE external research.'''
replace3 = '''Publication route contract: {route_json}\n\n## Declared source document context\n{source_block}\n\nIf a declared source document is present above, it is authoritative for what that source document actually says. Audit and classify claims from that exact text. Do not claim that the document is unavailable, and do not reconstruct its contents from adjacent ecosystem documents. Adjacent documents may be used only as explicitly identified secondary ecosystem context.\n\nThe claim classification above was made BEFORE external research.'''
if anchor3 not in text:
    raise SystemExit('prompt insertion anchor not found')
text = text.replace(anchor3, replace3, 1)

anchor4 = '''        default=repo_info(token,TARGET)["default_branch"]\n        run(["git","clone","--quiet","--branch",default,"--single-branch",auth_url(TARGET,token),str(root)])\n        run(["git","checkout","-b",branch],cwd=root)\n        cmd=shlex.split(os.environ.get("KUEPER_RESEARCH_AGENT_CMD",'codex exec --full-auto -c web_search="live"'))\n        cp=run(cmd+[research_prompt(item)],cwd=root,check=False)\n'''
replace4 = '''        source_context=source_document_context(token,item)\n        default=repo_info(token,TARGET)["default_branch"]\n        run(["git","clone","--quiet","--branch",default,"--single-branch",auth_url(TARGET,token),str(root)])\n        run(["git","checkout","-b",branch],cwd=root)\n        cmd=shlex.split(os.environ.get("KUEPER_RESEARCH_AGENT_CMD",'codex exec --full-auto -c web_search="live"'))\n        cp=run(cmd+[research_prompt(item,source_context)],cwd=root,check=False)\n'''
if anchor4 not in text:
    raise SystemExit('execute anchor not found')
text = text.replace(anchor4, replace4, 1)

path.write_text(text, encoding='utf-8')
print('Applied source-document context fix to tools/research/execute.py')
