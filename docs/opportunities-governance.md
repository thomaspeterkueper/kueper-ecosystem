# Externe Forschungs- und Förderchancen – systemweiter Vertrag (Entwurf)

Status: proposal · Issue: [#131](https://github.com/thomaspeterkueper/kueper-ecosystem/issues/131) · Stand: 2026-11-24

## Zweck und Zuständigkeit

Dieses Dokument beschreibt den **gemeinsamen Metadatenvertrag** für Förderprogramme, Wettbewerbe, Kooperationen und Publikationsmöglichkeiten. Das Ecosystem ist die Source of Truth **für das Schema und die Zuständigkeitsregeln**, nicht für die operativen Chancenakten oder fachwissenschaftlichen Evidenzen. Eine spätere zentrale Übersicht konsumiert Daten aus der dafür benannten operativen Komponente; sie erzeugt keine zweite unabhängige Datenbank. Fachliche Forschungsbefunde bleiben in den zuständigen Projekten, Relationen im KG. Änderungen an anderen Repositories erfolgen gemäß `docs/cross-repository-workflow.md`.

## Opportunity v0.1 – Pflichtfelder

- `id`: stabile ID `OPP-YYYY-NNNN`, nach Vergabe unveränderlich; `YYYY` ist das Jahr der Ersterfassung (nicht Frist- oder Vergabejahr). Bis zur Freigabe des ID-Raums (siehe „ID-Vergabe“) ist `id: null`.
- `title`, `type`: `grant | prize | collaboration | publication`
- `organizer`, `official_url`, `source_checked_at`: Primärquelle und Zeitpunkt der Prüfung (ISO-8601)
- `status`: `discovered | screening | prioritized | preparing | submitted | awarded | rejected | archived`
- `eligibility`: `eligible | partner_required | ineligible | unclear`
- `eligibility_reason`: nachvollziehbarer Grund, kein bloßer Score
- `eligibility_checked_at`: Prüfdatum (ISO-8601)
- `projects`: Liste von Projekt-IDs aus `registry/projects.json` (Feld `id`, z. B. `knowledge-graph`, `noxia`), keine Repository-Namen
- `topics`: Liste von Themen-Schlagworten (Freitext v0.1; spätere Bindung an KG-Domains offen)
- `call_round`: Ausschreibungsrunde bzw. Ausgabejahr (z. B. `2027`); Teil des Dedup-Schlüssels (Regel 5), `null` nur bei fortlaufend offenen Programmen
- `owner`: interne Rolle oder Person für die nächste Entscheidung
- `effort`: `low | medium | high | unknown` plus `effort_note` (Begründung, z. B. geschätzte Personentage)
- `assessment`: getrennte Bewertungsdimensionen nach Regel 3, je Dimension `rating` (`low | medium | high | unknown`) und `reason`; Dimensionen: `research_fit`, `validation_level`, `benefit`, `visibility`, `collaboration_potential`, `ip_risk`. Vor dem Eligibility-Gate alle `unknown`.
- `status_history`: Auditliste nach Regel 6, je Eintrag `at` (ISO-8601), `by`, `from`, `to`, `reason`; der erste Eintrag hat `from: null`

Alle Pflichtfelder müssen in jedem Datensatz vorhanden sein. Für die beiden Prüfzeitpunkte gelten getrennte Regeln (siehe Regel 1 und 2):

- `source_checked_at` ist `null`, solange noch keine offizielle Quelle geprüft wurde; dann gilt zwingend `eligibility: unclear`.
- `eligibility_checked_at` ist `null`, solange das Eligibility-Gate noch nicht geprüft wurde; dann gilt ebenfalls zwingend `eligibility: unclear`. Der Zwischenzustand „Primärquelle geprüft, Gate noch offen“ (`source_checked_at` gesetzt, `eligibility_checked_at: null`, `eligibility: unclear`) ist ausdrücklich zulässig.
- Invarianten: `eligibility` ≠ `unclear` ⇒ `source_checked_at` und `eligibility_checked_at` beide gesetzt; `eligibility_checked_at` gesetzt ⇒ `source_checked_at` gesetzt. Ein geprüftes Gate darf `unclear` bleiben (fehlende Nachweise, Regel 2); dann ist `eligibility_checked_at` gesetzt.

Optionale Felder: `deadline_at` (exakte Frist, ISO-8601 mit Uhrzeit und Zeitzone); `deadline_date` (Fristdatum `YYYY-MM-DD`; gesetzt, sobald eine Frist bekannt ist – bei exakter Frist das lokale Datum von `deadline_at`, sonst das allein bekannte Datum) mit `deadline_status` (`confirmed | reported | unknown`, siehe Regel 1); `evidence_status` (Reifegrad des eingebrachten KUEPER-Beitrags, siehe Regel 4; ab Status `prioritized` Pflicht); `contact` (externer Ansprechpartner beim Ausrichter, nur dienstliche Kontaktangaben aus der offiziellen Quelle); `funding_amount` plus Währung; `country`; `language`; `partner_requirements`; `degree_requirements`; `publication_requirements`; `institution_requirements`; `residency_requirements`; `legal_form_requirements`; `allowed_ai_use`; `ip_terms`; `submission_url`; `evidence_refs` (kanonische IDs/URLs); `notes`; `next_action`; `last_reviewed_at`.

## ID-Vergabe

`OPP-*` ist ein neuer systemweiter Identitätsraum. Laut `decisions/ECO-ARC-0032-2026-DE.md` ist die Aufnahme weiterer Identitätsräume in die Signatur-Registry ausdrücklich nicht entschieden; parallele Vergabe nach Stichprobe hat dort bereits zu Kollisionen geführt. Daher gilt:

- Es wird **keine** `OPP-*`-ID vergeben, bevor eine angenommene Architekturentscheidung (ECO-ARC) festlegt, wer IDs vergibt und wie Eindeutigkeit gesichert wird (z. B. Erweiterung der Signatur-Registry um die Serie `OPP` mit `nextFree`, Kollisionsprüfung und Lint).
- Bis dahin tragen Datensätze `id: null` und werden über normierte `official_url` + Ausrichter + Ausschreibungsrunde identifiziert (Regel 5).

## Prüf- und Entscheidungsregeln

1. Vor Bewertung müssen **offizielle** Teilnahmebedingungen mit Abrufdatum hinterlegt werden. Die Einreichungsfrist wird als exakte lokale Zeit mit Zeitzone in `deadline_at` erfasst. `deadline_date` trägt immer das Fristdatum, sobald eine Frist bekannt ist: Ist `deadline_at` gesetzt, ist `deadline_date` dessen Datum in der dort angegebenen Zeitzone; ist nur das Datum bekannt, bleibt `deadline_at` `null` – Uhrzeit oder Zeitzone werden nicht erfunden. `deadline_status` sagt, woher die Frist stammt: `confirmed` (offizielle Teilnahmebedingungen mit Abrufdatum), `reported` (Mitteilung oder Sekundärquelle, noch nicht bestätigt), `unknown` (keine Frist bekannt; dann `deadline_at` und `deadline_date` beide `null`). Invarianten: `deadline_at` gesetzt ⇒ `deadline_date` gesetzt und gleich dessen lokalem Datum; `confirmed` ⇒ `source_checked_at` nicht `null` und `deadline_date` gesetzt; `reported` ⇒ `deadline_date` gesetzt; `unknown` ⇔ `deadline_at` und `deadline_date` beide `null`. Für Filter und Fristwarnungen gilt bei fehlender Uhrzeit vorsichtshalber der Beginn des Fristtags.
2. **Eligibility ist ein Gate, keine gewichtete Punktzahl.** Fehlen Nachweise, ist der Status `unclear`; erforderlicher eigener Hochschulabschluss fehlt ⇒ `ineligible`, sofern es keine legitime alternative Bewerberkonstellation gibt. `partner_required` nur bei belegbar zulässiger kooperativer Bewerbung, nicht zur Umgehung von Regeln.
3. Erst danach: fachlicher Fit, Forschungs-/Validierungsreife, Nutzen, Sichtbarkeit, Kooperationspotenzial und IP-Risiko (Feld `assessment`), Aufwand (`effort`) und Frist (`deadline_at`) als getrennte, dokumentierte Dimensionen beurteilen. Keine aggregierte Scheingenauigkeit ohne Kalibrierung.
4. Evidenzstatus strikt trennen, im Feld `evidence_status`: `idea | hypothesis | simulated | experimentally_tested | independently_replicated | peer_reviewed`. Eine Simulation ersetzt weder Messung noch unabhängige Replikation. `evidence_status` beschreibt nur den Reifegrad des Beitrags, mit dem sich KUEPER bewerben würde; es ersetzt nicht die beiden Achsen aus `decisions/ECO-ARC-0036-2026-DE.md`. Die einzelnen Belege in `evidence_refs` behalten Herkunftsebene (`provenance`) und Prüfstand (`verification`) aus ihrer jeweiligen Source of Truth. Eine Abbildung des Reifegrads auf Status-Marker oder Herkunftsebenen legt dieser Vertrag nicht fest. `assessment.validation_level` bleibt die begründete Einschätzung, wie gut der Reifegrad zur Ausschreibung passt.
5. Projektbezüge nur als kanonische Referenzen. Duplikate über den Dedup-Schlüssel prüfen (Normierung siehe unten); gleicher Preis in anderem Jahr ist nicht automatisch Duplikat.
6. Statuswechsel auditieren (wer, wann, von/nach, Begründung) im Feld `status_history`. Bewerbungen werden **nie** automatisch verschickt.
7. KI-Einsatz-, Urheber-, Datenschutz- und Publikationsregeln **je Ausschreibung** beachten. Insbesondere darf ein generativer Textentwurf nicht eingereicht werden, wenn der Wettbewerb dies untersagt.

## Dedup-Schlüssel und Normierung

Solange keine `OPP-*`-IDs vergeben werden, ist der Schlüssel das Tripel (normierte `official_url`, normierter `organizer`, normierte `call_round`). Für Speicherung und Vergleich wird es als JSON-Array aus drei Zeichenketten serialisiert (UTF-8, ohne Leerraum zwischen den Elementen, JSON-Standard-Escaping, Nicht-ASCII-Zeichen unescaped – entspricht `json.dumps(key, ensure_ascii=False, separators=(",", ":"))`), z. B. `["https://cheninstitute.org/prize","chen institute","2027"]`; ein bloßes Verketten mit Trennzeichen ist unzulässig, weil Freitexte das Trennzeichen enthalten können. Die Normierung ist deterministisch und wird in dieser Reihenfolge angewandt:

- `official_url`: (1) Schema und Host in Kleinbuchstaben; (2) Standardport des ursprünglichen Schemas entfernen (`:80` bei `http`, `:443` bei `https`); (3) Schema `http` wird zu `https`; (4) führendes `www.` entfernen; (5) Fragment (`#…`) entfernen; (6) Prozentkodierung in Pfad und Query auf Großbuchstaben-Hex vereinheitlichen; (7) Query-Parameter `utm_*`, `fbclid`, `gclid` entfernen, übrige Paare `name=wert` nach Name und bei gleichem Namen nach Wert sortieren (Zeichenkettenvergleich nach Unicode-Codepunkten, wiederholte Paare bleiben erhalten); (8) abschließenden `/` im Pfad entfernen (außer beim Wurzelpfad, der als leerer Pfad gilt). Die Groß- und Kleinschreibung des Pfads bleibt erhalten.
- `organizer`: Unicode-Normalform NFKC, `casefold`, alle Folgen von Leerraum (auch geschützte Leerzeichen) zu einem Leerzeichen, Anfang und Ende trimmen.
- `call_round`: als Zeichenkette, getrimmt; `null` wird zur leeren Zeichenkette.

Beispiel: `HTTP://www.ChenInstitute.org:80/prize/?utm_source=x#top` und `https://cheninstitute.org/prize` ergeben dieselbe URL `https://cheninstitute.org/prize`. Zwei Datensätze mit gleichem Schlüssel sind Duplikate; abweichende Pfade derselben Ausschreibung (z. B. Unterseiten) werden nicht automatisch zusammengeführt, sondern beim Screening geprüft.

## Testfall: Chen Institute & Science Prize 2027

```yaml
id: null                         # nicht vergeben – ID-Raum noch nicht freigegeben (siehe „ID-Vergabe“)
title: Chen Institute & Science Prize for AI Accelerated Research 2027
type: prize
organizer: Chen Institute       # laut Mitteilung; gegen offizielle Teilnahmebedingungen zu bestätigen
official_url: https://cheninstitute.org/prize
source_checked_at: null          # offizielle Teilnahmebedingungen noch nicht geprüft
status: screening
eligibility: unclear             # Gate erst nach Prüfung der offiziellen Bedingungen
eligibility_reason: "Offizielle Teilnahmebedingungen noch nicht mit Abrufdatum hinterlegt. Hinweis aus Issue #131 – möglicherweise formale akademische Voraussetzung, die individuell nicht erfüllt wäre; eine zulässige Partnerkonstellation wäre gesondert anhand der offiziellen Regeln zu prüfen."
eligibility_checked_at: null
projects: [knowledge-graph, noxia]   # IDs aus registry/projects.json
topics: [AI-accelerated research]
call_round: "2027"
owner: Thomas Küper (Projekt Owner)
effort: unknown
effort_note: Erst nach Prüfung der offiziellen Bedingungen abschätzbar.
assessment:                      # vor dem Eligibility-Gate alle unknown (Regel 3)
  research_fit: {rating: unknown, reason: ""}
  validation_level: {rating: unknown, reason: ""}
  benefit: {rating: unknown, reason: ""}
  visibility: {rating: unknown, reason: ""}
  collaboration_potential: {rating: unknown, reason: ""}
  ip_risk: {rating: unknown, reason: ""}
status_history:
  - {at: "2026-11-09", by: "Issue #131", from: null, to: discovered, reason: "Hinweis im Issue"}
  - {at: "2026-11-09", by: "Issue #131", from: discovered, to: screening, reason: "Referenzfall für Filterlogik"}
deadline_at: null                # Uhrzeit und Zeitzone nicht bestätigt
deadline_date: "2026-12-13"      # laut Mitteilung (Issue #131)
deadline_status: reported         # noch nicht an offiziellen Bedingungen bestätigt
evidence_refs: [https://github.com/thomaspeterkueper/kueper-ecosystem/issues/131]
next_action: Offizielle Teilnahmebedingungen abrufen, Abrufdatum eintragen, dann Eligibility-Gate entscheiden.
```

Dies ist ein **Schema-Beispiel**, noch kein Datensatz im Produktivsystem. Vor operativer Nutzung alle Anforderungen und Quellen neu prüfen.

## Schnittstellen- und Abnahmekriterien für die Umsetzung

- Ein kanonischer Speicherort wird vor Implementierung bestimmt; bestehendes Dashboard verwendet dessen API, keine lokale Kopie.
- Einlesen und Anzeigen von Opportunities mit Herkunft, letzter Prüfung, Zulassungsgrund und nächster Aktion.
- Filter nach `eligibility`, Projekt, Typ und Frist; unbekannte Fristen separat anzeigen.
- Tests für fehlende Abschlüsse, fehlende Primärquelle, abgelaufene/unklare Frist, Runden-Duplikate, Statusübergänge und Auditlog.
- Bestehende `external-tasks`-Spezifikation **nicht** durch Opportunity-Datensätze ersetzen.
