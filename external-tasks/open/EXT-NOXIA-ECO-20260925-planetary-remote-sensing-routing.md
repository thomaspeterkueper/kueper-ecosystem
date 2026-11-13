---
id: EXT-NOXIA-ECO-20260925-planetary-remote-sensing-routing
title: Planetary remote-sensing program routing
status: open
source: NOXIA
target: ECO
created: 2026-09-25
requested_by: NOXIA research intake
affects: [ECO, ENG, OTA, KG, NXU, NOXIA]
supersedes: []
---

# EXT-NOXIA-ECO-20260925-planetary-remote-sensing-routing – Planetary remote-sensing program routing

- **Origin:** NOXIA research intake
- **Target:** KUEPER Ecosystem
- **Date:** 2026-09-25
- **Status:** open

## Anlass

Alt-Task ohne kanonisches Format, eingegangen am 2026-09-25 (Herkunft: NOXIA research intake). Am 13.11.2026 ins Format nach `docs/cross-repository-workflow.md` und ECO-ARC-0006 überführt (ECO-OPS-20261113-legacy-task-frontmatter); der ursprüngliche Auftragstext steht unverändert unter „Gewünschte Änderung“. Die `id` entspricht bewusst dem bisherigen Dateinamen, damit der Idempotenzschlüssel im Task-Bus gleich bleibt.

## Gewünschte Änderung

Register Planetary Remote Sensing / Observational Astronomy as a cross-project program.

Ownership:
- OTA: evidence, provenance and research status.
- KG: observation/inference ontology and canonical IDs.
- Engineering: instrument/measurement simulation contracts.
- NOXIA Universe: discovery history and scientific culture.
- NOXIA Game: observation gameplay, uncertainty UX and learning modules.
- NOXIA Realtime: later visualization after contracts stabilize.

Cross-link with planetary-system generation, retrograde/non-coplanar architecture, navigation, exploration and the NOXIA learning-module family. Preserve the distinction between physical ground truth and actor/player knowledge.

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
