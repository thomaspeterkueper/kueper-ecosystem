---
id: EXT-ENG-ECO-20261002-kueper-products-bootstrap
title: Eigenständiges Projekt und Repository kueper-products etablieren
status: parked
source: ENG
target: ECO
created: 2026-10-02
requested_by: T.P.K.
priority: high
affects: [ECO, ENG, PRODUCTS, SSF, OTA, KG, NOXIA]
supersedes: []
---

# EXT-ENG-ECO-20261002-kueper-products-bootstrap — Eigenständiges Projekt und Repository kueper-products etablieren

## Anlass

KUEPER Engineering hat begonnen, einen formalen Pfad von Forschungsergebnissen zu nutzbaren Produkten zu definieren. Dabei wurde deutlich, dass reale Produktentwicklung eine eigene Verantwortung benötigt und nicht als Unterordner von Engineering geführt werden sollte.

Der neue Bereich soll ausdrücklich nicht auf Raumfahrt-, Forschungs- oder Hochtechnologieprodukte beschränkt sein. Besonders wichtig sind kleine, tatsächlich herstellbare Produkte für täglichen Bedarf, Haushalt, Handwerk, Werkstatt, Garten, Reparatur, Energie, Textilien und kleine Robotik.

## Gewünschte Änderung

Bitte ein eigenständiges Projekt und GitHub-Repository `kueper-products` als neues Mitglied des KUEPER-Ökosystems etablieren.

Vorgeschlagene Source-of-Truth-Rolle:

**KUEPER Products ist Source of Truth für Produktentdeckung, Produktportfolio, reale Nutzer-/Anwendungsprobleme, Produktanforderungen, Produktfamilien, Gebrauchstauglichkeit, Produktvarianten sowie den Übergang von validierter Technik zu pilotierbaren und produzierbaren realen Produkten.**

Abgrenzung:

- SSF: wissenschaftliche Grundlagen und Lerninhalte
- KUEPER Engineering: technische Entwicklung, Berechnung, Architektur, Prototypen, Verifikation und technische Baselines
- KUEPER Products: Produktidee, Zielnutzer, Alltagseinsatz, Produktdefinition, Varianten, Produkt-BOM/Assembly-Konzept, Sourcing, Zielkosten, Bedienbarkeit, Service, Verpackung, Compliance-/Zertifizierungsplanung und Produktreife
- OTA/KG: kanonische technische Wissensobjekte und Relationen
- NOXIA: Gameplay und Runtime
- kueper-ecosystem: Governance und Repository-Rollen

Vorgeschlagener initialer Repository-Aufbau:

- `README.md`
- `PROJECT-BRIEF.md`
- `opportunities/`
- `products/`
- `families/`
- `small-products/`
- `household/`
- `workshop/`
- `garden/`
- `energy/`
- `textiles/`
- `robotics/`
- `prototypes/`
- `manufacturing/`
- `costing/`
- `compliance/`
- `service/`
- `research-watch/`
- `templates/`
- `external-tasks/open/`
- `external-tasks/done/`
- `external-tasks/rejected/`

Eigene Produktidentitäten sollen eingeführt werden, aber ausdrücklich **nicht** `ENG-*`, OTA-, KG-, SSF- oder NOXIA-Identitäten wiederverwenden. Präfix und Registry-Regel sind durch ECO festzulegen.

## Erste Produkttracks

Das neue Projekt soll von Beginn an zwei gleichberechtigte Skalen führen:

### A. Small Products / Everyday

Kleine Produkte mit kurzer Strecke von Problem zu Prototyp, zum Beispiel:

- Haushaltshelfer und Aufbewahrung
- Reparatur- und Wartungshilfen
- einfache Werkstattvorrichtungen und Messhilfen
- modulare Halterungen, Adapter und Verbindungselemente
- energiearme Sensoren und Warngeber
- Wasser-, Feuchte-, Temperatur- und Luftqualitätsprodukte
- Garten- und Bewässerungshilfen
- robuste Textil-/Taschen-/Schutzlösungen
- ergonomische Alltagshilfen
- kleine modulare Robotik- oder MiniNode-Produkte
- Ersatzteil-, Reparatur- und Circular-Design-Produkte

Ziel ist bewusst nicht nur High-Tech. Auch ein mechanisch einfaches Produkt ist wertvoll, wenn es ein reales Problem besser, reparierbarer, langlebiger oder ressourcenschonender löst.

### B. Advanced Products

Aus Forschung und Engineering abgeleitete Systeme, etwa:

- Photophorese-/Knudsen-Plattformen
- Muographie
- Prospektionssysteme
- verteilte Sensor-/Radioastronomie-Knoten
- MiniNode-Schwärme
- funktionale/smarte Textilien
- spätere Raumfahrt- oder Planetentechnik

## Produktprinzipien

Das Projekt sollte mindestens folgende Leitlinien übernehmen:

1. Problem vor Technologie.
2. Klein und baubar ist genauso wertvoll wie spektakulär.
3. Reparierbarkeit und Lebensdauer sind Designparameter.
4. Standardteile und lokale Fertigbarkeit werden bevorzugt, wenn technisch sinnvoll.
5. Prototypen sollen möglichst früh physisch testbar sein.
6. Keine Scheingenauigkeit bei Kosten oder Leistungswerten.
7. Technik-Push aus Forschung ist erlaubt, benötigt aber immer einen realen Use Case.
8. Negative Produktentscheidungen werden dokumentiert.
9. Modularität und Produktfamilien werden bevorzugt, wenn dadurch echte Wiederverwendung entsteht.
10. Engineering- und Produktidentität bleiben getrennt.

## Begründung

Die Produktperspektive ist eine eigene Disziplin. Engineering beantwortet primär, ob und wie etwas technisch funktioniert. Products muss beantworten, ob daraus ein gutes reales Produkt für einen konkreten Nutzer wird.

Diese Trennung verhindert zugleich, dass KUEPER Engineering zum Gemischtwaren-Repository für Markt-, Nutzer-, Verpackungs-, Kosten- und Produktportfoliofragen wird.

## Betroffene Repositories

- `kueper-ecosystem`
- zukünftiges `kueper-products`
- `kueper-engineering`
- später über External Tasks auch SSF, OTA, KG und NOXIA

## Erwartetes Ergebnis

Erledigt ist der Task, wenn:

- `kueper-products` als eigenes Repository angelegt ist;
- die Source-of-Truth-Rolle in der Ecosystem-Dokumentation definiert ist;
- ein PROJECT-BRIEF mit den oben beschriebenen Grenzen existiert;
- External-Task-Verzeichnisse eingerichtet sind;
- eine eigene Produkt-ID-Konvention beschlossen ist;
- ein Template für Produktkandidaten existiert;
- ein Small-Products-/Everyday-Backlog existiert;
- ein Research-to-Product-Backlog existiert;
- die Engineering↔Products-Handoff-Regel dokumentiert ist.

## Hinweise

KUEPER Engineering PR #96 wurde nach dieser Entscheidung bereits so korrigiert, dass Engineering kein eigenes Produktportfolio mehr besitzen soll.

## Stand 13.11.2026 (Ökosystem-Kreislauf, Claude)

Claude-Status: wartet auf Thomas

Im Ecosystem bereits erfüllt:

- Registrierung als Projekt `products`, Code `PROD`, Rolle `productization` mit Source-of-Truth-Beschreibung und Pflichtpfaden (`registry/projects.json`, `decisions/ECO-ARC-0035-2026-DE.md`).
- Source-of-Truth-Grenzen und Engineering↔Products-Abgrenzung samt Product-Potential-Gate: `docs/architecture/KUEPER_PRODUCTS_ROUTING.md`.

Offen – liegt überwiegend in `kueper-products` selbst (PROJECT-BRIEF, External-Task-Verzeichnisse, Produktkandidaten-Template, Small-Products- und Research-to-Product-Backlog). Dieser Lauf hat keinen Zugriff auf das Repository und kann nicht sehen, ob es schon existiert. Neu anlegen darf der Kreislauf kein Repository.

Offen – Entscheidung: die eigene Produkt-ID-Konvention („durch ECO festzulegen“). Dafür gibt es bisher keine Entscheidung und keinen Entwurf.

## Rückfrage

1. Gibt es `thomaspeterkueper/kueper-products` schon? Wenn ja: bitte für die Claude-Läufe freigeben – dann werden die fehlenden Grundstrukturen dort als eigener Branch angelegt. Wenn nein: bitte selbst anlegen (leer genügt).
2. Produkt-ID: Vorschlag `PROD-NNNN` (fortlaufend, ohne Familien-Kürzel im Kennzeichen; Familie und Skala Small/Advanced als Felder), festgehalten als Entscheidung ECO-ARC im Ecosystem. Antwort „ja“ genügt, sonst bitte das gewünschte Muster nennen.

