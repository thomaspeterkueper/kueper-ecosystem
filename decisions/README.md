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

## Erste mögliche Entscheidungen

Noch anzulegen:

- ECO-ARC-0001 — Repository-Rollen und Source-of-Truth-Regel
- ECO-ARC-0002 — Cross-Repository-Workflow
- ECO-ARC-0003 — ID- und Metadatenkonventionen, sofern systemweit
- ECO-ARC-0004 — Verhältnis Ecosystem, KG, SSF, NOXIA, KUE, OTA
