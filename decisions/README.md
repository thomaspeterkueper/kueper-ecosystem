# Architecture Decisions

Status: draft  
Repository: `kueper-ecosystem`

## Zweck

Dieser Ordner sammelt systemweite Architekturentscheidungen des KUEPER-Ökosystems.

Eine Entscheidung gehört hierher, wenn sie mehrere Repositories betrifft oder Grundregeln des gesamten Systems festlegt.

## Abgrenzung

Nicht jede lokale Repository-Entscheidung gehört hierher.

Beispiele für lokale Entscheidungen:

- konkrete CSS-Struktur in `kueper.com`,
- konkrete Komponente in `solarsciencefoundation`,
- konkreter Gameplay-Wert in `noxiagame`,
- konkrete KG-Entität im Knowledge Graph.

Diese Entscheidungen bleiben im jeweiligen Repository.

## Schema

Empfohlenes Dateischema:

```text
ECO-ARC-0001-YYYY-DE.md
```

Beispiel:

```text
ECO-ARC-0001-2026-DE.md
```

## Statuswerte

Empfohlene Statuswerte:

- `draft` — Entwurf, noch nicht verbindlich
- `proposed` — vorgeschlagen zur Diskussion
- `accepted` — akzeptiert und systemweit gültig
- `superseded` — durch spätere Entscheidung ersetzt
- `rejected` — abgelehnt

## Minimale Struktur

```md
# ECO-ARC-0001-YYYY-DE — Titel

Status: draft  
Datum: YYYY-MM-DD  
Scope: systemweit  
Betroffene Repositories: ...

## Kontext

## Entscheidung

## Begründung

## Auswirkungen

## Nicht entschieden

## Folgeaufgaben
```

## Entscheidungen

- [ECO-ARC-0005-2026-DE — Status- und Monitoring-Control-Plane](./ECO-ARC-0005-2026-DE.md) — `accepted`
- [ECO-ARC-0006-2026-DE — Kanonisches External-Task-Format](./ECO-ARC-0006-2026-DE.md) — `accepted`
- [ECO-ARC-0007-2026-DE — Dokument-Architektur des KUEPER-Ökosystems](./ECO-ARC-0007-2026-DE.md) — `accepted`
- [ECO-ARC-0008-2026-DE — Noxia-Universum: Buchkanon, OTA-Grenze und SSF-Dualität](./ECO-ARC-0008-2026-DE.md) — `accepted`
- [ECO-ARC-0009-2026-DE — Mishkenaz: Sprachforschung und In-universe-Sprache Dvarakas](./ECO-ARC-0009-2026-DE.md) — `accepted`
- [ECO-ARC-0010-2026-DE — Omnizedenz: Überblick + Vertiefung](./ECO-ARC-0010-2026-DE.md) — `accepted`
- [ECO-ARC-0011-2026-DE — AVI-Modell: Überblick + Vertiefung](./ECO-ARC-0011-2026-DE.md) — `accepted`
- [ECO-ARC-0012-2026-DE — Kontrakomologie / Contracomology: Registrierung einer bestehenden Fassade](./ECO-ARC-0012-2026-DE.md) — `accepted`
- [ECO-ARC-0013-2026-DE — KUEPER Archive Core: gemeinsames Datenbankschema für Dokumentarchive](./ECO-ARC-0013-2026-DE.md) — `accepted`
- [ECO-ARC-0014-2026-DE — Kanonisches Domain-Präfix: KD, nicht KNOW](./ECO-ARC-0014-2026-DE.md) — `accepted`

## Erste mögliche Entscheidungen

Noch anzulegen:

- ECO-ARC-0001 — Repository-Rollen und Source-of-Truth-Regel
- ECO-ARC-0002 — Cross-Repository-Workflow
- ECO-ARC-0003 — ID- und Metadatenkonventionen, sofern systemweit
- ECO-ARC-0004 — Verhältnis Ecosystem, KG, SSF, NOXIA, KUE, OTA
