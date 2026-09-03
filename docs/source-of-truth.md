# Source of Truth

Status: draft  
Repository: `kueper-ecosystem`

## 1. Zweck

Dieses Dokument definiert, welches Repository für welchen Gegenstand die kanonische Quelle ist.

Source of Truth bedeutet:

> Wenn es widersprüchliche Aussagen in mehreren Repositories gibt, gilt die Aussage des zuständigen Repositories.

## 2. Grundregel

Jedes Repository ist nur für seinen eigenen Zuständigkeitsbereich Source of Truth.

Kein Repository darf fremde Domänen stillschweigend kanonisieren.

## 3. Zuständigkeiten

| Gegenstand | Source of Truth |
|---|---|
| Systemweite Architektur und Governance | `kueper-ecosystem` |
| Repository-Zuständigkeiten | `kueper-ecosystem` |
| Cross-Repository-Workflow | `kueper-ecosystem` |
| Systemweite Publikations- und KI-Transparenzpolicy | `kueper-ecosystem` (`config/publication-transparency.json`) |
| Gemeinsame ID- und Metadatenregeln | `kueper-ecosystem`, sofern systemweit; sonst jeweiliges Fachrepo |
| Entitäten und Relationen | `kueper-knowledge-graph` |
| Knowledge Domains | `kueper-knowledge-graph` |
| KXF-Exporte und Mappings | `kueper-knowledge-graph` |
| Projektübergreifende IDs, Mappings und semantische Relationen (KG) | `kueper-knowledge-graph` |
| KUE-Archivdokumente | `kueper.com` |
| Werkneutrale wissenschaftliche Grundlagenpublikation | `kueper.com` oder später eigenes Knowledge-Base-Repo, falls beschlossen |
| Lernmodule, Lernpfade, Übungen | `solarsciencefoundation` |
| Lernfortschritt und SSF-API | `solarsciencefoundation` |
| NOXIA-Spielmechaniken | `noxiagame` |
| NOXIA-Unlocks und Gameplay-Anwendung | `noxiagame` |
| Autorenwebsite und öffentliche Werkdarstellung | `thomas-kueper.de` |
| Fiktionale Archiv- und Werkbezüge | `overtime-archive.org` |
| Bestätigte universumsweite Primärdaten der NOXIA-Kontinuität (NXU) | `noxia-universe` |
| Ausschließlich kanonische `OTA-*`-Dokumente (OTA) | `overtime-archive.org` |
| Private Arbeitsstände/Authoring-Zustände für Buchprojekte und werkbezogene Medien (BW) | `buecherwelten` |

## 3a. Werkbezogene Abgrenzung (BW / NXU / OTA / KG)

Für Buchprojekte und werkbezogene Medien gilt folgende verbindliche
Zuständigkeitsabgrenzung (ECO-ARC-0031):

| Code | Zuständigkeit |
|---|---|
| `BW` | **private Arbeitsstände/Authoring-Zustände** — `buecherwelten` ist die private Authoring- und Entwicklungsschicht: Manuskripte, Szenen, Kapitelstände, werkbezogene Medien. Keine Publikationsschicht. |
| `NXU` | **bestätigte universumsweite Primärdaten der NOXIA-Kontinuität** — `noxia-universe` führt nur bestätigte Bücher, Figuren, Handlungen, Orte, Personen und Worldbuilding dieser Kontinuität. |
| `OTA` | **ausschließlich kanonische `OTA-*`-Dokumente** — `overtime-archive.org` ist alleinige Quelle für die kanonische OTA-Dokumentebene. |
| `KG` | **projektübergreifende IDs, Mappings und semantische Relationen** — `kueper-knowledge-graph` führt die semantische Verknüpfung zwischen den Projekten. |

Private Authoring-Inhalte (`BW`) werden durch bloße technische Lesbarkeit
nicht kanonisch, nicht publiziert und nicht automatisch nach `NXU`, `OTA`
oder `KG` übertragen (`private source -> public target` ist deny-by-default,
ECO-ARC-0030). Überführungen in eine andere Zuständigkeit erfordern eine
ausdrückliche Promotion-Entscheidung.

## 4. Referenzieren ist erlaubt

Ein Repository darf Informationen aus anderen Repositories verwenden oder referenzieren.

Beispiele:

- SSF darf auf KG-IDs referenzieren.
- NOXIA darf SSF-Fortschritt konsumieren.
- OTA darf auf KUE-Dokumente verweisen.
- `kueper.com` darf auf systemweite Governance-Regeln verweisen.

Das referenzierende Repository wird dadurch aber nicht Source of Truth für die referenzierte Information.

## 5. Keine verdeckte Kanonisierung

Eine Aussage wird nicht dadurch kanonisch, dass sie in einem abhängigen Repository verwendet wird.

Beispiel:

Wenn NOXIA einen Unlock `UNL:NOX:orbital-navigation` verwendet, definiert NOXIA den Unlock selbst, aber nicht die fachliche Physik, auf die er sich stützt.

## 6. Konfliktregel

Bei Konflikten gilt folgende Reihenfolge:

1. Zuständiges Source-of-Truth-Repository
2. Systemweite Governance-Regel aus `kueper-ecosystem`
3. explizit akzeptierte Architekturentscheidung
4. lokale Implementierung
5. Chat- oder Arbeitsnotiz

Arbeitsnotizen, Chat-Aussagen und Entwürfe sind nicht automatisch kanonisch.

## 7. Änderung fremder Zuständigkeiten

Wenn eine Änderung ein anderes Repository betrifft:

1. Änderung nicht direkt im aktuellen Repository umsetzen.
2. Ziel-Repository bestimmen.
3. Markdown-Anforderung unter `external-tasks/open/` im Ziel-Repository anlegen.
4. Ziel-Repository entscheidet über Annahme, Umsetzung, Ablehnung oder Anpassung.
5. Nach Bearbeitung wird die Anforderung nach `done/` oder `rejected/` verschoben.

## 8. Offene Frage: kanonische Wissensbasis

Noch zu entscheiden:

Soll ein eigenes Repository für fachliche Grundlageninhalte entstehen, z. B. `kueper-knowledge-base`?

Mögliche Rolle:

- kanonische Erklärtexte zu Mathematik, Physik, Chemie, Biologie, Informatik usw.
- unabhängig von SSF-Didaktik,
- unabhängig von kueper.com-Publikation,
- referenzierbar durch KG, SSF, NOXIA und KUE.

Bis zur Entscheidung bleiben fachliche Grundlagen dort, wo sie ausdrücklich angelegt werden, ohne automatische systemweite Kanonisierung.
