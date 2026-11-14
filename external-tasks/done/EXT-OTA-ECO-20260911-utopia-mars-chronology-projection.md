---
id: EXT-OTA-ECO-20260911-utopia-mars-chronology-projection
title: Utopia Mars Chronology Projection
status: done
source: OTA
target: ECO
created: 2026-09-11
requested_by: OTA / NOXIA Universe
affects: [ECO, OTA, NXU, KG, NOXIA]
supersedes: []
---

# EXT-OTA-ECO-20260911-utopia-mars-chronology-projection – Utopia Mars Chronology Projection

**Status:** done  
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

## Abschluss (2026-10-10)

Umgesetzt in PR #115 (`chore(agent): execute task b0697af4`). Der Utopia-/Mars-Strang
ist als eigener Scope `Utopia/Mars` in die bestehende Universe-Timeline-Projektion
(ECO-ARC-0018-2026-DE) aufgenommen:

- `app/internal/universe/timeline/seed-projection.ts` – Projektionsdaten und
  Marker-Mapping (`[R]`/`[K]` → kanonisch, `[F/P]`/`[P]` → vorläufig, `[K/P]` nicht
  hochgestuft), sieben Ereignisse/Phasen aus dem Task, `caveats` für offene Punkte.
- `app/api/internal/universe-timeline/route.ts` und
  `app/internal/universe/timeline/page.tsx` – Auslieferung und UI mit sichtbaren
  Projektionshinweisen (Real/Fiktion unterscheidbar, Vorbehalte einsehbar).
- `tests/universe-projection.test.ts` – Vertrag, Marker-Mapping, Koordinatenverbot,
  Quellen-Signaturen und Cross-Project-Anker; grün über `npm run test:timeline`.
- `docs/utopia-mars-chronology-projection.md` – Dokumentation der Projektion,
  der Modellierungsregeln und der Abweichung zum Task-Text.

Modellierungsregeln eingehalten: keine kanonische Stadtkoordinate (bleibt `[OFFEN]`),
keine Duplikation der OTA-Quelle, keine Parallelstruktur (`relation_refs` auf
`WORK:NOXIA:generation_mars` und `CHAR:NOXIA:maryem_hamid`).

Abweichung zum Task-Text: `OTA-META-0004-2076-DE` v1.1 (Stand nach OTA PR #60)
setzt **Kaiwu (开物)** inzwischen als `[K]`; darum entfällt der Arbeitsname
„Utopia-Siedlung" und die Annahme eines offenen Stadtnamens. Die Projektion folgt
dem aktuellen OTA-Stand und legt die Abweichung in `docs/` und im API-Feld `caveats`
offen.

Zweites Review und Übernahme: Ökosystem-Kreislauf (Claude), 14.11.2026 – Konflikt mit der Frontmatter-Migration vom 13.11.2026 aufgelöst, kanonisches Format beibehalten. Erledigt. Umgesetzt.
