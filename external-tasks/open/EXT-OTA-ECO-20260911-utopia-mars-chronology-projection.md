---
id: EXT-OTA-ECO-20260911-utopia-mars-chronology-projection
title: Utopia Mars Chronology Projection
status: open
source: OTA
target: ECO
created: 2026-09-11
requested_by: OTA / NOXIA Universe
affects: [ECO, OTA, NXU, KG, NOXIA]
supersedes: []
---

# EXT-OTA-ECO-20260911-utopia-mars-chronology-projection – Utopia Mars Chronology Projection

**Status:** open  
**From:** OTA / NOXIA Universe  
**To:** KUEPER Ecosystem  
**Date:** 2026-09-11  
**Source PR:** https://github.com/thomaspeterkueper/overtime-archive.org/pull/60

## Anlass

Alt-Task ohne kanonisches Format, eingegangen am 2026-09-11 (Herkunft: OTA / NOXIA Universe). Am 13.11.2026 ins Format nach `docs/cross-repository-workflow.md` und ECO-ARC-0006 überführt (ECO-OPS-20261113-legacy-task-frontmatter); der ursprüngliche Auftragstext steht unverändert unter „Gewünschte Änderung“. Die `id` entspricht bewusst dem bisherigen Dateinamen, damit der Idempotenzschlüssel im Task-Bus gleich bleibt.

## Gewünschte Änderung

### Ziel

Den neuen Utopia-/Mars-Industrie-Strang in Timeline- und Cross-Project-Projektionen aufnehmen, ohne die OTA-Quelle zu duplizieren oder vorläufige Aussagen als Kanon zu behandeln.

### Neue Dokumente

- `OTA-SCI-0090-2026-DE`
- `OTA-HIS-0004-2021-DE`
- `OTA-META-0004-2076-DE`
- `OTA-HIS-0005-2050-DE`
- `OTA-ORG-0008-2087-DE`

### Timeline-Kandidaten

Bitte als getrennte Ereignisse/Phasen modellieren:

- 2021 — Zhurong landet in Utopia Planitia `[R]`
- 2024 — chinesische nationale Space-Science-Roadmap bis 2050 `[R]`
- ca. 2072–2075 — robotische Vorbereitung des Utopia-Siedlungsstandorts `[P]`
- ca. 2076/77 — erste permanente Besatzung `[P]`
- 03.12.2080 — Maryem Hamid auf Mars geboren `[K]`; Utopia-Zuordnung `[P]`
- 2087 — Große Stille als Kompetenz-/Resilienztest `[K/P]`
- 2091 — Utopia als etablierter zweiter Marsknoten `[P]`

### Modellierungsregeln

- Timeline ist Projektion des KG/OTA, nicht eigene Wahrheitsquelle.
- `45°N / 110°E` nicht als kanonische Stadtkoordinate anzeigen.
- endgültiger chinesischer Stadtname bleibt offen.
- reale Ereignisse und fiktionale Fortschreibung visuell/semantisch unterscheidbar halten.
- `Utopia-Siedlung` vorläufig als Alias/Arbeitsname behandeln.

### Cross-Project-Bezug

Relevant für:

- NOXIA Universe chronology
- Generation Mars
- Halden / Maryem Hamid
- NOXIAGAME world projection
- KUEPER Knowledge Graph

Bitte die neuen Beziehungen an bestehende Timeline-/Object–Relation–Event-Strukturen anschließen, nicht als separates Parallelmodell implementieren.

## Begründung

Timeline- und Cross-Project-Projektionen sind Ecosystem-Aufgabe; die OTA-Quelle bleibt Source of Truth und wird nicht dupliziert.

## Betroffene Repositories

- `kueper-ecosystem`
- `overtime-archive.org`
- `noxia-universe`
- `kueper-knowledge-graph`
- `noxiagame`

## Erwartetes Ergebnis

- Utopia-/Mars-Industrie-Strang als getrennte Ereignisse/Phasen in den Timeline- und Cross-Project-Projektionen aufgenommen, mit den Modellierungsregeln oben.
- Reale und fiktionale Einträge bleiben visuell und semantisch unterscheidbar; keine Duplizierung der OTA-Quelle.
