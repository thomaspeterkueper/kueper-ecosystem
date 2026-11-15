---
id: EXT-ENG-ECO-20260925-energy-grid-learning-routing
title: Energy-grid / learning-module routing
status: done
source: ENG
target: ECO
created: 2026-09-25
requested_by: NOXIA cross-project
affects: [ECO, ENG, OTA, KG, NXU, NOXIA]
supersedes: []
---

# EXT-ENG-ECO-20260925-energy-grid-learning-routing – Energy-grid / learning-module routing

- **Origin:** NOXIA cross-project
- **Target:** KUEPER Ecosystem
- **Date:** 2026-09-25
- **Status:** done

## Anlass

Alt-Task ohne kanonisches Format, eingegangen am 2026-09-25 (Herkunft: NOXIA cross-project). Am 13.11.2026 ins Format nach `docs/cross-repository-workflow.md` und ECO-ARC-0006 überführt (ECO-OPS-20261113-legacy-task-frontmatter); der ursprüngliche Auftragstext steht unverändert unter „Gewünschte Änderung“. Die `id` entspricht bewusst dem bisherigen Dateinamen, damit der Idempotenzschlüssel im Task-Bus gleich bleibt.

## Gewünschte Änderung

Register the Energy Grid Layer and associated learning module as a cross-project program.

Responsibility:
- Engineering: physical/system architecture and simulation contracts.
- OTA: evidence/provenance/current real-world grid research.
- KG: canonical energy and learning concepts/relations.
- noxia-universe: historical/worldbuilding consequences.
- noxiagame: gameplay, UX, balancing and learning scenarios.
- noxia-realtime: later visualization/runtime adoption after contracts stabilize.

Cross-link this program to robotics/MiniNodes, buildings, industry, resource extraction, settlements and transport. Preserve federated ownership and route changes by external tasks.

## Begründung

Querschnittsprogramm über mehrere Repositories. Registrierung und Zuständigkeitsverteilung sind Governance-Aufgabe von `kueper-ecosystem`; jedes Repository behält nur seine eigene Domäne, Änderungen anderswo laufen als External Tasks.

## Betroffene Repositories

- `kueper-ecosystem`
- `kueper-engineering`
- `overtime-archive.org`
- `kueper-knowledge-graph`
- `noxia-universe`
- `noxiagame`
- `noxia-realtime` (erst nach stabilen Verträgen)

## Erwartetes Ergebnis

- Programm in `kueper-ecosystem` registriert, Zuständigkeiten wie unter „Gewünschte Änderung“ festgehalten.
- Querverweise zu den genannten Nachbarprogrammen dokumentiert.
- Folgearbeiten in den Ziel-Repositories als External Tasks geroutet.

## Erledigt

Status: done – Ökosystem-Kreislauf (Claude), 15.11.2026.

## Umgesetzt

- Programm registriert: `docs/programs/energy-grid.md` mit Zweck, Geltungsbereich, Zuständigkeiten (ENG, OTA, KG, NXU, NOXIA, Lernpfad SSF; `noxia-realtime` zurückgestellt) und Regeln.
- Querverweise zu Robotik/MiniNode, Adaptive Industry, Gebäuden/Siedlungen (Mars Settlement Kernel, Living Infrastructure), Bergbau/Ressourcen und Transport/Logistik.
- Folgearbeiten: bereits ab 25.09.2026 geroutet (ENG `ENG-SYS-EGCA-0001`, KG `exports/ontology-energy-grid-learning-0.1.json` und OTA `OTA-SCI-0109-2026-DE` erledigt; NXU-Entwicklung und -Integration, NOXIA-Lernmodul und SSF-Lernpfad offen) und als Stand zusammengeführt; keine doppelten Aufträge erzeugt.
- Register `docs/programs/README.md` und `docs/system-map.md` ergänzt; Verweise in `adaptive-industry.md`, `living-infrastructure.md`, `mars-settlement-kernel.md` und `robotics-mininode.md` auf die Registrierung umgestellt.
