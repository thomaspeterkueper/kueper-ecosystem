---
id: EXT-NOXIA-ECO-20260925-mycology-ecopoiesis-routing
title: Mycology / soil ecology / ecopoiesis routing
status: done
source: NOXIA
target: ECO
created: 2026-09-25
requested_by: NOXIA research intake
affects: [ECO, ENG, OTA, KG, NXU, NOXIA]
supersedes: []
---

# EXT-NOXIA-ECO-20260925-mycology-ecopoiesis-routing – Mycology / soil ecology / ecopoiesis routing

- **Origin:** NOXIA research intake
- **Target:** KUEPER Ecosystem
- **Date:** 2026-09-25
- **Status:** done

## Anlass

Alt-Task ohne kanonisches Format, eingegangen am 2026-09-25 (Herkunft: NOXIA research intake). Am 13.11.2026 ins Format nach `docs/cross-repository-workflow.md` und ECO-ARC-0006 überführt (ECO-OPS-20261113-legacy-task-frontmatter); der ursprüngliche Auftragstext steht unverändert unter „Gewünschte Änderung“. Die `id` entspricht bewusst dem bisherigen Dateinamen, damit der Idempotenzschlüssel im Task-Bus gleich bleibt.

## Gewünschte Änderung

Register Mycology / Soil Ecology / Ecopoiesis as a cross-project program and explicitly connect it to existing Mars-settlement research rather than creating a parallel silo.

Ownership:
- OTA: evidence, prior-research consolidation and provenance.
- KG: canonical ecological entities/relations.
- Engineering: controlled-substrate/ecosystem simulation contracts.
- NOXIA Universe: settlement/ecopoiesis history and culture.
- NOXIA Game: ecology gameplay and Hidden Biosphere learning modules.
- NOXIA Realtime: later visualization after contracts stabilize.

Cross-link with Planetary Evolution, biospheres, agriculture, closed-loop life support, waste/recycling, resources, habitats and future terraforming. Preserve federated ownership.

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

Status: done – Ökosystem-Kreislauf (Claude), 14.11.2026.

## Umgesetzt

- Programm registriert: `docs/programs/mycology-soil-ecopoiesis.md` mit Zweck, Geltungsbereich, Zuständigkeiten (OTA, KG, ENG, NXU, NOXIA; `noxia-realtime` zurückgestellt) und Abgrenzung zu Living Infrastructure (Fachdomäne unter der Integrationsschicht, keine eigenen Ressourcenzähler).
- Anschluss an die bestehende Mars-Siedlungsforschung statt Parallelsilo: Querverweise zu Living Infrastructure, Mars Settlement Kernel, Planetary Evolution, ECLSS/Landwirtschaft/Abfall, Ressourcen/Habitaten und Myzelbaustoffen.
- Folgearbeiten: bereits am 25.–27.09.2026 geroutet (KG-Ontologie und ENG-Bodenökologie-Architektur erledigt; OTA-Dossier, NXU-Kanon und NOXIA-Gameplay offen) und in der Registrierung als Stand zusammengeführt; keine doppelten Aufträge erzeugt.
- Register `docs/programs/README.md` und `docs/system-map.md` ergänzt; Verweis in `docs/programs/living-infrastructure.md` auf die Registrierung umgestellt.
