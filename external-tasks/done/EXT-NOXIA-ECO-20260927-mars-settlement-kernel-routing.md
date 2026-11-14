---
id: EXT-NOXIA-ECO-20260927-mars-settlement-kernel-routing
title: Mars Settlement Systems Kernel routing
status: done
source: NOXIA
target: ECO
created: 2026-09-27
requested_by: NOXIA integration
affects: [ECO, ENG, OTA, KG, NXU, NOXIA]
supersedes: []
---

# EXT-NOXIA-ECO-20260927-mars-settlement-kernel-routing – Mars Settlement Systems Kernel routing

- **Origin:** NOXIA integration
- **Target:** KUEPER Ecosystem
- **Date:** 2026-09-27
- **Status:** done

## Anlass

Alt-Task ohne kanonisches Format, eingegangen am 2026-09-27 (Herkunft: NOXIA integration). Am 13.11.2026 ins Format nach `docs/cross-repository-workflow.md` und ECO-ARC-0006 überführt (ECO-OPS-20261113-legacy-task-frontmatter); der ursprüngliche Auftragstext steht unverändert unter „Gewünschte Änderung“. Die `id` entspricht bewusst dem bisherigen Dateinamen, damit der Idempotenzschlüssel im Task-Bus gleich bleibt.

## Gewünschte Änderung

Register the Mars Settlement Systems Kernel as the integration authority joining:
Energy Grid, ECLSS/water, Living Infrastructure/Mycology, agriculture, waste/recycling, Adaptive Industry, logistics and MiniNodes/robotics.

Ownership:
- Engineering: conserved flows, process contracts, resilience and fidelity.
- KG: canonical entities/relations/units.
- OTA: empirical calibration/provenance.
- Universe: settlement history, institutions and culture.
- Game: simulation, balancing, UX and learning.
- Realtime: later consumer of stable contracts.

Require downstream systems to reuse shared reservoirs/flows rather than creating duplicate resource counters.

The kernel must preserve the ecosystem-wide epistemic rule:
physical reality != observations != estimates/models != actor knowledge.

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

- Mars Settlement Systems Kernel in `kueper-ecosystem` als Integrationsinstanz registriert, Zuständigkeiten wie unter „Gewünschte Änderung“ festgehalten.
- Regel „gemeinsame Reservoirs/Flüsse statt doppelter Ressourcenzähler“ und die epistemische Trennung dokumentiert.
- Folgearbeiten in den Ziel-Repositories als External Tasks geroutet.

## Erledigt

Status: done – Ökosystem-Kreislauf (Claude), 15.11.2026.

## Umgesetzt

- Mars Settlement Systems Kernel als Integrationsinstanz registriert: `docs/programs/mars-settlement-kernel.md` mit verbundenen Systemen (Energy Grid, ECLSS/Wasser, Living Infrastructure/Mykologie, Landwirtschaft, Abfall/Recycling, Adaptive Industry, Logistik, MiniNodes/Robotik) und Zuständigkeiten (ENG, KG, OTA, NXU, NOXIA; `noxia-realtime` als späterer Konsument zurückgestellt).
- Regel „gemeinsame Reservoire und Flüsse statt doppelter Ressourcenzähler“ und die epistemische Trennung dokumentiert.
- Folgearbeiten: bereits ab 27.09.2026 geroutet (ENG `ENG-SYS-MSSK-0001`, KG `ONT:KG:SETTLEMENT-SYSTEMS-KERNEL-0.1` v0.1.1, OTA `OTA-SCI-0112-2026-DE` erledigt; NXU-Entwicklungsmodell und -Kanonisierung sowie NOXIA-Simulation und -Integration offen) und als Stand zusammengeführt; keine doppelten Aufträge erzeugt.
- Register `docs/programs/README.md` und `docs/system-map.md` ergänzt; Verweise in `living-infrastructure.md`, `mycology-soil-ecopoiesis.md`, `planetary-evolution.md` und `adaptive-industry.md` auf die Registrierung umgestellt.
