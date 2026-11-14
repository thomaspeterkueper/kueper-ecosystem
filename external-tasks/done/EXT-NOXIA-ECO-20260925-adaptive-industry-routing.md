---
id: EXT-NOXIA-ECO-20260925-adaptive-industry-routing
title: Adaptive industry program routing
status: done
source: NOXIA
target: ECO
created: 2026-09-25
requested_by: NOXIA research intake
affects: [ECO, ENG, OTA, KG, NXU, NOXIA]
supersedes: []
---

# EXT-NOXIA-ECO-20260925-adaptive-industry-routing – Adaptive industry program routing

- **Origin:** NOXIA research intake
- **Target:** KUEPER Ecosystem
- **Date:** 2026-09-25
- **Status:** done

## Anlass

Alt-Task ohne kanonisches Format, eingegangen am 2026-09-25 (Herkunft: NOXIA research intake). Am 13.11.2026 ins Format nach `docs/cross-repository-workflow.md` und ECO-ARC-0006 überführt (ECO-OPS-20261113-legacy-task-frontmatter); der ursprüngliche Auftragstext steht unverändert unter „Gewünschte Änderung“. Die `id` entspricht bewusst dem bisherigen Dateinamen, damit der Idempotenzschlüssel im Task-Bus gleich bleibt.

## Gewünschte Änderung

Register adaptive manufacturing / digital-twin / Physical-AI work as a cross-project program.

Ownership:
- OTA: evidence, maturity and provenance.
- KG: canonical industrial entities, states and relations.
- Engineering: plant/twin/control architecture and interfaces.
- NOXIA Universe: historical/social/off-world development.
- NOXIA Game: production gameplay, UX, balancing and learning module.
- NOXIA Realtime: later visualization/runtime integration after contracts stabilize.

Cross-link explicitly with the Energy Grid Layer, MiniNode/robot-swarm program, mining/resources, logistics, buildings and the NOXIA learning-module family. Preserve federated ownership.

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

- Programm registriert: `docs/programs/adaptive-industry.md` mit Zweck, Geltungsbereich, Zuständigkeiten (OTA, KG, ENG, NXU, NOXIA; `noxia-realtime` zurückgestellt) und Regeln.
- Querverweise zu Energy Grid Layer, MiniNode/Roboterschwarm, Bergbau/Ressourcen, Logistik, Gebäuden/Siedlungen (Mars Settlement Kernel, Living Infrastructure) und der NOXIA-Lernmodulfamilie.
- Folgearbeiten: bereits ab 25.09.2026 geroutet (OTA `OTA-SCI-0110-2026-DE`, KG `ONT:KG:ADAPTIVE-MANUFACTURING-0.1` und ENG `ENG-SYS-AFCA-0001` erledigt; NXU-Entwicklung und -Integration sowie NOXIA-Gameplay/Lernmodul offen) und als Stand zusammengeführt; keine doppelten Aufträge erzeugt.
- Register `docs/programs/README.md` und `docs/system-map.md` ergänzt; Verweise in `living-infrastructure.md` und `mycology-soil-ecopoiesis.md` auf die Registrierung umgestellt.
