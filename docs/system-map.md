# System Map

Status: draft  
Repository: `kueper-ecosystem`

## 1. Zweck der Systemkarte

Diese Systemkarte beschreibt die oberste Struktur des KUEPER-Projektverbunds. Sie dient als Orientierung für Menschen und KI-Assistenten, bevor in einzelnen Repositories gearbeitet wird.

## 2. Grundmodell

```text
kueper-ecosystem
  |
  |-- definiert systemweite Architektur, Governance und Zuständigkeiten
  |
  v
kueper-knowledge-graph
  |
  |-- verwaltet semantische Entitäten, Relationen, Domains, Mappings und Exporte
  |
  +--> kueper.com
  |      öffentliche wissenschaftliche Archiv- und Publikationsschicht
  |
  +--> solarsciencefoundation
  |      Lernmodule, Lernpfade, Übungen, Fortschritt, API
  |
  +--> noxiagame
  |      spielerische Anwendung und Simulation
  |
  +--> overtime-archive.org
         werkbezogene Real/Fiction-Schicht

thomas-kueper.de
  |
  |-- öffentliche Autoren-, Werk- und Philosophieplattform
```

## 3. Rollen der Ebenen

### Governance-Ebene

`kueper-ecosystem` beschreibt, welche Regeln gelten.

Beispiele:

- Repository-Zuständigkeiten
- Source-of-Truth-Regeln
- Cross-Repository-Workflow
- ID- und Metadatenkonventionen
- Architekturentscheidungen

### Semantische Ebene

`kueper-knowledge-graph` beschreibt, wie Wissen, Entitäten und Systeme zusammenhängen.

Beispiele:

- Knowledge Domains
- Entitäten
- Relationen
- KXF-Exporte
- systemübergreifende Mappings

### Archiv- und Publikationsebene

`kueper.com` veröffentlicht und archiviert wissenschaftlich oder methodisch relevante Grundlagen. Es bleibt werkneutral und universumsunabhängig.

### Lern- und Vermittlungsebene

`solarsciencefoundation` übersetzt Wissen in didaktische Module, Lernpfade, Übungen und Fortschrittszustände.

### Anwendungsebene

`noxiagame` nutzt Wissen, Lernfortschritt und Konzepte spielerisch.

### Autoren- und Werkebene

`thomas-kueper.de` bündelt Autor, Werke, Philosophie, Projektseiten und öffentliche Darstellung.

### Fiktionale Archiv- und Anwendungsschicht

`overtime-archive.org` erlaubt werkbezogene und fiktionale Kontexte, sofern sie korrekt auf reale Grundlagen und KUE/KG-Bezüge verweisen.

## 4. Verweisrichtungen

Grundregel:

```text
Governance -> Graph -> Archiv/Lernen/Anwendung
```

Praktisch:

- `kueper-ecosystem` darf systemweite Regeln für alle Repositories definieren.
- `kueper-knowledge-graph` darf auf systemweite Regeln referenzieren und semantische Mappings anbieten.
- `kueper.com` darf auf KG- oder Ecosystem-Regeln verweisen, bleibt aber fachlich werkneutral.
- `solarsciencefoundation` darf Wissen didaktisch transformieren.
- `noxiagame` darf Wissen spielerisch anwenden.
- `overtime-archive.org` darf fiktionale Kontexte auf reale Grundlagen zurückführen.

## 5. Nicht-Ziele dieser Systemkarte

Diese Datei entscheidet noch nicht im Detail über:

- konkrete ID-Formate,
- konkrete KXF-Schemas,
- konkrete Lernmodul-Strukturen,
- konkrete NOXIA-Unlock-Regeln,
- konkrete Publikationsregeln für einzelne Dokumente.

Diese Themen erhalten eigene Dokumente oder Architekturentscheidungen.
