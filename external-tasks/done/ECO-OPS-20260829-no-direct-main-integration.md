# Ecosystem Ops: direkte Integration auf Default-Branches als Merge-Ersatz verhindern

**Origin:** KUEPER Arbeitsloop
**Target:** kueper-ecosystem
**Status:** done
**Created:** 2026-08-29
**Completed on branch:** 2026-08-29
**Priority:** high

## Anlass

Im Knowledge-Graph-Repository wurde PR #38 nicht normal gemergt, sondern sein Inhalt nach einem Connector-/GraphQL-Problem direkt auf `main` integriert. Diese Form eines Merge-Ersatzes ist für die KUEPER-Automation nicht zulässig.

## Implementierte Absicherung

- `tools/worker/default_branch_guard.py` führt eine zentrale Fail-closed-Prüfung für Publikationspfade ein.
- `agent_worker_v72.py` prüft sowohl vor Branch-Erzeugung als auch unmittelbar vor dem Push, dass das Publikationsziel nicht der Default-Branch ist.
- Der Agenten-Prompt verbietet ausdrücklich Commit/Push/Cherry-Pick/Rekonstruktion/Contents-API-Write auf den Default-Branch als Ersatz für PR, Ready, Review oder Merge.
- Bei technisch nicht verfügbarem PR-Lifecycle muss der PR/Head-Branch erhalten bleiben und der Blocker sichtbar gemacht werden.
- `test_default_branch_guard.py` deckt insbesondere den Fall `draft/open PR + Ready/Merge unavailable => no default-branch mutation` deterministisch ab.
- Die bereits direkt integrierten KG-Inhalte werden nicht automatisch revertiert.

## Akzeptanz

Erfüllt auf Implementierungsbranch `automation/no-direct-main-integration`. Die Änderung wird über einen normalen PR zur Prüfung bereitgestellt; kein autonomer Merge.
