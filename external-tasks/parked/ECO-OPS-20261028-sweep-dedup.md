---
id: ECO-OPS-20261028-sweep-dedup
title: Governance-Sweep – eine rollierende Task statt täglicher Duplikate
status: parked
created: 2026-10-28
requested_by: T.P.K.
priority: medium
estimated_effort: low
type: operations / governance
---

# ECO-OPS-20261028-sweep-dedup — Governance-Sweep: eine rollierende Task statt täglicher Duplikate

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** parked
**Created:** 2026-10-28
**Type:** operations / governance

## Anlass

In `external-tasks/open/` liegen 19 Dateien `EXT-ECO-ECO-YYYYMMDD-001.md` „Governance-Sweep – neue Funde“ (24.09.–12.10. und 24.10.). 18 davon melden jeweils denselben Einzelfund `task_addressed_to_eco`. Sie werden nicht bearbeitet und verdecken echte Aufgaben.

Außerdem verletzen sie ECO-ARC-0006: `source` und `target` dürfen nicht gleich sein (`tools/lint-external-tasks/lint.py` meldet genau das). Der Linter läuft in keinem Workflow.

Zusätzlich liegen 11 ältere Tasks ohne Frontmatter in `open/` (u. a. `EXT-NOXIA-ECO-20260925-*-routing`, `EXT-ENG-ECO-20260924-*`).

## Gewünschte Änderung

1. `tools/governance/sweep.py`: statt täglich eine neue Datei genau **eine** rollierende Datei pflegen (z. B. `external-tasks/open/ECO-OPS-governance-sweep.md`), die nur aktualisiert wird; wird sie leer, wandert sie nach `done/`.
2. Den Fund `task_addressed_to_eco` nicht als neue Task melden, wenn die betreffende Task schon offen ist.
3. Die 18 gleichlautenden Alt-Dateien nach `done/` verschieben (Vermerk „zusammengeführt in ECO-OPS-governance-sweep“), die vom 24.10. ebenso, sobald ECO-OPS-20261028-bot-token-401 erledigt ist.
4. Linter-Lauf über `external-tasks/` als Workflow bei Pull Requests; interne `ECO-OPS-*`-Dateien zulassen (Dateinamensmuster ergänzen, ECO-ARC-0006 entsprechend ergänzen).
5. Die 11 Alt-Tasks ohne Frontmatter ins kanonische Format überführen oder begründet schließen.

## Erwartetes Ergebnis

- `external-tasks/open/` enthält höchstens eine Sweep-Datei.
- Der Linter läuft bei jedem PR, alle offenen Tasks bestehen ihn.

## Stand 13.11.2026 (Ökosystem-Kreislauf, Claude)

Claude-Status: wartet auf Thomas

- Punkt 2 ist bereits erfüllt: `tools/governance/sweep.py` meldet Selbstbezug-Dateien (source = target = ECO) nicht mehr (`is_eco_addressed_task`) und eskaliert nur Funde, die im vorigen Bericht noch nicht standen. Seit 29.10.2026 ist keine neue Sweep-Datei entstanden.
- Punkt 3 erledigt: alle 20 Dateien `EXT-ECO-ECO-*-001.md` (24.09.–29.10.2026) nach `done/` verschoben, mit Vermerk.
- Punkt 5 als eigene Task abgetrennt: `external-tasks/open/ECO-OPS-20261113-legacy-task-frontmatter.md`.
- Punkte 1 und 4 nicht umgesetzt: Beide ändern `.github/workflows/` (die Datei-Erzeugung steckt im Workflow `governance-sweep.yml`, der Linter braucht einen neuen PR-Workflow). Änderungen an `.github/` bleiben nach `docs/autonomous-loops.md` reviewpflichtig.

## Rückfrage

Darf der Ökosystem-Kreislauf `.github/workflows/governance-sweep.yml` so ändern, dass er statt `EXT-ECO-ECO-<Datum>-001.md` nur noch die rollierende Datei `external-tasks/open/ECO-OPS-governance-sweep.md` pflegt, und einen neuen Workflow `external-tasks-lint.yml` (nur lesend, bei Pull Requests auf `external-tasks/**`) anlegen – mit `ECO-OPS-*` als zugelassenem Dateinamensmuster im Linter und einer Ergänzung zu ECO-ARC-0006? Antwort „ja“ genügt; dann kommt die Task zurück nach `open/`.
