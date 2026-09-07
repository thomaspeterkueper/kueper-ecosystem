---
id: NOXIA-ECO-20260831-merge-gate-required-checks
source: SYS:KUEPER:noxia
target: SYS:KUEPER:ecosystem
priority: critical
type: automation-governance
created: 2026-08-31
completed: 2026-09-07
status: done
affects: [NOXIA, KUEPER-Ecosystem]
---

# Fail-closed Merge-Gate für externe CI-/DB-Checks

## Anlass

NOXIA PR #42 wurde am 31.08.2026 bei grünem Vercel-Status gemergt, obwohl der zum selben PR-Head gehörende GitHub Check Run `Supabase Preview` mit `failure` abgeschlossen war. Die Fehlermeldung betraf `uuid_generate_v4()` während der Preview-Migration.

## Umgesetzte Regel

Der aktive zentrale Reviewer V0.8 wertet nun vor jeder semantischen Review-/Completion-Stufe eine deklarative Repository-Policy aus `registry/merge-gates.json` aus.

Für `thomaspeterkueper/noxiagame` gilt `fail-closed` mit folgenden logischen Pflichtgates:

1. `vercel` — Commit-Status `Vercel` muss `success` sein.
2. `supabase-preview` — Check Run `Supabase Preview` muss zum aktuellen PR-Head gehören, `completed` sein und `success` liefern.
3. `supabase-migrations` — nutzt denselben autoritativen Supabase-Preview-Run; ein Migration-/Branch-Fehler führt zu einer nicht erfolgreichen Conclusion und blockiert damit ebenfalls.

Fehlende, mehrdeutige, nicht abgeschlossene, alte oder nicht erfolgreiche Pflichtchecks blockieren. `neutral` und `skipped` gelten für Pflichtchecks ausdrücklich nicht als Erfolg.

## Lifecycle

Die Prüfung passiert vor Provider-/LLM-Budget-Reservierung. Ein geblockter PR bleibt im Review-Lifecycle und erhält das Ergebnis `ci-gate-blocked`; es wird weder ein semantischer PASS erzeugt noch ein Reviewslot verbraucht. Sobald die erforderlichen Checks auf einem aktuellen Head vollständig grün sind, darf die bestehende Review-Governance fortfahren.

Der heutige Reviewer führt selbst keinen Merge aus (`No auto-merge performed`). Deshalb sitzt das Gate bewusst vor der serverseitigen Reviewed-Completion; ein nachgelagerter vertrauenswürdiger Merge-Reconciler darf nur auf diesen gegateten Lifecycle aufsetzen.

## Regressionstests

`tools/review/test_merge_gate.py` deckt deterministisch ab:

- Vercel grün + Supabase Preview/Migration rot => blockiert.
- erforderlicher Check fehlt => blockiert.
- Check gehört zu altem Head => blockiert.
- erforderlicher Check ist noch nicht abgeschlossen => blockiert.
- Vercel rot => blockiert.
- Statuspayload gehört zu altem Head => blockiert.
- alle Pflichtchecks des aktuellen Heads explizit erfolgreich => Review darf fortfahren.

Die Tests sind in `.github/workflows/pr-review-agent.yml` aufgenommen.
