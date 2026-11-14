---
id: EXT-NOXIA-ECO-20260925-planetary-architecture-routing
title: Planetary architecture / learning routing
status: done
source: NOXIA
target: ECO
created: 2026-09-25
requested_by: NOXIA research intake
affects: [ECO, ENG, OTA, KG, NXU, NOXIA]
supersedes: []
---

# EXT-NOXIA-ECO-20260925-planetary-architecture-routing – Planetary architecture / learning routing

- **Origin:** NOXIA research intake
- **Target:** KUEPER Ecosystem
- **Date:** 2026-09-25
- **Status:** done

## Anlass

Alt-Task ohne kanonisches Format, eingegangen am 2026-09-25 (Herkunft: NOXIA research intake). Am 13.11.2026 ins Format nach `docs/cross-repository-workflow.md` und ECO-ARC-0006 überführt (ECO-OPS-20261113-legacy-task-frontmatter); der ursprüngliche Auftragstext steht unverändert unter „Gewünschte Änderung“. Die `id` entspricht bewusst dem bisherigen Dateinamen, damit der Idempotenzschlüssel im Task-Bus gleich bleibt.

## Gewünschte Änderung

Register the non-coplanar/retrograde planetary-system workstream and route ownership.

- OTA: evidence and provenance.
- KG: canonical entities/relations.
- NOXIA Universe: formation-history/worldbuilding canon.
- Engineering: orbital-mechanics contracts.
- NOXIA Game: procedural generation, gameplay and learning module.
- NOXIA Realtime: later visualization/runtime adoption after contracts stabilize.

Cross-link with astronomy, navigation, system generation, exploration and the emerging NOXIA learning-module family. Preserve federated ownership.

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

- Programm registriert: `docs/programs/planetary-architecture.md` mit Zweck, Geltungsbereich, Zuständigkeiten (OTA, KG, NXU, ENG, NOXIA; `noxia-realtime` zurückgestellt) und Regeln.
- Trennung von beobachteter Geometrie und Entstehungsgeschichte sowie die epistemische Regel ausdrücklich festgehalten.
- Querverweise zu Astronomie/Fernerkundung, Navigation, Systemgenerierung, Exploration und der NOXIA-Lernmodulfamilie.
- Folgearbeiten: bereits ab 25.09.2026 geroutet (KG `ONT:KG:SPIN-ORBIT-ARCHITECTURE-0.1` und ENG `ENG-CONTRACT-ORBIT-PLANE-0001` erledigt; OTA-Fallstudie GJ 3090 b, NXU-Mehrfachgeschichten, NOXIA-Generierung/Lernmodul und Übernahme des Bahnebenen-Vertrags offen) und als Stand zusammengeführt; keine doppelten Aufträge erzeugt.
- Register `docs/programs/README.md` und `docs/system-map.md` ergänzt; Verweis in `docs/programs/planetary-remote-sensing.md` auf die Registrierung ergänzt.
