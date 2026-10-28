---
id: ECO-OPS-20261028-sweep-dedup
title: Governance-Sweep – eine rollierende Task statt täglicher Duplikate
status: open
created: 2026-10-28
requested_by: T.P.K.
priority: medium
estimated_effort: low
type: operations / governance
---

# ECO-OPS-20261028-sweep-dedup — Governance-Sweep: eine rollierende Task statt täglicher Duplikate

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** open
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
