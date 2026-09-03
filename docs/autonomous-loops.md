# Autonome Loops im KUEPER Ecosystem

Status: V2  
Control Plane: `kueper-ecosystem`

## Ziel

Das Ecosystem wartet nicht darauf, dass der Owner jedes Projekt manuell auffordert. Offene External Tasks werden regelmäßig entdeckt, im aktuellen Ziel-Repository neu bewertet und autonom bearbeitet. Erkennt ein Projekt dabei einen konkreten Bedarf in einem anderen Projekt, kann es diesen als strukturierten Folge-Request an das Ecosystem übergeben.

## V2-Kreislauf

```text
PROJECT WORK
  lokaler Task wird bearbeitet
    ↓
DISCOVER
  konkreter Bedarf außerhalb der eigenen Source of Truth?
    ↓ nein                         ↓ ja
  lokal fertig              .kueper/outbox/*.json
                                  ↓
ROUTE
  Zielcode + Registry + Tiefe + Duplikat prüfen
                                  ↓
  kanonischen External Task in Ziel-Inbox erzeugen
                                  ↓
OBSERVE → SELECT → PREFLIGHT → RESCAN/REPLAN → ACT → VERIFY
                                  ↓
RESULT → PR → MERGE GATE → NEXT SWEEP
```

## Merge Gate (fail-closed)

Vor einem automatischen Merge wertet der zentrale Loop (`tools/loop/orchestrate.py` → `tools/loop/merge_gate.py`) die externen CI-/Deployment-Checks des Ziel-Repositories **fail-closed** aus:

- Maßgeblich ist die deklarative `merge_gate`-Policy des Ziel-Repositories in `registry/projects.json` (kanonische Struktur: `schemas/project-registry.schema.json`).
- Jeder erforderliche Check muss ein abgeschlossenes, erfolgreiches Ergebnis für den **aktuellen** PR-Head-SHA haben; Ergebnisse älterer Heads zählen nie.
- Fehlende, fehlgeschlagene, nicht abgeschlossene, widersprüchliche oder nicht auswertbare erforderliche Checks blockieren den Merge; ein grünes Urteil wird nie aus fehlenden Daten abgeleitet.
- Keine deklarierte Policy → kein Auto-Merge; `mode: "off"` ist der explizite Owner-Opt-out.
- Reviewpflichtige PRs (siehe Regel 6 der Verantwortungsgrenzen) erreichen den Merge-Pfad nicht.

Details und Regressionstests: `docs/architecture/EXTERNAL_CHECK_MERGE_GATE.md`, `tools/loop/test_merge_gate.py`.

## Verantwortungsgrenzen

1. `kueper-ecosystem` orchestriert, ist aber nicht fachliche Source of Truth.
2. Ein Projekt darf nur seine eigenen fachlichen Entscheidungen und Dateien ändern.
3. Cross-Repo-Bedarf wird als Request formuliert, niemals durch einen Fremd-Commit erzwungen.
4. Vor der Bearbeitung wird der Default-Branch-HEAD erneut geprüft; bei Bewegung wird neu geplant.
5. Unklare oder widersprüchliche Tasks werden geparkt und erhalten eine konkrete `## Rückfrage`.
6. Änderungen an `.github/`, Migrationen, Auth/Security, Infrastruktur, Lockfiles und Deployment-Konfiguration bleiben reviewpflichtig.

## Follow-up Envelope

Ein Projekt darf unter `.kueper/outbox/` JSON-Dateien erzeugen. Pflichtfelder:

```json
{
  "target": "KG",
  "title": "Kurzer konkreter Titel",
  "reason": "Warum der Bedarf bei der aktuellen Arbeit entstanden ist.",
  "requested_change": "Was das Zielprojekt prüfen oder umsetzen soll.",
  "expected_result": "Woran Erledigung erkennbar ist.",
  "priority": "medium",
  "parent_task": "EXT-...",
  "depth": 2
}
```

`target` ist ein registrierter System-Code. Source und Target dürfen nicht identisch sein.

## Rekursions- und Sturmbegrenzung

V2 begrenzt autonome Ketten absichtlich:

- maximal drei Follow-ups, die ein einzelner Project-Agent sinnvoll erzeugen soll;
- maximale Routing-Tiefe standardmäßig `3`;
- maximal zehn neu geroutete Requests pro Sweep;
- Fingerprint-Deduplizierung gegen `open`, `parked` und `done` im Ziel-Repository;
- keine spekulativen, bloß wünschenswerten oder selbstgerichteten Requests;
- ein Follow-up wird erst im nächsten Sweep bearbeitet. Dadurch gibt es keine ungebremste Rekursion innerhalb eines Agentenlaufs.

Konfiguration: `KUEPER_MAX_FOLLOWUP_DEPTH` und `KUEPER_MAX_FOLLOWUPS`.

## Routing

`tools/loop/route_followups.py` liest die Outboxes aller aktivierten Registry-Projekte. Ein gültiger Envelope wird in das kanonische Format `EXT-{SOURCE}-{TARGET}-{YYYYMMDD}-{NNN}` übersetzt und direkt in `external-tasks/open/` des fachlich zuständigen Ziel-Repositories geschrieben.

Jeder geroutete Task enthält zusätzlich:

- `routing_fingerprint`
- `parent_task`
- `routing_depth`

Damit bleibt die Herkunft einer autonomen Task-Kette nachvollziehbar.

## Takt

Der zentrale Sweep läuft stündlich. Reihenfolge V2:

1. vorhandene Outboxes routen;
2. offene External Tasks scannen;
3. priorisierte Tasks bearbeiten;
4. entstandene Follow-ups liegen im jeweiligen PR und werden nach dessen Merge beim nächsten Sweep geroutet.

## Noch nicht Teil von V2

V2 erzeugt neue Requests nur aus **konkreter Projektarbeit**. Es startet noch keine freie, selbstzweckhafte Ideen- oder Research-Expansion. Das ist bewusst getrennt, damit das Ecosystem zunächst beweist, dass autonome Task-Ketten stabil, relevant und begrenzt bleiben.

Nächste Stufen:

1. Knowledge-Expansion mit eigenem Relevanzbudget;
2. multilingualer Research-Loop mit Evidenzbewertung;
3. Canon-Conflict-Loop Realwissen ↔ Worldbuilding ↔ Manuskript/Spiel;
4. Kosten-/Token-/Zeitbudgets und systemweite Priorisierung.
