# Repository Roles

Status: draft  
Repository: `kueper-ecosystem`

## 1. Zweck

Dieses Dokument definiert die Zuständigkeiten der Repositories im KUEPER-Ökosystem.

Ziel ist, Überschneidungen zu vermeiden und klar festzuhalten, welches Repository für welchen Gegenstand Source of Truth ist.

## 2. Repository-Rollen

| Repository | Primäre Rolle | Enthält | Enthält nicht |
|---|---|---|---|
| `kueper-ecosystem` | Systemarchitektur und Governance | Regeln, Zuständigkeiten, Architekturentscheidungen, Cross-Repo-Workflow | Fachinhalte, Lernmodule, Spielmechaniken |
| `kueper.com` | Wissenschaftliches Archiv und Publikationsschicht | werkneutrale Grundlagen, KUE-Dokumente, methodische Texte | Fiktion, Charaktere, Spielmechaniken |
| `kueper-knowledge-graph` | Semantische Struktur | Entitäten, Relationen, Domains, Mappings, KXF-Exporte | lange Erklärtexte, Website-Layout, Lerncontent |
| `solarsciencefoundation` | Lernplattform | Lernmodule, Lernpfade, Übungen, Fortschritt, API | kanonische Fachquelle, Spielsimulation |
| `noxiagame` | Spiel und Anwendung | Spielsysteme, Simulation, Unlocks, Gameplay-Kontext | kanonische Wissensdefinitionen |
| `thomas-kueper.de` | Autoren- und Werkplattform | Autor, Werke, öffentliche Projektseiten, Philosophie | systemweite Governance, KG-Exporte |
| `overtime-archive.org` | werkbezogene Real/Fiction-Schicht | fiktionale Anwendung, Werkarchive, Real/Fiction-Brücken | kanonische wissenschaftliche Grundlagen |

## 3. Grundsatz: Kein Repository besitzt fremde Domänen

Ein Repository darf externe Konzepte referenzieren, aber nicht zur Source of Truth für sie werden.

Beispiele:

- NOXIA darf `PHY-L0-000001` verwenden, aber nicht definieren, was dieses Modul fachlich bedeutet.
- SSF darf ein KG-Konzept didaktisch vermitteln, aber nicht die KG-Relationen kanonisch ändern.
- `kueper.com` darf wissenschaftliche Grundlagen veröffentlichen, aber keine NOXIA-Spielmechanik definieren.
- `kueper-ecosystem` darf festlegen, welche Regeln gelten, aber keine Physikmodule schreiben.

## 4. Repository-Grenzen

### `kueper-ecosystem`

Zuständig für:

- Systemvision
- Repository-Landkarte
- Source-of-Truth-Regeln
- Cross-Repository-Workflow
- systemweite Architekturentscheidungen
- gemeinsame Standards

Nicht zuständig für:

- konkrete Implementierung in Einzelprojekten
- Fachinhalte
- Spielinhalte
- Lernmodultexte

### `kueper-knowledge-graph`

Zuständig für:

- semantische Entitäten
- Relationen
- Knowledge Domains
- KXF-Exporte
- systemübergreifende Mappings

Nicht zuständig für:

- ausführliche didaktische Texte
- Website-Design
- Spielszenen

### `kueper.com`

Zuständig für:

- öffentliche oder interne KUE-Archivdokumente
- werkneutrale wissenschaftliche Grundlagen
- methodische Dokumente
- kuratierte Wissenspublikation

Nicht zuständig für:

- fiktionale Welten
- Charaktere
- NOXIA-Gameplay
- SSF-Fortschrittslogik

### `solarsciencefoundation`

Zuständig für:

- Lernmodule
- Lernpfade
- Übungen
- Fortschrittszustände
- didaktische Vermittlung
- Schnittstellen zu NOXIA

Nicht zuständig für:

- Source of Truth der Fachinhalte
- globale Projektgovernance

### `noxiagame`

Zuständig für:

- Spielsysteme
- Simulation
- Unlocks
- Gameplay-Integration
- Anwendung von Wissen im Spiel

Nicht zuständig für:

- kanonische Definitionen von Wissen
- SSF-Lernarchitektur
- KG-Domänenmodell

### `thomas-kueper.de`

Zuständig für:

- öffentliche Autorenpräsenz
- Werkübersichten
- philosophische und literarische Projektseiten
- kuratierte öffentliche Darstellung

Nicht zuständig für:

- systemweite Architektur
- KG-Exporte
- SSF-Modulverwaltung

### `overtime-archive.org`

Zuständig für:

- werkbezogene Archive
- fiktionale Anwendungen
- Real/Fiction-Brücken
- narrative Kontextualisierung

Nicht zuständig für:

- wissenschaftliche Grundlagen als Source of Truth
- globale Governance

## 5. Änderungsprinzip

Wenn eine gewünschte Änderung außerhalb des zuständigen Repositories liegt, wird sie nicht direkt umgesetzt.

Stattdessen wird im Ziel-Repository eine Markdown-Anforderung unter `external-tasks/open/` angelegt.
