# Project Registry

Version: 1.1.0  
Stand: 2026-08-29

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
- Noxia Universe
- Mishkenaz
- Omnizedenz
- AVI-Modell
- Contracomology
- KUEPER Archive Core
- Endia
- Zereya
- Davaru
- Fluíde Hermeneutik
- Resonanz-Ethik
- Buecherwelten

## Grundregeln

- `enabled: true` aktiviert die Überwachung; `enabled: false` deaktiviert sie: Collector und Dashboard überspringen das Projekt, bis der Owner den Eintrag aktiviert.
- `repository` ist die verbindliche GitHub-Quelle für Repository-Metadaten.
- `code` ist der verbindliche Ökosystem-Code (ECO-ARC-0031); die Referenzliste der vergebenen Codes steht in ECO-ARC-0006. Das Feld ist seit Schema-Revision 1.1.0 kanonischer Ablageort, nicht mehr nur die `notes`.
- `role` beschreibt die Rolle; `authoring` bezeichnet private Arbeitsstände/Authoring-Zustände (keine Publikationsschicht).
- `sensitivity` modelliert Vertraulichkeit und Berechtigungen für sensible Repositories (z. B. `private-manuscript-source`, ECO-ARC-0030/0031). Für private Quellen gilt deny-by-default: kein automatischer Inhaltstransfer an öffentliche Ziele.
- `version_source` enthält geordnete Kandidaten. Der Collector verwendet die erste vorhandene und lesbare Quelle.
- `required_paths` sind Governance-Erwartungen. Fehlende Pfade werden nicht automatisch angelegt, sondern als Abweichung gemeldet.
- `integrations` beschreibt erwartete Beziehungen, nicht deren technische Implementierung.
- Unbekannte URLs oder Health-Endpunkte bleiben `null`. Sie dürfen nicht geraten werden.
- Secret-Werte gehören niemals in die Registry.

## Private Repositories

Für private Repositories (z. B. `buecherwelten`) verarbeiten Collector und
Dashboard ausschließlich operative Metadaten: Erreichbarkeit, Default Branch,
letzter Push, Anzahl offener PRs (keine Titel), Existenz der Governance-Pfade,
Dateinamen und Frontmatter offener External Tasks sowie das `private`-Flag.
Inhalte werden weder gelesen noch gespeichert. Der für Collector/Dashboard
verwendete read-only `GH_TOKEN` muss `Contents: read` für das private
Repository besitzen, damit die Überwachung funktioniert.

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
