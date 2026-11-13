---
id: EXT-NOXIA-ECO-20260927-mars-settlement-kernel-routing
title: Mars Settlement Systems Kernel routing
status: open
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
- **Status:** open

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
