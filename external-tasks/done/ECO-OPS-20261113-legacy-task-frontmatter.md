---
id: ECO-OPS-20261113-legacy-task-frontmatter
title: Elf Alt-Tasks ohne Frontmatter ins kanonische Format überführen oder begründet schließen
status: done
created: 2026-11-13
requested_by: T.P.K.
priority: low
estimated_effort: medium
type: operations / governance
parent_task: ECO-OPS-20261028-sweep-dedup
---

# ECO-OPS-20261113-legacy-task-frontmatter — Alt-Tasks ohne Frontmatter

**Origin:** abgetrennt aus ECO-OPS-20261028-sweep-dedup, Punkt 5 (Ökosystem-Kreislauf 13.11.2026)
**Target:** kueper-ecosystem
**Status:** done
**Created:** 2026-11-13

## Anlass

In `external-tasks/open/` liegen elf Tasks ohne YAML-Frontmatter. `tools/lint-external-tasks/lint.py` lehnt sie ab, und Auswahl nach Priorität ist für sie nicht möglich:

- EXT-ENG-ECO-20260924-robotics-program-routing.md
- EXT-ENG-ECO-20260925-energy-grid-learning-routing.md
- EXT-NOXIA-ECO-20260925-adaptive-industry-routing.md
- EXT-NOXIA-ECO-20260925-living-infrastructure-integration.md
- EXT-NOXIA-ECO-20260925-mycology-ecopoiesis-routing.md
- EXT-NOXIA-ECO-20260925-planetary-architecture-routing.md
- EXT-NOXIA-ECO-20260925-planetary-evolution-routing.md
- EXT-NOXIA-ECO-20260925-planetary-remote-sensing-routing.md
- EXT-NOXIA-ECO-20260927-mars-settlement-kernel-routing.md
- EXT-NXU-ECO-20260921-piazzi-lights-engineering-handoff.md
- EXT-OTA-ECO-20260911-utopia-mars-chronology-projection.md

## Gewünschte Änderung

Je Datei prüfen, ob der Bedarf noch besteht (Routing schon erfolgt? Ziel-Task schon vorhanden oder erledigt?). Noch gültige Tasks mit Frontmatter nach `docs/cross-repository-workflow.md` und ECO-ARC-0006 versehen; überholte mit kurzer Begründung nach `done/` oder `rejected/` verschieben.

## Begründung

Gehört zur Pflege der eigenen Inbox des Control Plane.

## Betroffene Repositories

- `kueper-ecosystem`

## Erwartetes Ergebnis

- Keine Datei in `external-tasks/open/` ohne Frontmatter.
- `tools/lint-external-tasks/lint.py` meldet für diese elf Dateien keine Frontmatter-Fehler mehr.

## Erledigt

13.11.2026, Ökosystem-Kreislauf (Claude), Branch `claude/ECO-OPS-20261113-legacy-task-frontmatter`.

## Umgesetzt

- Alle elf Dateien haben YAML-Frontmatter (`id`, `title`, `status`, `source`, `target`, `created`, `requested_by`, `affects`, `supersedes`) und die fünf Pflicht-Sektionen. Der ursprüngliche Auftragstext steht unverändert unter „Gewünschte Änderung“, Kopfangaben bleiben erhalten.
- Bedarf geprüft: Für keines der neun Programme (Robotics, Energy Grid, Adaptive Industry, Living Infrastructure, Mycology, Planetary Architecture/Evolution/Remote Sensing, Mars Settlement Kernel) gibt es im Ecosystem bisher eine Registrierung; Piazzi-Lights- und Utopia-Projektion sind ebenfalls nicht umgesetzt. Alle elf bleiben daher `open`; keine wurde geschlossen. Den Stand in Engineering, OTA und NOXIA Universe konnte dieser Lauf nicht einsehen (kein Zugriff).
- `tools/lint-external-tasks/lint.py`: keine Frontmatter-Pflichtfeld- und Sektionsfehler mehr. Es bleiben je Datei zwei Namensfehler (Dateiname und `id` nicht im Muster `…-NNN`) – wie schon bei `EXT-ENG-ECO-20261002-kueper-products-bootstrap.md`.
- Bewusst nicht umbenannt: `tools/loop/ingest_external_tasks.py` bildet den Idempotenzschlüssel aus der `id` (`external-task:<repo>:<id>`). Eine neue `id` würde im Task-Bus Dubletten der bereits eingespeisten Tasks erzeugen. Ob umbenannt oder das Muster im Linter für Alt-Tasks gelockert wird, gehört zur offenen Rückfrage in `external-tasks/parked/ECO-OPS-20261028-sweep-dedup.md` (Linter-Muster).
- `python3 -m pytest tools`: 149 bestanden, 1 übersprungen.
