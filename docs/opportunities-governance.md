# Externe Forschungs- und Förderchancen – systemweiter Vertrag (Entwurf)

Status: proposal · Issue: [#131](https://github.com/thomaspeterkueper/kueper-ecosystem/issues/131) · Stand: 2026-11-09

## Zweck und Zuständigkeit

Dieses Dokument beschreibt den **gemeinsamen Metadatenvertrag** für Förderprogramme, Wettbewerbe, Kooperationen und Publikationsmöglichkeiten. Das Ecosystem ist die Source of Truth **für das Schema und die Zuständigkeitsregeln**, nicht für die operativen Chancenakten oder fachwissenschaftlichen Evidenzen. Eine spätere zentrale Übersicht konsumiert Daten aus der dafür benannten operativen Komponente; sie erzeugt keine zweite unabhängige Datenbank. Fachliche Forschungsbefunde bleiben in den zuständigen Projekten, Relationen im KG. Änderungen an anderen Repositories erfolgen gemäß `docs/cross-repository-workflow.md`.

## Opportunity v0.1 – Pflichtfelder

- `id`: stabile ID `OPP-YYYY-NNNN`, nach Vergabe unveränderlich
- `title`, `type`: `grant | prize | collaboration | publication`
- `organizer`, `official_url`, `source_checked_at`: Primärquelle und Zeitpunkt der Prüfung (ISO-8601)
- `status`: `discovered | screening | prioritized | preparing | submitted | awarded | rejected | archived`
- `eligibility`: `eligible | partner_required | ineligible | unclear`
- `eligibility_reason`: nachvollziehbarer Grund, kein bloßer Score
- `eligibility_checked_at`: Prüfdatum (ISO-8601)
- `projects`: Liste vorhandener Projekt-/Repository-IDs
- `owner`: verantwortliche Rolle oder Person für die nächste Entscheidung

Optionale Felder: `deadline_at` mit Zeitzone; `funding_amount` plus Währung; `country`; `language`; `partner_requirements`; `degree_requirements`; `publication_requirements`; `institution_requirements`; `residency_requirements`; `legal_form_requirements`; `allowed_ai_use`; `ip_terms`; `submission_url`; `evidence_refs` (kanonische IDs/URLs); `notes`; `next_action`; `last_reviewed_at`.

## Prüf- und Entscheidungsregeln

1. Vor Bewertung müssen **offizielle** Teilnahmebedingungen mit Abrufdatum hinterlegt werden. Die Einreichungsfrist wird als exakte lokale Zeit mit Zeitzone erfasst; ist sie nicht bekannt, `deadline_at` nicht erfinden.
2. **Eligibility ist ein Gate, keine gewichtete Punktzahl.** Fehlen Nachweise, ist der Status `unclear`; erforderlicher eigener Hochschulabschluss fehlt ⇒ `ineligible`, sofern es keine legitime alternative Bewerberkonstellation gibt. `partner_required` nur bei belegbar zulässiger kooperativer Bewerbung, nicht zur Umgehung von Regeln.
3. Erst danach: fachlicher Fit, Forschungs-/Validierungsreife, Aufwand, Frist, Nutzen, IP-Risiko und Sichtbarkeit als getrennte, dokumentierte Dimensionen beurteilen. Keine aggregierte Scheingenauigkeit ohne Kalibrierung.
4. Evidenzstatus strikt trennen: `idea | hypothesis | simulated | experimentally_tested | independently_replicated | peer_reviewed`. Eine Simulation ersetzt weder Messung noch unabhängige Replikation.
5. Projektbezüge nur als kanonische Referenzen. Duplikate über normierte `official_url` + Ausrichter + Ausschreibungsrunde prüfen; gleicher Preis in anderem Jahr ist nicht automatisch Duplikat.
6. Statuswechsel auditieren (wer, wann, von/nach, Begründung). Bewerbungen werden **nie** automatisch verschickt.
7. KI-Einsatz-, Urheber-, Datenschutz- und Publikationsregeln **je Ausschreibung** beachten. Insbesondere darf ein generativer Textentwurf nicht eingereicht werden, wenn der Wettbewerb dies untersagt.

## Testfall: Chen Institute & Science Prize 2027

`title`: Chen Institute & Science Prize for AI Accelerated Research 2027  
`type`: prize  
`official_url`: https://cheninstitute.org/prize  
`deadline_at`: **unklar bis zur Prüfung der offiziellen Uhrzeit und Zeitzone** (Mitteilung nennt 2026-12-13)  
`eligibility`: ineligible für individuelle Bewerbung ohne verlangten Abschluss  
`eligibility_reason`: akademische formale Voraussetzung nicht erfüllt; eine mögliche Partnerkonstellation wäre gesondert anhand der offiziellen Regeln zu prüfen  
`status`: screening  
`projects`: [kueper-knowledge-graph, noxiagame]  
`evidence_refs`: [https://github.com/thomaspeterkueper/kueper-ecosystem/issues/131]

Dies ist ein **Schema-Beispiel**, noch kein Datensatz im Produktivsystem. Vor operativer Nutzung alle Anforderungen und Quellen neu prüfen.

## Schnittstellen- und Abnahmekriterien für die Umsetzung

- Ein kanonischer Speicherort wird vor Implementierung bestimmt; bestehendes Dashboard verwendet dessen API, keine lokale Kopie.
- Einlesen und Anzeigen von Opportunities mit Herkunft, letzter Prüfung, Zulassungsgrund und nächster Aktion.
- Filter nach `eligibility`, Projekt, Typ und Frist; unbekannte Fristen separat anzeigen.
- Tests für fehlende Abschlüsse, fehlende Primärquelle, abgelaufene/unklare Frist, Runden-Duplikate, Statusübergänge und Auditlog.
- Bestehende `external-tasks`-Spezifikation **nicht** durch Opportunity-Datensätze ersetzen.
