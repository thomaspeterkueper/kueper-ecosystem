# Cross-Repository Workflow

Status: draft  
Repository: `kueper-ecosystem`

## 1. Zweck

Dieses Dokument definiert den Arbeitsablauf für Änderungen, die mehrere Repositories betreffen.

Ziel ist, die Source-of-Truth-Grenzen zu schützen und trotzdem koordinierte Weiterentwicklung zu ermöglichen.

## 2. Grundsatz

Wenn eine Änderung ein anderes Repository betrifft, wird sie nicht direkt im aktuellen Repository umgesetzt.

Stattdessen wird im Ziel-Repository eine Markdown-Anforderung angelegt.

## 3. Standardstruktur

Jedes Repository, das externe Anforderungen erhalten kann, verwendet folgende Struktur:

```text
external-tasks/
  open/
  done/
  rejected/
```

Optional:

```text
external-tasks/
  parked/
```

für Anforderungen, die grundsätzlich sinnvoll sind, aber aktuell nicht entschieden werden.

## 4. Ablauf

### Schritt 1: Zuständigkeit prüfen

Vor jeder Änderung wird geprüft:

- Betrifft sie das aktuelle Repository?
- Betrifft sie ein anderes Repository?
- Betrifft sie mehrere Repositories?
- Betrifft sie systemweite Governance?

### Schritt 2: Ziel-Repository bestimmen

Die Zuständigkeit ergibt sich aus `docs/repository-roles.md` und `docs/source-of-truth.md`.

### Schritt 3: Anforderung anlegen

Im Ziel-Repository wird eine Markdown-Datei unter `external-tasks/open/` angelegt.

### Schritt 4: Ziel-Repository entscheidet

Das Ziel-Repository kann:

- akzeptieren,
- anpassen,
- ablehnen,
- parken,
- in mehrere Anforderungen aufteilen.

### Schritt 5: Abschluss dokumentieren

Nach Bearbeitung wird die Datei verschoben nach:

- `external-tasks/done/`
- `external-tasks/rejected/`
- optional `external-tasks/parked/`

## 5. Dateinamensschema

Empfohlenes Schema:

```text
EXT-{SOURCE}-{TARGET}-{YYYYMMDD}-{NNN}.md
```

Beispiele:

```text
EXT-KUE-KG-20260708-001.md
EXT-SSF-NOXIA-20260708-001.md
EXT-ECO-KG-20260708-001.md
```

## 6. Mindestinhalt einer externen Anforderung

```md
# EXT-SOURCE-TARGET-YYYYMMDD-NNN — Kurztitel

Status: open  
Source Repository: `...`  
Target Repository: `...`  
Created: YYYY-MM-DD  
Requested by: ...

## Anlass

Warum entsteht diese Anforderung?

## Gewünschte Änderung

Was soll geändert, ergänzt oder geprüft werden?

## Begründung

Warum gehört die Änderung ins Ziel-Repository?

## Betroffene Repositories

- `...`

## Erwartetes Ergebnis

Was gilt als erledigt?

## Hinweise

Optionale Kontextinformationen.
```

## 7. Kein direkter Fremd-Commit

Ein Repository soll keine fachlichen oder architektonischen Entscheidungen in einem anderen Repository direkt erzwingen.

Ausnahmen sind nur möglich, wenn der Projekt Owner ausdrücklich erlaubt, im Ziel-Repository zu arbeiten und die Änderung dort fachlich zuständig ist.

## 8. Beispiele

### Beispiel A: SSF benötigt KG-Relation

SSF erkennt, dass ein Lernmodul eine neue Voraussetzung benötigt.

Nicht direkt in SSF definieren:

```text
requires: KNOW:gravity-basic
```

wenn diese Relation im KG noch nicht existiert.

Stattdessen:

```text
kueper-knowledge-graph/external-tasks/open/EXT-SSF-KG-YYYYMMDD-001.md
```

### Beispiel B: NOXIA benötigt SSF-Unlock

NOXIA möchte einen neuen Spielmechanik-Unlock an Lernfortschritt koppeln.

Die Spielmechanik liegt in NOXIA, der Lernfortschritt in SSF.

Ergebnis:

- NOXIA definiert den Gameplay-Bedarf.
- SSF entscheidet über Lernfortschritts- und API-Integration.

### Beispiel C: systemweite ID-Regel

Wenn eine ID-Regel alle Repositories betrifft, gehört die Architekturentscheidung zuerst nach `kueper-ecosystem`.

Danach können Ziel-Repositories externe Anforderungen zur Umsetzung erhalten.

### Beispiel D: Foundation Mining (wiederkehrendes Muster)

Ein Repository erschließt wiederverwendbare Realwissenschaft aus Beständen anderer Repositories, z. B. `kueper.com` (KUE) aus OTA- und SSF-Dokumenten (Arbeitsinventar: `kueper.com/docs/backlog/KUE-FOUNDATION-MINING-2026-09-22.md`).

Zuständigkeits- und Ableitungsrichtung:

```text
Primärliteratur → KUE-Realgrundlage → KG-Identität/Relation → SSF-Didaktik bzw. OTA/NOXIA-Anwendung
```

Die Pfeilkette beschreibt, wer wofür zuständig ist und in welche Richtung abgeleitet wird – keine Pflicht zur linearen technischen Verarbeitung. Sie ändert keine Zuständigkeit aus `docs/source-of-truth.md`.

Regeln:

- KUE übernimmt nur, was projektübergreifend, realwissenschaftlich, quellenfähig und gegenüber dem bestehenden KUE-Kanon eigenständig ist; vorher Deduplizierung gegen den Bestand.
- Projektspezifische Parameter (Spielwerte, Weltbau-Annahmen, technische Dimensionierung) bleiben im Herkunfts-Repository bzw. in `kueper-engineering` und werden nicht nach KUE übernommen.
- Bedarf in KG, SSF, OTA oder NOXIA läuft als External Task ins jeweilige Ziel-Repository; das Quell-Repository wird durch das Mining nicht Source of Truth für die abgeleitete Grundlage.
- Grounding-Audits prüfen Verweise entlang dieser Richtung: Anwendungen verweisen auf KG-IDs bzw. KUE-Dokumente, nicht umgekehrt.

## 9. Arbeitsartefakte aus Google Drive

Entwürfe, Spezifikationen, Reviews, LLM-/Agent-Übergaben sowie Bild- und Binärdaten dürfen in einem projektbezogenen Drive-Exchange liegen. Sie sind dort Arbeitsmaterial und **nicht** kanonisch.

Regeln:

- Kanonisch wird ein Artefakt erst durch bewusste Übernahme in das zuständige Repository; der Weg ist `incoming -> specs/graphics -> reviewed -> Repository -> archive` ([`ECO-ARC-0039-2026-DE`](../decisions/ECO-ARC-0039-2026-DE.md), [`docs/drive-exchange-standard.md`](drive-exchange-standard.md)).
- Die Übernahme in ein fremdes Repository läuft weiterhin ausschließlich über `external-tasks/open/` im Ziel-Repository. Ein Drive-Artefakt ersetzt diesen Weg nicht.
- Repository-Review, Tests und Merge-Gates gelten unverändert; ein Drive-Review ist kein Ersatz.
- Nach der Übernahme verweist das Drive-Artefakt auf Ziel-Repository, Pfad und möglichst Commit/PR.
- Es gibt keinen automatischen Sync in eine Richtung; insbesondere werden Binärdaten nicht automatisch in öffentliche Repositories kopiert.
- Private Drive-Inhalte, private URLs und vertrauliche Metadaten gehören nicht in öffentliche ECO-Indizes oder External Tasks.
