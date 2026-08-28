# Knowledge Expansion & Multilingual Research Loop

Status: V3.1  
Control Plane: `kueper-ecosystem`

## Zweck

Der V3-Loop erweitert das Ecosystem um kontrollierte Wissensvertiefung. Er soll für NOXIA, Noxia Universe, Mishkenaz, OTA, SSF und ausgewählte Buch-/Wissensprojekte relevante externe Wissenslücken selbst finden, priorisieren und recherchieren.

Seit V3.1 besitzt die Research-Phase einen gemeinsamen **External-Evidence-Layer**. Exa Web Search wird über Vercel AI Gateway als vorgeschalteter Recherche-Scout verwendet. Exa ersetzt weder die eigentliche Quellenkritik noch die Candidate-Validierung und besitzt keinerlei Schreibrecht auf kanonische Wissensbestände.

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
EXTERNAL EVIDENCE SCOUT
  Exa via Vercel AI Gateway
  Quellen finden + Unsicherheit sichtbar machen
      ↓
MULTILINGUAL EVIDENCE RESEARCH
  Evidence-Paket + zusätzliche Verifikation + Quellenkritik
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

## External Evidence mit Exa

`tools/research/agent-with-exa.mjs` ist ein Wrapper vor dem bestehenden Research-Agenten. Er erhält dieselbe Research-Frage wie der Synthese-Agent und führt zuerst eine gezielte Exa-Suche über Vercel AI Gateway aus.

Der Scout soll bevorzugt Primärquellen, peer-reviewte Arbeiten, offizielle Institutionen, Standards, akademische Verlage und originale technische Dokumentation finden. Sein Ergebnis ist ein kompaktes Evidence-Paket mit Kandidaten-Claims, Gegenbefunden, Unsicherheit und nachvollziehbaren URLs.

Das Evidence-Paket ist ausdrücklich **Discovery-Material / non-canonical**. Der nachgeschaltete Research-Agent muss Aussagen weiterhin gegen Quellen prüfen, Claim-Source-Mapping erzeugen und die bestehenden Evidenzregeln erfüllen.

Die zentrale Konfiguration liegt unter `research/policy.json` im Block `external_evidence`. Standardmäßig gelten:

- Provider: Exa;
- Transport: Vercel AI Gateway;
- leichtes Gateway-Modell für die Scout-Synthese;
- 6 Suchergebnisse pro Exa-Aufruf;
- maximal 4 Agent-Schritte;
- mindestens 2 sichtbare Quell-URLs im Evidence-Paket;
- `required: false` für einen sicheren Fallback.

### Authentifizierung und Fallback

Für GitHub Actions wird das Repository Secret `AI_GATEWAY_API_KEY` verwendet. Ist es nicht gesetzt oder schlägt Exa/Ai Gateway fehl, wird der bestehende Research-Agent ohne vorgeschaltetes Evidence-Paket ausgeführt. Damit blockiert ein externer Search-Provider niemals den bestehenden Recherche-Loop.

Der Fallback darf später auf `required: true` verschärft werden, wenn Exa im produktiven Betrieb ausreichend stabil beobachtet wurde.

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

Exa ändert daran nichts: Search-Treffer sind Hinweise auf Evidenz, nicht selbst kanonisches Wissen.

## Takt und Budget

Der Workflow `.github/workflows/knowledge-research-loop.yml` läuft einmal täglich und kann manuell gestartet werden.

Standardgrenzen:

- 1 Projekt pro Discovery-Lauf;
- maximal 3 neue Research-Gaps;
- maximal 2 recherchierte Topics;
- maximal 5 Quellensprachen pro Topic;
- Relevanzschwelle 0,60;
- Evidenzschwelle 0,65;
- Exa standardmäßig 6 Resultate pro Aufruf und maximal 4 Scout-Schritte.

Die Werte werden in `research/policy.json` zentral gepflegt. Nach Ende zeitlich begrenzter Gateway-Aktionen müssen Search-Kosten und Limits gegen den tatsächlichen Nutzen des Loops neu bewertet werden.

## Beziehung zu den anderen Loops

V1 erledigt vorhandene Requests.  
V2 erzeugt und routet notwendige Cross-Repo-Folgeaufgaben.  
V3 entdeckt und recherchiert externe Wissenslücken.  
V3.1 ergänzt V3 um einen zentralen External-Evidence-Scout über Exa.

V4 soll Research Candidates gegen vorhandenes Realwissen und fiktionalen Kanon prüfen und daraus gezielt Übernahme-, Konflikt- oder Consumer-Requests erzeugen.
