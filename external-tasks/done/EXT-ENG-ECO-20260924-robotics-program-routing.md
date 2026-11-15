---
id: EXT-ENG-ECO-20260924-robotics-program-routing
title: Cross-project robotics program routing
status: done
source: ENG
target: ECO
created: 2026-09-24
requested_by: KUEPER Engineering / NOXIA
affects: [ECO, ENG, OTA, KG, NXU, NOXIA]
supersedes: []
---

# EXT-ENG-ECO-20260924-robotics-program-routing – Cross-project robotics program routing

- **Origin:** KUEPER Engineering / NOXIA
- **Target:** KUEPER Ecosystem
- **Date:** 2026-09-24
- **Status:** done

## Anlass

Alt-Task ohne kanonisches Format, eingegangen am 2026-09-24 (Herkunft: KUEPER Engineering / NOXIA). Am 13.11.2026 ins Format nach `docs/cross-repository-workflow.md` und ECO-ARC-0006 überführt (ECO-OPS-20261113-legacy-task-frontmatter); der ursprüngliche Auftragstext steht unverändert unter „Gewünschte Änderung“. Die `id` entspricht bewusst dem bisherigen Dateinamen, damit der Idempotenzschlüssel im Task-Bus gleich bleibt.

## Gewünschte Änderung

Register and govern a cross-project robotics/MiniNode program.

### Responsibility split
- KUEPER Engineering: physical architecture, interfaces, prototype engineering and eventual real-world garden-remodelling swarm.
- KG: canonical entities/relations/IDs.
- OTA: evidence, technical dossiers, maturity/provenance.
- noxia-universe: historical/cultural/industrial canon.
- noxiagame: gameplay, balancing and runtime contracts.
- noxia-realtime: later visualization/control implementation only after contracts stabilize.

Ensure the federated rule remains intact: each repository owns only its domain; cross-repository changes travel as external tasks. The real-world garden robot swarm is a future capital-dependent program, not a current build commitment.

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

- Programm registriert: `docs/programs/robotics-mininode.md` mit Zweck, Geltungsbereich, Zuständigkeiten (ENG, KG, OTA, NXU, NOXIA, Produktpfad `kueper-products`; `noxia-realtime` zurückgestellt) und Regeln; der reale Garten-Roboterschwarm ist als künftiges, kapitalabhängiges Programm festgehalten.
- Querverweise zu Adaptive Industry, Mars Settlement Systems Kernel, Living Infrastructure, Energy Grid Layer und Planetarer Fernerkundung.
- Folgearbeiten: bereits ab 24.09.2026 geroutet (ENG `ENG-SYS-MININODE-0001` und `ENG-SYS-MININODE-ENV-0001`, KG `ONT:KG:MODULAR-ROBOTICS-0.1` und OTA `OTA-TEC-0126-2026-DE` erledigt; NXU-Linie und -Integration, NOXIA-Gameplay und Products-Handoff offen) und als Stand zusammengeführt; keine doppelten Aufträge erzeugt.
- Register `docs/programs/README.md` und `docs/system-map.md` ergänzt; Verweise in `adaptive-industry.md`, `living-infrastructure.md` und `mars-settlement-kernel.md` auf die Registrierung umgestellt.
