# KUEPER Ecosystem

Übergreifendes Architektur- und Governance-Repository für das KUEPER-Projektsystem.

Dieses Repository ist nicht die Website, nicht der Knowledge Graph, nicht SSF und nicht NOXIA. Es beschreibt, wie diese Projekte zusammenhängen, welche Zuständigkeiten gelten und welche gemeinsamen Regeln für Zusammenarbeit, Datenflüsse, IDs, Dokumenttypen und Entscheidungen verbindlich sind.

## Zweck

`kueper-ecosystem` ist die Meta-Ebene des Projektverbunds.

Es beantwortet Fragen wie:

- Welche Repositories gibt es?
- Welche Rolle hat jedes Repository?
- Was ist Source of Truth wofür?
- Welche Verweisrichtungen gelten?
- Wie werden Änderungen behandelt, die andere Repositories betreffen?
- Welche gemeinsamen Architekturentscheidungen gelten systemweit?
- Welche ID-, Metadaten- und Dokumentstandards sind verbindlich?

## Nicht-Zweck

Dieses Repository enthält nicht:

- fachliche Grundlageninhalte wie Physik, Mathematik oder Biologie,
- Lernmodule,
- Spielmechaniken,
- Website-Implementierung,
- fiktionale Inhalte,
- produktive Exporte des Knowledge Graph.

Diese Inhalte bleiben in den jeweils zuständigen Repositories.

## Repository-Landkarte

| Repository | Rolle |
|---|---|
| `kueper-ecosystem` | Übergreifende Architektur, Governance, Zuständigkeiten, Systemvereinbarungen |
| `kueper.com` | Wissenschaftliches KUE-Archiv / öffentliche Wissens- und Grundlagenpublikation |
| `kueper-knowledge-graph` | Semantische Ebene: Entitäten, Relationen, Knowledge Domains, KXF-Exporte, Mappings |
| `solarsciencefoundation` | Lernplattform: Module, Lernpfade, Übungen, Fortschritt, API-Schicht |
| `noxiagame` | Spielerische Anwendung und Simulation |
| `thomas-kueper.de` | Autorenwebsite, Werke, Philosophie, öffentliche Autorendarstellung |
| `overtime-archive.org` | Werkbezogene Real/Fiction-Exploration und fiktionale Anwendungsschicht |

## Startdokumente

- [`docs/system-map.md`](docs/system-map.md)
- [`docs/repository-roles.md`](docs/repository-roles.md)
- [`docs/source-of-truth.md`](docs/source-of-truth.md)
- [`docs/cross-repository-workflow.md`](docs/cross-repository-workflow.md)
- [`decisions/README.md`](decisions/README.md)

## Grundsatz

Jedes Projekt bleibt Source of Truth nur für seinen eigenen Zuständigkeitsbereich.

Wenn eine Änderung ein anderes Repository betrifft, wird sie nicht direkt umgesetzt. Stattdessen wird im Ziel-Repository unter `external-tasks/open/` eine Markdown-Anforderung angelegt. Bearbeitete Anforderungen werden später nach `done/` beziehungsweise `rejected/` verschoben.

## Status

Initialer Architektur-Grundstock. Noch nicht kanonisch vollständig.
