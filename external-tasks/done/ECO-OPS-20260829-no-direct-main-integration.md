# Ecosystem Ops: direkte Integration auf Default-Branches als Merge-Ersatz verhindern

**Origin:** KUEPER Arbeitsloop
**Target:** kueper-ecosystem
**Status:** done
**Created:** 2026-08-29
**Completed:** 2026-09-07
**Priority:** high

## Ergebnis

Der aktive Workerpfad V7.6 ist fail-closed gegen direkte Writes auf den jeweiligen Repository-Default-Branch gehärtet.

Umgesetzt wurde:

- lokaler Git-`pre-push`-Guard in jedem autonomen Worker-Clone;
- explizite Blockade von `HEAD:<default>` und `HEAD:refs/heads/<default>`;
- Coding-Agent erhält keine GitHub-Schreibcredentials (`KUEPER_BOT_TOKEN`, `KUEPER_WORKFLOW_TOKEN`, `GH_TOKEN`, `GITHUB_TOKEN`);
- vor der Agent-Ausführung wird `origin` auf die unauthentifizierte Repository-URL zurückgesetzt;
- Schreibcredential wird erst am kontrollierten Worker-Push auf einen PR-/Task-Branch wieder eingesetzt;
- REVIEW_FIX bleibt auf dem bestehenden PR-Head und kann einen fehlgeschlagenen Ready-/Merge-Schritt nicht durch einen Default-Branch-Write ersetzen;
- Agent-Regel verbietet Cherry-Pick, Nachbau oder direkte Integration als Merge-Ersatz;
- deterministische Tests laufen im Agent-Worker-Workflow zusammen mit den V7.5-/V7.6-Tests.

## Akzeptanz

- Default-Branch-Pushes werden vor Netzwerkmutation blockiert.
- `--no-verify` kann die Worker-Refspec-Prüfung nicht umgehen.
- PR-/Task-Branch-Pushes bleiben zulässig.
- Ein blockierter Ready-/Merge-Pfad bleibt blockiert; es gibt keinen Ersatzwrite auf `main`/`master`.
- Auto-Merge-Rechte wurden nicht erweitert.

Die bereits am 2026-08-29 integrierten KG-Identitäten werden nicht rückwirkend revertiert.
