# Knowledge Expansion & Multilingual Research Loop

Status: V3.2  
Control Plane: `kueper-ecosystem`

## Zweck

Der V3-Loop erweitert das Ecosystem um kontrollierte Wissensvertiefung. Er soll für NOXIA, Noxia Universe, Mishkenaz, OTA, SSF und ausgewählte Buch-/Wissensprojekte relevante externe Wissenslücken selbst finden, priorisieren und recherchieren.

Seit V3.1 besitzt die Research-Phase einen gemeinsamen **External-Evidence-Layer**. Exa Web Search wird über Vercel AI Gateway als vorgeschalteter Recherche-Scout verwendet. Exa ersetzt weder die eigentliche Quellenkritik noch die Candidate-Validierung und besitzt keinerlei Schreibrecht auf kanonische Wissensbestände.

V3.2 ergänzt davor eine **epistemische Claim-Klassifikation** und danach eine **explizite Publikationsroute**. Insbesondere gilt: reale wissenschaftliche E-Papers gehören nach Review in die öffentliche `KUE-SCI`-Schicht von `kueper.com`; OTA bleibt Archiv-/In-Universe-Schicht und darf reale Evidenz, Theorie, Spekulation und Fiktion nebeneinander dokumentieren, ohne diese Ebenen zu vermischen.

## Architektur

```text
ELIGIBLE PROJECT
      ↓
GAP DISCOVERY
  repo lesen, keine Änderung
      ↓
CLAIM CLASSIFICATION
  epistemische Klasse vor externer Recherche
  F/W-only ohne Realanker → keine Exa-Recherche
      ↓
RELEVANCE + EXTERNAL-RESEARCH GATE
      ↓
research/queue/RES-*.json
      ↓
EXTERNAL EVIDENCE SCOUT
  Exa via Vercel AI Gateway
  nur extern prüfbare Anteile recherchieren
      ↓
MULTILINGUAL EVIDENCE RESEARCH
  Evidence-Paket + zusätzliche Verifikation + Quellenkritik
      ↓
PROFILE-SPECIFIC EVIDENCE GATE
      ↓
KG: research/candidates/RES-*.md
      ↓
NON-CANONICAL CANDIDATE
      ↓
review-gated publication recommendation
  real scientific e-paper → kueper.com / KUE-SCI
  archive/canon document  → OTA
      ↓
später: Validation / Canon Conflict / Consumer Requests
```

## Discovery und Claim-Klassifikation

`tools/research/discover.py` wählt pro Tag ein freigegebenes Projekt rotierend aus. Der Agent liest dessen aktuellen Repository-Stand und darf maximal drei tatsächlich relevante externe Wissenslücken melden.

Vor dem Queueing muss bei Profilen mit `require_claim_classification` die epistemische Klasse feststehen. Der Discovery-Agent speichert deshalb `claim_classes`, `external_research_required`, einen optionalen `real_world_anchor` und einen rein beratenden `publication_route_hint` im Queue-Eintrag.

Für OTA gelten die vorhandenen Archivmarker als Recherchevertrag:

- `R`: extern prüfbare reale Aussage; starke Evidenz erforderlich.
- `T`: theoretische/modelleigene Aussage; Quellen dürfen Prämissen und Konsistenz stützen oder begrenzen, nicht das Postulat durch Quellenzahl „beweisen“.
- `H`: Hypothese/falsifizierbare Aussage; unterstützende, Null- und Gegenbefunde müssen sichtbar bleiben.
- `S`: Spekulation; externe Recherche prüft Grenzen und Plausibilitätsanker, nicht die Wahrheit der Spekulation.
- `F`: fiktionaler Kanon; Exa besitzt keinerlei Validierungsautorität.
- `W`: Werk-Setzung; wird als Werkfakt behandelt, nicht als Realwissen.
- `R-Anker`: fiktionale Aussage mit realem Anker; nur der reale Anker wird extern geprüft.
- `OFFEN`: explizit ungelöste Frage; bleibt offen, solange der externe Anteil nicht belastbar geklärt ist.

Reine `F/W`-Gaps ohne realen Anker werden nicht als externe Research Topics eingereiht. Das verhindert, dass ein Search-System fiktionalen Kanon scheinbar wissenschaftlich „bestätigt“.

Bewertet werden außerdem Relevanz für das konkrete Projekt, Wiederverwendbarkeit, Unsicherheit und Evidenzpotenzial. Der Mittelwert bildet den `relevance_score`; unter 0,60 wird kein Research Topic angelegt.

## Research Queue

Die Queue liegt zentral unter `research/queue/` im Ecosystem. Queue-Einträge enthalten Herkunft, Frage, Relevanzscore, gewünschte Recherche-Sprachen, Evidenzprofil, vorab festgelegte Claim-Klassen, den realen Rechercheanker, gegebenenfalls eine Publikationsroute und einen Fingerprint gegen Wiederholungen.

## External Evidence mit Exa

`tools/research/agent-with-exa.mjs` ist ein Wrapper vor dem bestehenden Research-Agenten. Er erhält dieselbe Research-Frage und zusätzlich die vorab klassifizierten Claims. Die Exa-Suche soll nur die extern prüfbaren Anteile, Prämissen, Grenzen, historischen Attestationen, Gegenbefunde oder Falsifizierbarkeitsfragen untersuchen.

Der Scout bevorzugt Primärquellen, peer-reviewte Arbeiten, offizielle Institutionen, Standards, akademische Verlage und originale technische Dokumentation. Sein Evidence-Paket enthält Claim-Klassifikation, Kandidaten-Claims, Gegenbefunde, Unsicherheit, Aktualitätsprüfung und nachvollziehbare URLs.

Das Evidence-Paket ist ausdrücklich **Discovery-Material / non-canonical**. Der nachgeschaltete Research-Agent muss Aussagen weiterhin gegen Quellen prüfen, Claim-Source-Mapping erzeugen und die jeweiligen Evidenzregeln erfüllen.

Die zentrale Konfiguration liegt unter `research/policy.json`. `external_evidence` steuert Exa; `evidence_profiles` steuert Qualitätsanforderungen; `publication_routing` definiert nur mögliche Zielschichten, niemals automatische Publikation.

### Authentifizierung und Fallback

Für GitHub Actions wird das Repository Secret `AI_GATEWAY_API_KEY` verwendet. Ist es nicht gesetzt oder schlägt Exa/AI Gateway fehl, wird der bestehende Research-Agent ohne vorgeschaltetes Evidence-Paket ausgeführt. Damit blockiert ein externer Search-Provider niemals den bestehenden Recherche-Loop.

Der Fallback darf später auf `required: true` verschärft werden, wenn Exa im produktiven Betrieb ausreichend stabil beobachtet wurde.

## OTA-Profil: `ota-archive-evidence`

Das OTA-Profil ist absichtlich kein normales „science“-Profil. OTA-Dokumente können reale Wissenschaft, Theoriebildung, historische Anker, Spekulation, Werk-Setzungen und fiktionalen Kanon im selben Dokument enthalten. Daher verlangt das Profil vor Recherche die Claim-Klasse und nach Recherche zusätzlich `Claim-Klassifikation`, `Aktualität und Widerspruchsprüfung` sowie `Publikationsroute` im Candidate.

Für extern prüfbare OTA-Anteile gelten mindestens 0,70 Evidence Score, drei Quellen, zwei Domains, drei sichtbare URLs und mindestens ein starker Quellentyp. Das ist eine Candidate-Schwelle, keine Kanonisierung.

## Reale wissenschaftliche E-Papers: `kueper.com` / `KUE-SCI`

Die öffentliche kanonische Publikationsschicht für reale wissenschaftliche E-Papers ist:

```text
Repository: thomaspeterkueper/kueper.com
Pfad:       src/content/kue/sci
Namespace:  KUE-SCI
Route-ID:   real_scientific_epaper
```

Dafür existiert das strengere Evidenzprofil `scientific-publication`: mindestens 0,78 Evidence Score, vier Quellen, drei Domains, vier URLs, starker Primär-/Peer-Review-/Dataset-Anker, Claim-Klassifikation sowie Aktualitäts- und Gegenbefundprüfung.

Wichtig: Der Research Loop darf eine KUE-SCI-Route **empfehlen**, aber niemals direkt publizieren. Erst ein späterer Review-/Promotion-Schritt darf aus einem KG-Candidate ein öffentliches KUE-SCI-Dokument erzeugen. OTA-spezifisches Canon-Framing, fiktionale Erweiterungen oder Werk-Setzungen werden dabei nicht in ein reales wissenschaftliches E-Paper übernommen.

## Multilinguale Recherche

`tools/research/execute.py` priorisiert Queue-Einträge und recherchiert standardmäßig höchstens zwei Themen pro Lauf.

Deutsch und Englisch sind allgemeine Ausgangssprachen. Weitere Sprachen werden projektspezifisch vorgeschlagen. Für Mishkenaz sind zunächst zusätzlich Hindi, Gujarati und Sanskrit freigegeben, weil diese für bestimmte historische, regionale oder philologische Fragen zusätzliche Quellenräume erschließen können.

Sprache ist kein Qualitätsmerkmal. Eine Quelle wird nach Autorität, Nähe zum Gegenstand, Methodik, Publikationskontext, Aktualität und Nachprüfbarkeit bewertet.

## Candidate Format

Research-Ergebnisse werden ausschließlich unter `research/candidates/` im Knowledge Graph abgelegt. Jeder Candidate enthält mindestens Forschungsfrage, Kurzfazit, Befundlage, Gegenbefunde und Unsicherheit, Claim-Source-Mapping, Quellen mit URL/Sprache/Quellentyp, Relevanz für KUEPER-Projekte und offene Fragen. Profilabhängig kommen Claim-Klassifikation, Aktualitäts-/Widerspruchsprüfung und Publikationsroute hinzu.

Diese Dokumente sind ausdrücklich `candidate / non-canonical`.

## Sicherheits- und Qualitätsgrenzen

V3.2 darf nicht kanonische KG-Entitäten oder Relationen automatisch ändern, Roman-/Game-Kanon verändern, F/W-Setzungen extern „beweisen“, unbelegte Aussagen als Wissen übernehmen, Quellen/URLs/Autoren/Publikationen/Übersetzungen/Zitate erfinden, eine Sprache als Belegqualität behandeln oder direkt in OTA bzw. kueper.com publizieren.

Exa ändert daran nichts: Search-Treffer sind Hinweise auf Evidenz, nicht selbst kanonisches Wissen.

## Takt und Budget

Der Workflow `.github/workflows/knowledge-research-loop.yml` läuft einmal täglich und kann manuell gestartet werden. Standardgrenzen sind ein Projekt pro Discovery-Lauf, maximal drei neue Research-Gaps, maximal zwei recherchierte Topics, maximal fünf Quellensprachen pro Topic und Exa standardmäßig sechs Resultate pro Suchaufruf mit adaptiv höchstens einem weiteren Suchpass.

Die Werte werden in `research/policy.json` zentral gepflegt. Nach Ende zeitlich begrenzter Gateway-Aktionen müssen Search-Kosten und Limits gegen den tatsächlichen Nutzen des Loops neu bewertet werden.

## Beziehung zu den anderen Loops

V1 erledigt vorhandene Requests.  
V2 erzeugt und routet notwendige Cross-Repo-Folgeaufgaben.  
V3 entdeckt und recherchiert externe Wissenslücken.  
V3.1 ergänzt V3 um einen zentralen External-Evidence-Scout über Exa.  
V3.2 ergänzt die epistemische Vorabklassifikation und trennt Research-Candidate, OTA-Archiv und reale KUE-SCI-Publikation explizit.

V4 soll Research Candidates gegen vorhandenes Realwissen und fiktionalen Kanon prüfen und daraus gezielt Übernahme-, Konflikt- oder Consumer-Requests erzeugen.
