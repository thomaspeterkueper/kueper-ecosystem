#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "registry" / "projects.json"
POLICY_PATH = ROOT / "research" / "policy.json"
DISCOVER_PATH = ROOT / "tools" / "research" / "discover.py"
EXECUTE_PATH = ROOT / "tools" / "research" / "execute.py"
EXA_PATH = ROOT / "tools" / "research" / "agent-with-exa.mjs"
DOC_PATH = ROOT / "docs" / "research-evidence-profiles.md"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"migration anchor not found: {label}")
    return text.replace(old, new, 1)


profiles = {
    "general": {
        "description": "General external research with explicit provenance and uncertainty.",
        "minimum_evidence_score": 0.65,
        "minimum_sources": 2,
        "minimum_domains": 2,
        "minimum_urls": 2,
        "preferred_source_types": ["primary-source", "peer-reviewed", "official-institution", "academic-publisher"],
        "strong_source_markers": ["primary-source", "peer-reviewed", "official-institution", "academic-publisher"],
        "require_strong_source": False,
        "scout_guidance": "Prefer direct, attributable sources. Use secondary sources for orientation or disagreement, not as a substitute for stronger evidence when stronger evidence exists."
    },
    "science": {
        "description": "Empirical and theoretical science with a strong primary-literature bias.",
        "minimum_evidence_score": 0.72,
        "minimum_sources": 3,
        "minimum_domains": 2,
        "minimum_urls": 3,
        "preferred_source_types": ["peer-reviewed", "primary-source", "official-dataset", "official-institution", "academic-publisher"],
        "strong_source_markers": ["peer-reviewed", "primary-source", "official-dataset", "official-institution"],
        "require_strong_source": True,
        "scout_guidance": "Prioritize peer-reviewed papers, original datasets, collaboration/instrument publications and official institutions. Label preprints explicitly. Distinguish measurement, accepted interpretation, model dependence and open controversy."
    },
    "avi-theoretical-cosmology": {
        "description": "Strict cosmology/theory profile for the Axiomatisches Vakuum Integral (AVI).",
        "minimum_evidence_score": 0.72,
        "minimum_sources": 3,
        "minimum_domains": 2,
        "minimum_urls": 3,
        "preferred_source_types": ["peer-reviewed", "primary-source", "official-dataset", "collaboration-publication", "academic-publisher"],
        "strong_source_markers": ["peer-reviewed", "primary-source", "official-dataset", "collaboration-publication"],
        "require_strong_source": True,
        "scout_guidance": "Treat standard cosmology, observations and mathematical results as external evidence; treat AVI-specific assumptions as model postulates unless independently supported. Separate established background, derived consequence, postulate, interpretation and falsifiable prediction. Do not use metaphysical analogy as physical evidence."
    },
    "technical-scientific": {
        "description": "Engineering/technology research anchored in standards, original documentation and science.",
        "minimum_evidence_score": 0.68,
        "minimum_sources": 2,
        "minimum_domains": 2,
        "minimum_urls": 2,
        "preferred_source_types": ["standard", "official-technical-documentation", "peer-reviewed", "primary-source", "official-institution"],
        "strong_source_markers": ["standard", "official-technical-documentation", "peer-reviewed", "primary-source"],
        "require_strong_source": True,
        "scout_guidance": "Prefer standards bodies, original technical documentation, peer-reviewed engineering literature and official datasets. Vendor material may establish product facts but not independent performance claims. Community posts are leads only unless independently corroborated."
    },
    "historical-linguistic": {
        "description": "Historical, archaeological and linguistic research with attestation/reconstruction separation.",
        "minimum_evidence_score": 0.68,
        "minimum_sources": 3,
        "minimum_domains": 2,
        "minimum_urls": 3,
        "preferred_source_types": ["primary-historical-source", "archaeological-publication", "peer-reviewed", "academic-corpus", "scholarly-grammar", "academic-publisher"],
        "strong_source_markers": ["primary-historical-source", "archaeological-publication", "peer-reviewed", "academic-corpus", "scholarly-grammar"],
        "require_strong_source": True,
        "scout_guidance": "Separate directly attested forms/finds, scholarly reconstruction, comparative inference and fictional extrapolation. Prefer archaeological reports, corpora, scholarly grammars, historical primary sources and peer-reviewed historical linguistics. Search relevant source languages when they materially improve access to primary scholarship."
    },
    "worldbuilding-scientific": {
        "description": "Real-world plausibility research for fictional settings while preserving the canon/evidence boundary.",
        "minimum_evidence_score": 0.65,
        "minimum_sources": 2,
        "minimum_domains": 2,
        "minimum_urls": 2,
        "preferred_source_types": ["peer-reviewed", "primary-source", "official-institution", "standard", "academic-publisher"],
        "strong_source_markers": ["peer-reviewed", "primary-source", "official-institution", "standard"],
        "require_strong_source": True,
        "scout_guidance": "Research the real-world constraint first, then state what it permits or challenges in worldbuilding. Never present fictional canon as evidence. Distinguish physically established constraints, engineering feasibility, speculative extension and narrative choice."
    },
    "philosophy-comparative": {
        "description": "Philosophical/theological comparison without pretending metaphysical theses are empirically verified.",
        "minimum_evidence_score": 0.65,
        "minimum_sources": 3,
        "minimum_domains": 2,
        "minimum_urls": 3,
        "preferred_source_types": ["primary-philosophical-text", "scholarly-edition", "peer-reviewed", "academic-reference", "academic-publisher"],
        "strong_source_markers": ["primary-philosophical-text", "scholarly-edition", "peer-reviewed", "academic-reference"],
        "require_strong_source": True,
        "scout_guidance": "Use primary philosophical/theological texts and serious scholarship. Separate textual/historical fact, scholarly interpretation, comparative analogy and KUEPER-system claim. Metaphysical propositions are not validated merely by source count; report them as philosophical positions unless they make independently testable empirical claims."
    }
}

registry = load_json(REGISTRY_PATH)
registry["updated_at"] = "2026-08-28"
avi = next(p for p in registry["projects"] if p["id"] == "avi-modell")
avi["notes"] = (
    "Vertiefung des kosmologischen Arbeitsmodells AVI (Axiomatisches Vakuum Integral). "
    "Scope: physikalisch/mathematische Untersuchung einer moeglichen Kopplung lokaler Raten/Zyklen an globale kosmologische bzw. informationelle Referenzparameter; "
    "Phi(a) wird als globaler, nicht-raeumlicher Arbeitsparameter bzw. integrierter Historienparameter behandelt. "
    "Fokus auf klar getrennte etablierte Grundlagen, Modellpostulate, Ableitungen und falsifizierbare Vorhersagen. "
    "AVI ist hier kein allgemeines Kreativ-, Text-, Musik- oder Weltbau-Modell. "
    "Ueberblick/Vertiefung-Verhaeltnis mit thomas-kueper.de bleibt konsistenzpflichtig. Code AVI; ECO-ARC-0011 ist inhaltlich an diesen korrigierten Scope anzupassen."
)
save_json(REGISTRY_PATH, registry)

policy = load_json(POLICY_PATH)
policy["schema_version"] = "1.2.0"
policy["evidence_profiles"] = profiles
mapping = {
    "noxia": ("technical-scientific", 1.0, ["de", "en"]),
    "noxia-universe": ("worldbuilding-scientific", 1.0, ["de", "en"]),
    "mishkenaz": ("historical-linguistic", 1.0, ["de", "en", "hi", "gu", "sa"]),
    "ota": ("science", 0.9, ["de", "en"]),
    "ssf": ("science", 0.8, ["de", "en"]),
    "avi-modell": ("avi-theoretical-cosmology", 0.85, ["de", "en"]),
    "omnizedenz": ("philosophy-comparative", 0.65, ["de", "en"]),
    "contracomology": ("philosophy-comparative", 0.65, ["de", "en"]),
    "kueper-com": ("general", 0.7, ["de", "en"]),
    "endia": ("worldbuilding-scientific", 0.7, ["de", "en"]),
    "zereya": ("worldbuilding-scientific", 0.7, ["de", "en"]),
}
policy["eligible_projects"] = [
    {"id": pid, "weight": weight, "languages": langs, "evidence_profile": profile}
    for pid, (profile, weight, langs) in mapping.items()
]
save_json(POLICY_PATH, policy)

# discover.py: make gap discovery profile-aware and persist profile in queue items.
text = DISCOVER_PATH.read_text(encoding="utf-8")
text = replace_once(
    text,
    'def prompt(project:dict[str,Any],langs:list[str])->str:\n    return f\'\'\'You are the knowledge-gap analyst for the KUEPER ecosystem. Inspect this repository deeply but DO NOT change it.\nRepository: {project[\'repository\']}\nProject role: {project.get(\'role\')}\nPotential research languages: {\', \'.join(langs)}\n',
    'def prompt(project:dict[str,Any],langs:list[str],profile_name:str,profile:dict[str,Any])->str:\n    profile_rules=json.dumps(profile,ensure_ascii=False)\n    return f\'\'\'You are the knowledge-gap analyst for the KUEPER ecosystem. Inspect this repository deeply but DO NOT change it.\nRepository: {project[\'repository\']}\nProject role: {project.get(\'role\')}\nPotential research languages: {\', \'.join(langs)}\nEvidence profile: {profile_name}\nEvidence profile rules: {profile_rules}\n',
    "discover prompt signature",
)
text = replace_once(
    text,
    '    eligible=POLICY["eligible_projects"];pmap=projects()\n    day=int(dt.datetime.now(dt.timezone.utc).strftime("%Y%j"));choice=eligible[day%len(eligible)];project=pmap[choice["id"]]\n',
    '    eligible=POLICY["eligible_projects"];pmap=projects()\n    day=int(dt.datetime.now(dt.timezone.utc).strftime("%Y%j"));choice=eligible[day%len(eligible)];project=pmap[choice["id"]]\n    profile_name=choice.get("evidence_profile","general");profile=POLICY.get("evidence_profiles",{}).get(profile_name,POLICY.get("evidence_profiles",{}).get("general",{}))\n',
    "discover profile resolution",
)
text = replace_once(
    text,
    '        run(cmd+[prompt(project,choice.get("languages",POLICY["default_languages"]))],cwd=root)\n',
    '        run(cmd+[prompt(project,choice.get("languages",POLICY["default_languages"]),profile_name,profile)],cwd=root)\n',
    "discover prompt call",
)
text = replace_once(
    text,
    '"languages":langs or POLICY["default_languages"],"relevance_score":score,',
    '"languages":langs or POLICY["default_languages"],"evidence_profile":profile_name,"relevance_score":score,',
    "queue evidence profile",
)
DISCOVER_PATH.write_text(text, encoding="utf-8")

# execute.py: resolve profile, pass it to synthesis, and enforce profile thresholds.
text = EXECUTE_PATH.read_text(encoding="utf-8")
text = replace_once(
    text,
    'def repo_info(token,repo):return gh(token,"GET",f"/repos/{repo}")\n\ndef queue(token)->list[tuple[dict[str,Any],dict[str,Any]]]:',
    'def repo_info(token,repo):return gh(token,"GET",f"/repos/{repo}")\n\ndef evidence_profile(item:dict[str,Any])->tuple[str,dict[str,Any]]:\n    name=item.get("evidence_profile")\n    if not name:\n        entry=next((p for p in POLICY.get("eligible_projects",[]) if p.get("id")==item.get("source_project")),{})\n        name=entry.get("evidence_profile","general")\n    profiles=POLICY.get("evidence_profiles",{})\n    return name,profiles.get(name,profiles.get("general",{}))\n\ndef queue(token)->list[tuple[dict[str,Any],dict[str,Any]]]:',
    "execute profile helper",
)
text = replace_once(
    text,
    'def research_prompt(item:dict[str,Any])->str:\n    langs=", ".join(item.get("languages") or POLICY["default_languages"])\n    return f\'\'\'You are the evidence research agent for the KUEPER ecosystem.\n\nResearch ID: {item[\'id\']}\nSource project: {item[\'source_project\']}\nQuestion: {item[\'question\']}\nWhy now: {item.get(\'why_now\',\'\')}\nRequested source languages: {langs}\n\nUse live web search. Research the question rigorously. Languages are discovery channels, NOT evidence rankings. Prefer primary sources, peer-reviewed work, official institutions, and academic publishers.',
    'def research_prompt(item:dict[str,Any])->str:\n    langs=", ".join(item.get("languages") or POLICY["default_languages"])\n    profile_name,profile=evidence_profile(item)\n    profile_rules=json.dumps(profile,ensure_ascii=False)\n    return f\'\'\'You are the evidence research agent for the KUEPER ecosystem.\n\nResearch ID: {item[\'id\']}\nSource project: {item[\'source_project\']}\nQuestion: {item[\'question\']}\nWhy now: {item.get(\'why_now\',\'\')}\nRequested source languages: {langs}\nEvidence profile: {profile_name}\nEvidence profile rules: {profile_rules}\n\nUse live web search. Research the question rigorously. Languages are discovery channels, NOT evidence rankings. Apply the evidence profile above before the general defaults. Prefer primary sources, peer-reviewed work, official institutions, and academic publishers.',
    "execute research prompt",
)
text = replace_once(
    text,
    '{{"evidence_score":0.0,"source_count":0,"distinct_domains":0,"languages_used":["en"],"uncertainty":"low|medium|high","candidate_filename":"{item[\'id\']}.md"}}',
    '{{"evidence_score":0.0,"source_count":0,"distinct_domains":0,"languages_used":["en"],"uncertainty":"low|medium|high","evidence_profile":"{profile_name}","candidate_filename":"{item[\'id\']}.md"}}',
    "execute result schema",
)
text = replace_once(
    text,
    'Metadata (Research ID, source project, status: candidate/non-canonical, researched date)\n',
    'Metadata (Research ID, source project, evidence profile, status: candidate/non-canonical, researched date)\n',
    "candidate metadata",
)
text = replace_once(
    text,
    'def validate_result(root:Path,item:dict[str,Any])->dict[str,Any]:\n    jf=root/".research-result.json";candidate=root/POLICY["candidate_path"]/f"{item[\'id\']}.md"\n    if not jf.exists() or not candidate.exists():raise RuntimeError("research agent did not create required result files")\n    meta=json.loads(jf.read_text(encoding="utf-8"));score=float(meta.get("evidence_score",0));src=int(meta.get("source_count",0));domains=int(meta.get("distinct_domains",0))\n    text=candidate.read_text(encoding="utf-8");urls=re.findall(r"https?://[^\\s)>]+",text)\n    if score<float(POLICY["minimum_evidence_score_for_candidate"]):raise RuntimeError(f"evidence score too low: {score}")\n    if src<2 or domains<2 or len(set(urls))<2:raise RuntimeError("candidate requires >=2 sources from >=2 domains with URLs")\n',
    'def validate_result(root:Path,item:dict[str,Any])->dict[str,Any]:\n    jf=root/".research-result.json";candidate=root/POLICY["candidate_path"]/f"{item[\'id\']}.md"\n    if not jf.exists() or not candidate.exists():raise RuntimeError("research agent did not create required result files")\n    profile_name,profile=evidence_profile(item)\n    meta=json.loads(jf.read_text(encoding="utf-8"));score=float(meta.get("evidence_score",0));src=int(meta.get("source_count",0));domains=int(meta.get("distinct_domains",0))\n    text=candidate.read_text(encoding="utf-8");urls=re.findall(r"https?://[^\\s)>]+",text)\n    min_score=float(profile.get("minimum_evidence_score",POLICY["minimum_evidence_score_for_candidate"]));min_sources=int(profile.get("minimum_sources",2));min_domains=int(profile.get("minimum_domains",2));min_urls=int(profile.get("minimum_urls",2))\n    if score<min_score:raise RuntimeError(f"evidence score too low for {profile_name}: {score} < {min_score}")\n    if src<min_sources or domains<min_domains or len(set(urls))<min_urls:raise RuntimeError(f"candidate for {profile_name} requires >={min_sources} sources, >={min_domains} domains and >={min_urls} URLs")\n    if profile.get("require_strong_source"):\n        markers=[str(x).lower() for x in profile.get("strong_source_markers",[])]\n        if markers and not any(marker in text.lower() for marker in markers):raise RuntimeError(f"candidate for {profile_name} lacks a strong source type marker")\n    if meta.get("evidence_profile") not in (None,profile_name):raise RuntimeError(f"agent reported mismatched evidence profile: {meta.get(\'evidence_profile\')} != {profile_name}")\n',
    "profile validation",
)
text = replace_once(
    text,
    '"body":f"Multilingual evidence candidate for `{item[\'source_project\']}`. Evidence score: `{meta.get(\'evidence_score\')}`.',
    '"body":f"Multilingual evidence candidate for `{item[\'source_project\']}` using evidence profile `{evidence_profile(item)[0]}`. Evidence score: `{meta.get(\'evidence_score\')}`.',
    "PR body profile",
)
EXECUTE_PATH.write_text(text, encoding="utf-8")

# Exa wrapper: apply the same profile before open-web search.
text = EXA_PATH.read_text(encoding="utf-8")
text = replace_once(
    text,
    'const evidencePolicy = policy.external_evidence ?? {};\n',
    'const evidencePolicy = policy.external_evidence ?? {};\nconst evidenceProfiles = policy.evidence_profiles ?? {};\n',
    "exa profiles constant",
)
text = replace_once(
    text,
    'function uniqueUrls(text) {\n  return [...new Set(text.match(/https?:\\/\\/[^\\s)>\\]"\']+/g) ?? [])];\n}\n',
    'function uniqueUrls(text) {\n  return [...new Set(text.match(/https?:\\/\\/[^\\s)>\\]"\']+/g) ?? [])];\n}\n\nfunction resolveProfile(sourceProject) {\n  const explicit = field(originalPrompt, \'Evidence profile\');\n  const project = (policy.eligible_projects ?? []).find((entry) => entry.id === sourceProject);\n  const name = explicit || project?.evidence_profile || \'general\';\n  return { name, config: evidenceProfiles[name] ?? evidenceProfiles.general ?? {} };\n}\n',
    "exa profile resolver",
)
text = replace_once(
    text,
    "  const requestedLanguages = field(originalPrompt, 'Requested source languages') || 'de, en';\n\n  const model =",
    "  const requestedLanguages = field(originalPrompt, 'Requested source languages') || 'de, en';\n  const { name: profileName, config: profile } = resolveProfile(sourceProject);\n\n  const model =",
    "exa profile resolution",
)
text = replace_once(
    text,
    '    process.env.KUEPER_EVIDENCE_NUM_RESULTS || evidencePolicy.num_results || 6,\n',
    '    process.env.KUEPER_EVIDENCE_NUM_RESULTS || profile.exa_num_results || evidencePolicy.num_results || 6,\n',
    "exa profile result count",
)
text = replace_once(
    text,
    '    process.env.KUEPER_EVIDENCE_MAX_STEPS || evidencePolicy.max_steps || 4,\n',
    '    process.env.KUEPER_EVIDENCE_MAX_STEPS || profile.exa_max_steps || evidencePolicy.max_steps || 4,\n',
    "exa profile max steps",
)
text = replace_once(
    text,
    '  const minimumUrls = Number(evidencePolicy.minimum_urls || 2);\n',
    '  const minimumUrls = Number(profile.minimum_urls || evidencePolicy.minimum_urls || 2);\n  const preferredSourceTypes = (profile.preferred_source_types ?? []).join(\', \');\n  const profileGuidance = profile.scout_guidance || \'Apply rigorous source criticism and preserve uncertainty.\';\n',
    "exa profile minima",
)
text = replace_once(
    text,
    'Requested discovery languages: ${requestedLanguages}\n\nUse the exa_search tool before answering.',
    'Requested discovery languages: ${requestedLanguages}\nEvidence profile: ${profileName}\nPreferred source types: ${preferredSourceTypes || \'not specified\'}\nProfile-specific guidance: ${profileGuidance}\n\nUse the exa_search tool before answering.',
    "exa prompt profile",
)
text = replace_once(
    text,
    "      'Use Exa search to ground the response in current external sources. Search first; synthesize second. Preserve uncertainty and source provenance.',",
    "      `Use Exa search to ground the response in current external sources. Search first; synthesize second. Apply evidence profile ${profileName}. Preserve uncertainty and source provenance.`,",
    "exa system profile",
)
text = replace_once(
    text,
    "        tags: ['kueper', 'external-evidence', 'exa', `project:${sourceProject}`],",
    "        tags: ['kueper', 'external-evidence', 'exa', `project:${sourceProject}`, `profile:${profileName}`],",
    "exa profile tag",
)
text = replace_once(
    text,
    "    model,\n    searchCalls: searchResults.length,",
    "    model,\n    profile: profileName,\n    searchCalls: searchResults.length,",
    "exa packet profile",
)
text = replace_once(
    text,
    "          model: packet.model,\n          searchCalls: packet.searchCalls,",
    "          model: packet.model,\n          profile: packet.profile,\n          searchCalls: packet.searchCalls,",
    "exa smoke profile",
)
text = replace_once(
    text,
    'Scout model: ${packet.model}\\nSearch calls: ${packet.searchCalls}',
    'Scout model: ${packet.model}\\nEvidence profile: ${packet.profile}\\nSearch calls: ${packet.searchCalls}',
    "exa augmented profile",
)
EXA_PATH.write_text(text, encoding="utf-8")

DOC_PATH.write_text("""# KUEPER Research Evidence Profiles

The research loop uses project-specific evidence profiles from `research/policy.json`. The profile is selected during knowledge-gap discovery, stored on the queue item, passed to the Exa external-evidence scout and re-applied by the synthesis/validation stage.

## Profiles

- `science` — OTA and SSF. Strong bias toward peer-reviewed literature, original datasets, collaboration publications and official institutions.
- `avi-theoretical-cosmology` — AVI (Axiomatisches Vakuum Integral). Separates established cosmology, model postulate, derived consequence, interpretation and falsifiable prediction; metaphysical analogy is never physical evidence.
- `technical-scientific` — NOXIA. Standards, original technical documentation, engineering literature and official data take precedence over vendor/community claims.
- `historical-linguistic` — Mishkenaz. Separates attestation, archaeological/linguistic reconstruction, comparative inference and fictional extrapolation; relevant source languages are discovery channels.
- `worldbuilding-scientific` — NOXIA Universe, ENDIA and Zereya. Researches real-world constraints first and keeps them distinct from canon and narrative choice.
- `philosophy-comparative` — Omnizedenz and Contracomology. Uses primary philosophical/theological texts and serious scholarship while distinguishing textual fact, scholarly interpretation, comparison and KUEPER-system claims. Source count does not turn a metaphysical position into an empirical finding.
- `general` — fallback/editorial profile for projects without a stronger domain-specific profile.

## Eligible rotation

The research rotation now includes `avi-modell`, `omnizedenz` and `contracomology` in addition to the previously eligible projects. Their weights are deliberately below the most active NOXIA/Mishkenaz streams, so adding them broadens coverage without letting them dominate the daily queue.

## Safety boundary

Exa remains discovery/retrieval only. The selected evidence profile controls source preference and minimum evidence gates; successful search results still enter the Knowledge Graph only as non-canonical research candidates. `auto_canonicalize` remains disabled.
""", encoding="utf-8")

# Structural sanity checks before the workflow commits anything.
policy = load_json(POLICY_PATH)
assert policy["auto_canonicalize"] is False
assert "avi-theoretical-cosmology" in policy["evidence_profiles"]
assert all(p.get("evidence_profile") in policy["evidence_profiles"] for p in policy["eligible_projects"])
registry = load_json(REGISTRY_PATH)
avi = next(p for p in registry["projects"] if p["id"] == "avi-modell")
assert "Axiomatisches Vakuum Integral" in avi["notes"]
print(json.dumps({"ok": True, "eligible_projects": len(policy["eligible_projects"]), "profiles": sorted(policy["evidence_profiles"].keys())}, indent=2))
