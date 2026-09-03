# External-Check Merge Gate (fail-closed)

Status: implementation contract  
Date: 2026-08-31  
Control Plane: `kueper-ecosystem`

## Anlass

NOXIA PR #42 (`thomaspeterkueper/noxiagame#42`) wurde am 31.08.2026 über den automatisierten Review-/Merge-Pfad gemergt, obwohl der Supabase Preview Branch zu diesem Zeitpunkt einen fehlgeschlagenen Migrationslauf meldete:

```text
ERROR: function uuid_generate_v4() does not exist (SQLSTATE 42883)
At statement: 21
CREATE TABLE IF NOT EXISTS locations (...)
```

Vercel war grün, der Supabase-Migrationscheck rot. Der zentrale Loop (`tools/loop/orchestrate.py`) hatte bis dahin nach PR-Erzeugung ohne Auswertung externer Checks `gh pr merge --auto` aktiviert; GitHub-Auto-Merge allein wertet nur die dort konfigurierten Required Checks aus. Der fachliche Review-Pfad allein ist kein ausreichendes Merge-Gate für externe CI-/DB-Checks.

## Vertrag

Vor einem automatischen Merge prüft der zentrale Loop **fail-closed**, ob alle für das Ziel-Repository relevanten externen Checks erfolgreich sind. Maßgeblich ist ausschließlich die deklarative Policy des Ziel-Repositories in `registry/projects.json`:

```json
"merge_gate": {
  "mode": "fail-closed",
  "required": [
    "vercel",
    "supabase-preview",
    "supabase-migrations"
  ]
}
```

Kanonische Struktur: `schemas/project-registry.schema.json` (`merge_gate`, `mergeGateCheck`). Die zentrale Automation hart kodiert keine Checks global; jedes Repository deklariert seine eigenen.

### Bekannte Check-Arten

| id | Quelle | Match |
|---|---|---|
| `vercel` | Check-Run (Name) **oder** Commit-Status (Context), enthält `vercel` | `success` |
| `supabase-preview` | Check-Run der Supabase-GitHub-App, Name enthält `preview branch` | `success` |
| `supabase-migrations` | Check-Run der Supabase-GitHub-App, Name enthält `migrations` | `success` |

Benutzerdefinierte Checks können als Objekt deklariert werden:

```json
{ "id": "ci", "source": "check-run", "name": "build", "match": "exact", "app_slug": "github-actions" }
```

`source`: `check-run` | `status` | `any`. `match`: `contains` | `exact` | `prefix`.

## Fail-closed-Semantik

Ein grünes Urteil wird nie aus fehlenden Daten abgeleitet:

1. Keine `merge_gate`-Policy deklariert → **kein Auto-Merge** (Mode `missing`). `mode: "off"` ist der explizite, dokumentierte Owner-Opt-out ohne Checks.
2. Ungültige Policy oder unbekannte erforderliche Check-ID → **kein Merge**.
3. Erforderlicher Check ohne Ergebnis für den **aktuellen** PR-Head-SHA → **kein Merge** (`missing`). Ergebnisse älterer Heads zählen nie als Freigabe.
4. `failure`/`error`/`cancelled`/`timed_out`/`neutral`/`skipped`/`stale` sowie ein abgeschlossener Run ohne `success`-Conclusion → **kein Merge** (`failed`). Mehrere Ergebnisse desselben Checks sind nur grün, wenn alle `success` sind.
5. Nicht abgeschlossene Ergebnisse (`queued`/`in_progress`/`pending`) → **kein Merge** (`incomplete`).
6. Unvollständig abrufbare Check-Evidenz (abgeschnittene API-Seiten) → **kein Merge** (`truncated`).
7. Fehler bei der Evidenzbeschaffung → **kein Merge**; der Blocker wird im Loop-Report sichtbar.
8. Review-Pflichten bleiben unverändert vorgelagert: PRs mit reviewpflichtigen Dateien (`requires_review`) erreichen den Merge-Pfad nicht.

Ein Merge darf erst nach erfolgreichem automatischem Review **und** erfolgreicher CI-/Deployment-Gate-Auswertung erfolgen.

## Implementierung

- `tools/loop/merge_gate.py`: Policy-Normalisierung, deterministische `evaluate()`-Funktion, Evidenzbeschaffung (Check-Runs + Combined Status für exakt einen Head-SHA), End-to-End-`gate_decision()`.
- `tools/loop/orchestrate.py`: `queue_auto_merge()` ruft `gh pr merge --auto --squash --delete-branch` nur auf, wenn `gate["allowed"]` gilt. Gilt für neu erzeugte PRs **und** für den Wiederbesuch bereits offener PRs (dort wird auch geprüft, ob Auto-Merge bereits aktiv ist). Nicht auflösbare PR-Dateilisten gelten als reviewpflichtig.
- `registry/projects.json`: NOXIA deklariert `vercel`, `supabase-preview`, `supabase-migrations` als `fail-closed`.
- Deterministische Regressionstests: `tools/loop/test_merge_gate.py`.

## Regressionstests

Abgedeckt durch `tools/loop/test_merge_gate.py`:

- PR review-approved/mergeable, Vercel grün, Supabase `Migrations` fehlgeschlagen → **kein Merge**;
- erforderlicher Check fehlt → **kein Merge**;
- Check gehört zu altem Head → **kein Merge**;
- alle erforderlichen Checks auf aktuellem Head grün → Merge darf entsprechend bestehender Governance fortfahren;
- zusätzlich: incomplete/neutral/widersprüchliche Ergebnisse, unbekannte IDs, fehlende/ungültige Policy, abgeschnittene Evidenz, Verkabelung der Merge-Invokation hinter dem Gate.

## Abgrenzung

- Keine Erweiterung von Auto-Merge-Rechten (siehe ECO-OPS-20260829-no-direct-main-integration).
- Research-Candidate-Merge-Gate (`RESEARCH_CANDIDATE_MERGE_GATE.md`) bleibt ein separater Vertrag.
- Der Automated PR Review Agent (V7.3) besitzt weiterhin keine Merge-Befugnis.
