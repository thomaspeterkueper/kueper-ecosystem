---
id: NOXIA-ECO-20260831-merge-gate-required-checks
source: SYS:KUEPER:noxia
target: SYS:KUEPER:ecosystem
priority: critical
type: automation-governance
created: 2026-08-31
status: done
resolved: 2026-08-31
affects: [NOXIA, KUEPER-Ecosystem]
---

# Fail-closed Merge-Gate für externe CI-/DB-Checks

## Anlass

NOXIA PR #42 (`thomaspeterkueper/noxiagame#42`) wurde am 31.08.2026 durch den automatisierten Review-/Merge-Pfad gemergt, obwohl der Supabase Preview Branch zu diesem Zeitpunkt einen fehlgeschlagenen Migrationslauf meldete.

Beobachteter Fehler vor Merge:

```text
ERROR: function uuid_generate_v4() does not exist (SQLSTATE 42883)
At statement: 21
CREATE TABLE IF NOT EXISTS locations (...)
```

Vercel war grün, der Supabase-Migrationscheck jedoch rot. Der Code-Review-Pfad hatte zuvor bereits Findings bearbeitet; der fachliche Review allein reicht deshalb nicht als Merge-Gate.

## Anforderung

Der zentrale KUEPER PR-Review-/Merge-Regelkreis muss vor einem automatischen Merge **fail-closed** prüfen, ob alle für das Ziel-Repository relevanten externen Checks erfolgreich sind.

Für NOXIA mindestens:

1. Vercel Deployment/Build erfolgreich.
2. Supabase Preview Branch ohne Branch Error.
3. Supabase `Migrations` erfolgreich; ein explizites `❌`, failure/error oder nicht abgeschlossenes erforderliches Ergebnis blockiert Merge.
4. Der geprüfte Check muss zum aktuellen PR-Head gehören; Ergebnisse älterer Heads dürfen nicht als Freigabe gelten.
5. Fehlende oder nicht eindeutig auswertbare erforderliche Checks dürfen nicht als grün interpretiert werden.
6. Ein Merge darf erst nach erfolgreichem automatischem Review **und** erfolgreicher CI-/Deployment-Gate-Auswertung erfolgen.

## Repository-spezifische Policy

Die zentrale Automation sollte erforderliche Checks nicht global hart codieren, sondern pro registriertem Repository deklarativ konfigurieren können, z. B. in Registry/Policy-Metadaten.

Beispiel für NOXIA:

```yaml
merge_gate:
  mode: fail-closed
  required:
    - vercel
    - supabase-preview
    - supabase-migrations
```

Die konkrete kanonische Struktur liegt im Zuständigkeitsbereich des KUEPER-Ecosystem-Repositories.

## Regressionstest

Ein deterministischer Test muss mindestens diesen Fall abdecken:

- PR ist review-approved/mergeable.
- Vercel ist erfolgreich.
- Supabase `Migrations` ist fehlgeschlagen.
- Erwartung: **kein Merge**, Status bleibt blocked/pending-fix.

Zusätzlich:

- erforderlicher Check fehlt -> kein Merge;
- Check gehört zu altem Head -> kein Merge;
- alle erforderlichen Checks aktueller Head grün -> Merge darf entsprechend bestehender Governance fortfahren.

## Abgrenzung

NOXIA definiert hier nur die beobachtete Anforderung an den zentralen Automationsdienst. Implementierung, Registry-Schema und globale Merge-Governance bleiben Source of Truth des KUEPER-Ecosystem-Repositories.

## Umsetzung (2026-08-31)

Umgesetzt im KUEPER-Ecosystem-Repository:

- `schemas/project-registry.schema.json`: kanonische `merge_gate`-Policy-Struktur (`mode` + `required`, bekannte Check-Arten `vercel`/`supabase-preview`/`supabase-migrations`, benutzerdefinierte Check-Deskriptoren).
- `registry/projects.json`: NOXIA deklariert `merge_gate` mit `mode: fail-closed` und `required: [vercel, supabase-preview, supabase-migrations]`.
- `tools/loop/merge_gate.py`: fail-closed-Evaluator (Head-SHA-Bindung, missing/failed/incomplete/unknown/truncated blockieren; kein grünes Urteil aus fehlenden Daten).
- `tools/loop/orchestrate.py`: `gh pr merge --auto` wird nur noch nach bestandener Gate-Auswertung aktiviert — für neu erzeugte und wiederbesuchte offene PRs.
- `tools/loop/test_merge_gate.py`: deterministische Regressionstests inkl. des beobachteten Falls (Vercel grün, Supabase-Migrations rot → kein Merge).
- Vertrag: `docs/architecture/EXTERNAL_CHECK_MERGE_GATE.md`; Loop-Doku: `docs/autonomous-loops.md`.

