# Ecosystem Ops: direkte Integration auf Default-Branches als Merge-Ersatz verhindern

**Origin:** KUEPER Arbeitsloop
**Target:** kueper-ecosystem
**Status:** done
**Created:** 2026-08-29
**Resolved:** 2026-08-29
**Priority:** high
**Type:** operations / governance enforcement

## Anlass

Im Knowledge-Graph-Repository wurde PR #38 (`[integrated] canonical NOXIA unlock learning-module identities`) am 2026-08-29 nicht normal gemergt. Wegen eines Connector-/GraphQL-Problems beim Umschalten des Draft-PRs auf Ready wurde der fachlich geprüfte Inhalt stattdessen als Commit `81aad150ac7b2180b00e73daa90b57a523d9490e` direkt auf `main` integriert und der Draft-PR anschließend geschlossen. Das ist funktional ein Merge-Ersatz und verletzt die verbindliche Betriebsgrenze.

## Implementierte Absicherung

- **Governance:** `decisions/ECO-ARC-0031-2026-DE.md` legt die fail-closed-Betriebsgrenze systemweit fest: kein Cherry-Pick, kein Nachbauen, kein Contents-API-/Git-Write auf den Default-Branch als Ersatz für PR, Ready, Review oder Merge; der PR bleibt bei blockiertem Ready/Merge offen/draft und der Blocker wird als review-/merge-blocked sichtbar gehalten. Keine Erweiterung von Auto-Merge-Rechten.
- **Dreistufiger Guard** in `tools/worker/default_branch_guard.py`:
  - *Entscheidungs-Guard:* Der Worker verweigert jeden Publikationspfad, dessen Ziel der Default-Branch ist — vor Branch-Erzeugung und unmittelbar vor jedem Push.
  - *Sandbox-Guard:* Ein pre-push-Hook im Agenten-Klon lehnt Git-Pushes auf den Default-Branch ab (Ende-zu-Ende gegen ein lokales Git-Repo verifiziert).
  - *Verifikations-Guard:* Nach jedem Agentenlauf wird der Remote-Default-Branch mit dem Ausgangs-SHA verglichen; eine Abweichung parkt den Task als Governance-Verstoß mit Owner-Entscheid, eine nicht durchführbare Prüfung parkt fail-closed.
- **Worker-Pfad:** `agent_worker_v72.py` (Clone → Hook → Verifikation → Push) und der REVIEW_FIX-Pfad in `agent_worker_v73.py` (verweigert einen Push, wenn der PR-Head seiner Base entspricht; Hook und Verifikation ebenfalls aktiv) setzen den Guard durch. Die Agenten-Prompts aller Worker-Versionen verbieten Default-Branch-Writes als Merge-Ersatz ausdrücklich.
- **Test:** `tools/worker/test_default_branch_guard.py` deckt deterministisch den Fall `draft/open PR + Ready/Merge unavailable ⇒ no default-branch content mutation` ab, einschließlich Hook-Installation und Remote-Verifikation (Mutation erkannt, unprüfbar = fail-closed). 14 Tests, alle grün.
- **Dokumentation:** `docs/architecture/PR_TASK_REVIEW_LIFECYCLE_V73.md` (Auto-Merge-Grenze) und `docs/agent-worker-v7.md` (Default-Branch-Write-Guard) beschreiben das neue Verhalten.
- **Kein automatischer Revert:** Die bereits integrierten KG-Identitäten bleiben unangetastet.

## Akzeptanz

- Agent/Worker kann einen offenen/draft PR bei API-/Connector-Fehler nicht durch direkte Default-Branch-Integration ersetzen — erfüllt durch Entscheidungs-, Sandbox- und Verifikations-Guard.
- Ein deterministischer Test deckt den Fall ab — `test_draft_pr_ready_unavailable_cannot_fall_back_to_main` u. a.
- Der Blocker wird als review-/merge-blocked sichtbar gehalten — PR bleibt unverändert; Verstöße werden als `requires_owner_decision` geparkt.
- Keine Erweiterung von Auto-Merge-Rechten — kein Merge-Pfad wurde hinzugefügt.

## Offene Folgeaufgabe

- KG-seitige Branch-Protection auf `main` und Härtung des lokalen Agentenpfads (separater External Task, geroutet über `.kueper/outbox/`).
- Aufnahme des Guard-Tests in den Test-Schritt von `agent-worker-v7.yml` (privilegierte Workflow-Änderung mit `KUEPER_WORKFLOW_TOKEN`).
