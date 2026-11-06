---
id: EXT-KG-ECO-20261106-001
title: SCION-Wissenshandoff an KG-REQ-20261022 anschließen (GW250114, Positron, M31)
status: done
completed: 2026-11-06
source: KG
target: ECO
created: 2026-11-06
requested_by: T.P.K.
priority: medium
affects: [ECO, KG]
supersedes: []
---

# EXT-KG-ECO-20261106-001 – SCION-Wissenshandoff an KG-REQ-20261022 anschließen

## Anlass

KG-REQ-20261022 (Präzisionsphysik und historische Distanzmessung) verlangt, die SCION-Regressionsfälle an die vorhandenen Dateien `.github/workflows/scion-science-handoff-tests.yml` und `tools/loop/test_scion_science_handoff.py` anzuschließen – ausdrücklich ohne parallele Pipeline. Beide Dateien liegen in diesem Repository. Die KG-Seite ist in `kueper-knowledge-graph` PR #274 umgesetzt (kanonische IDs `EVT:L1:gw250114`, `PLC:AST:m31`, `CON:L1:*`, sieben Dokumentreferenzen).

Der Request nennt vier Testfälle. Der bestehende Pilot deckt zwei davon ab (eindeutige Beobachtungsidentität GW250114, historische M31-Distanz). Es fehlen **asymmetrische Evidenz** (Beobachtung vs. geplante Präzision) und **Existenz/Konsum der tatsächlichen KG-IDs**. Außerdem weicht der „aktuelle“ M31-Wert im Pilot (780 kpc, „modern calibration approximate“) vom Referenzwert in KUE-SCI-0198 und im KG ab (761 ± 11 kpc, Li u. a. 2021).

## Gewünschte Änderung

1. M31-Fixture auf den belegten Referenzwert `761 kpc` (Li u. a. 2021, HST NIR Cepheiden) umstellen.
2. Neuer Test `test_positron_capability_is_not_cpt_result`: Eine experimentelle Fähigkeit (PRL 137, 173001) und eine Zielgenauigkeit sind keine Messergebnisse; es gibt kein Ergebnis und keine „Verletzung“.
3. Neuer Test `test_consumed_kg_ids_exist`: liest – nur wenn `KG_ROOT` gesetzt ist – die aktive KXF-Registry des KG und prüft, dass die konsumierten IDs existieren und GW250114 genau eine ID hat. Ohne `KG_ROOT` wird er übersprungen; der Pilot bleibt offline.
4. Workflow: zusätzlicher Checkout von `kueper-knowledge-graph` nach `kg/` und `KG_ROOT` für den Testlauf.

Umsetzung liegt als PR auf Branch `claude/scion-kg-precision-physics` vor.

## Reihenfolge

**Erst KG PR #274 mergen, dann diesen PR.** Gegen den heutigen KG-`main` schlägt `test_consumed_kg_ids_exist` erwartungsgemäß fehl, weil die IDs dort noch fehlen; gegen den Stand von PR #274 laufen alle sechs Tests grün (lokal geprüft 2026-11-06).

## Begründung

So prüft SCION nicht nur Beispieldaten, sondern auch, dass die IDs, die SSF und NOXIA konsumieren sollen, im KG tatsächlich existieren – ohne dass der Pilot selbst Repositories anspricht oder kanonische Inhalte verändert.

## Betroffene Repositories

- `kueper-ecosystem` (Tests, Workflow)
- `kueper-knowledge-graph` (nur lesend; PR #274 als Voraussetzung)

## Abschluss (2026-11-06)

Umgesetzt in PR #129 nach dem Merge von kueper-knowledge-graph PR #274. Der Workflow checkt das private KG-Repo mit `secrets.KUEPER_BOT_TOKEN` aus (wie `ota-tech-object-audit.yml`). CI-Lauf gegen KG-`main`: alle sechs Tests grün, `test_consumed_kg_ids_exist` nicht übersprungen.
