---
id: EXT-NOXIA-ECO-20260925-living-infrastructure-integration
title: Living infrastructure integration
status: done
source: NOXIA
target: ECO
created: 2026-09-25
requested_by: Mycology / Planetary Evolution / Life Support
affects: [ECO, ENG, OTA, KG, NXU, NOXIA]
supersedes: []
---

# EXT-NOXIA-ECO-20260925-living-infrastructure-integration – Living infrastructure integration

- **Origin:** Mycology / Planetary Evolution / Life Support
- **Target:** KUEPER Ecosystem
- **Date:** 2026-09-25
- **Status:** open

## Anlass

Alt-Task ohne kanonisches Format, eingegangen am 2026-09-25 (Herkunft: Mycology / Planetary Evolution / Life Support). Am 13.11.2026 ins Format nach `docs/cross-repository-workflow.md` und ECO-ARC-0006 überführt (ECO-OPS-20261113-legacy-task-frontmatter); der ursprüngliche Auftragstext steht unverändert unter „Gewünschte Änderung“. Die `id` entspricht bewusst dem bisherigen Dateinamen, damit der Idempotenzschlüssel im Task-Bus gleich bleibt.

## Gewünschte Änderung

Register Living Infrastructure as the integration layer joining Mycology/Soil Ecology, closed-loop life support, agriculture, waste/recycling, Planetary Evolution and future ecopoiesis.

Ensure Engineering owns conserved-flow/system contracts, KG owns material/process identities, Universe owns historical/cultural consequences, Game owns player-facing loops, and OTA owns evidence.

Note: repository-wide searches on 2026-09-25 did not locate older Mars-fungi material under obvious terms (Mars/Pilze/fungi/mycelium/regolith/ecopoiesis). Treat prior research as potentially external, differently named or not yet migrated; do not assume absence from the wider project archive.

Do not route to Realtime until stable contracts exist.

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

- Living Infrastructure als Cross-Repository-Programm registriert: `docs/programs/living-infrastructure.md` mit Zweck, Geltungsbereich, Zuständigkeitsverteilung, Integrationsrichtung und Abgrenzung.
- Programmregister `docs/programs/README.md` angelegt und aus `README.md` sowie `docs/system-map.md` verlinkt.
- Querverweise zu Mycology/Soil Ecology/Ecopoiesis, Planetary Evolution, Mars Settlement Kernel, Energy Grid, Adaptive Industry, Robotics/MiniNode sowie zu ECLSS und Myzelbaustoffen dokumentiert.
- Folgearbeit-Envelopes für `ENG` (konservierte Flüsse/Systemverträge), `KG` (Material-/Prozessidentitäten) und `OTA` (Evidenz/Provenienz) in `.kueper/outbox/` erzeugt; das Routing in die Ziel-Repositories übernimmt der Ecosystem-Loop.
- `NXU` und `NOXIA` bewusst nachgelagert, `noxia-realtime` gemäß Auftrag ausgeschlossen.
