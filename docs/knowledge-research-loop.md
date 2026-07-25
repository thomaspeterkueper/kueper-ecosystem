# Knowledge Expansion & Multilingual Research Loop

Status: V3  
Control Plane: `kueper-ecosystem`

## Zweck

Der V3-Loop erweitert das Ecosystem um kontrollierte Wissensvertiefung. Er soll für NOXIA, Noxia Universe, Mishkenaz, OTA, SSF und ausgewählte Buch-/Wissensprojekte relevante externe Wissenslücken selbst finden, priorisieren und recherchieren.

## Architektur

```text
ELIGIBLE PROJECT
      ↓
GAP DISCOVERY
  repo lesen, keine Änderung
      ↓
RELEVANCE GATE >= 0,60
      ↓
research/queue/RES-*.json
      ↓
MULTILINGUAL EVIDENCE RESEARCH
  Websuche + Quellenkritik
      ↓
EVIDENCE GATE >= 0,65
  >= 2 Quellen / >= 2 Domains
      ↓
KG: research/candidates/RES-*.md
      ↓
NON-CANONICAL CANDIDATE
      ↓
später: Validation / Canon Conflict / Consumer Requests
```

## Discovery

`tools/research/discover.py` wählt pro Tag ein freigegebenes Projekt rotierend aus. Der Agent liest dessen aktuellen Repository-Stand und darf maximal drei tatsächlich relevante externe Wissenslücken melden.

Bewertet werden:

- Relevanz für das konkrete Projekt;
- Wiederverwendbarkeit in anderen KUEPER-Projekten;
- bestehende Unsicherheit;
- Aussicht auf belastbare externe Evidenz.

Der Mittelwert bildet den `relevance_score`. Unter 0,60 wird kein Research Topic angelegt.

## Research Queue

Die Queue liegt zentral unter `research/queue/` im Ecosystem. Queue-Einträge enthalten Herkunft, Frage, Relevanzscore, gewünschte Recherche-Sprachen und einen Fingerprint gegen Wiederholungen.

## Multilinguale Recherche

`tools/research/execute.py` priorisiert Queue-Einträge und recherchiert standardmäßig höchstens zwei Themen pro Lauf.

Deutsch und Englisch sind allgemeine Ausgangssprachen. Weitere Sprachen werden projektspezifisch vorgeschlagen. Für Mishkenaz sind zunächst zusätzlich Hindi, Gujarati und Sanskrit freigegeben, weil diese für bestimmte historische, regionale oder philologische Fragen zusätzliche Quellenräume erschließen können.

Wichtig: Sprache ist kein Qualitätsmerkmal. Eine Quelle wird nach Autorität, Nähe zum Gegenstand, Methodik, Publikationskontext, Aktualität und Nachprüfbarkeit bewertet.

## Candidate Format

Research-Ergebnisse werden ausschließlich unter `research/candidates/` im Knowledge Graph abgelegt. Jeder Candidate enthält mindestens:

- Forschungsfrage;
- Kurzfazit;
- Befundlage;
- Gegenbefunde und Unsicherheit;
- Claim-Source-Mapping;
- Quellen mit URL, Sprache und Quellentyp;
- Relevanz für KUEPER-Projekte;
- offene Fragen.

Diese Dokumente sind ausdrücklich `candidate / non-canonical`.

## Sicherheits- und Qualitätsgrenzen

V3 darf nicht:

- kanonische KG-Entitäten oder Relationen automatisch ändern;
- Roman- oder Game-Kanon verändern;
- unbelegte Aussagen als Wissen übernehmen;
- Quellen, URLs, Autoren, Publikationen, Übersetzungen oder Zitate erfinden;
- eine Sprache als Belegqualität behandeln;
- beliebig viele Themen erzeugen.

## Takt und Budget

Der Workflow `.github/workflows/knowledge-research-loop.yml` läuft einmal täglich und kann manuell gestartet werden.

Standardgrenzen:

- 1 Projekt pro Discovery-Lauf;
- maximal 3 neue Research-Gaps;
- maximal 2 recherchierte Topics;
- maximal 5 Quellensprachen pro Topic;
- Relevanzschwelle 0,60;
- Evidenzschwelle 0,65.

Die Werte werden in `research/policy.json` zentral gepflegt.

## Beziehung zu den anderen Loops

V1 erledigt vorhandene Requests.  
V2 erzeugt und routet notwendige Cross-Repo-Folgeaufgaben.  
V3 entdeckt und recherchiert externe Wissenslücken.

V4 soll Research Candidates gegen vorhandenes Realwissen und fiktionalen Kanon prüfen und daraus gezielt Übernahme-, Konflikt- oder Consumer-Requests erzeugen.
