# Project Registry

Version: 1.0.0  
Stand: 2026-07-10

## Zweck

`projects.json` beschreibt den Soll-Zustand der Projekte, die durch das KUEPER Ecosystem überwacht werden.

Die Registry ist keine Source of Truth für fachliche Projektdaten. Sie enthält ausschließlich Beobachtungsziele und systemweite Erwartungen.

## Enthaltene Projekte

- KUEPER Ecosystem
- NOXIA
- Solar Science Foundation
- KUEPER Knowledge Graph
- OverTime Archive
- kueper.com
- thomas-kueper.de

## Grundregeln

- `enabled: true` aktiviert die Überwachung.
- `repository` ist die verbindliche GitHub-Quelle für Repository-Metadaten.
- `version_source` enthält geordnete Kandidaten. Der Collector verwendet die erste vorhandene und lesbare Quelle.
- `required_paths` sind Governance-Erwartungen. Fehlende Pfade werden nicht automatisch angelegt, sondern als Abweichung gemeldet.
- `integrations` beschreibt erwartete Beziehungen, nicht deren technische Implementierung.
- Unbekannte URLs oder Health-Endpunkte bleiben `null`. Sie dürfen nicht geraten werden.
- Secret-Werte gehören niemals in die Registry.

## Validierung

Die Datei wird gegen folgendes Schema validiert:

```text
schemas/project-registry.schema.json
```

Eine ungültige Registry muss den Collector stoppen. Aus einer unvollständigen oder syntaktisch fehlerhaften Registry darf kein grüner Status erzeugt werden.

## Änderungen an anderen Repositories

Ergibt sich aus einer Prüfung eine notwendige Änderung in einem Ziel-Repository, wird diese nicht hier umgesetzt. Stattdessen gilt der Ablauf aus:

```text
docs/cross-repository-workflow.md
```

Die Anforderung wird im Ziel-Repository unter `external-tasks/open/` angelegt.
