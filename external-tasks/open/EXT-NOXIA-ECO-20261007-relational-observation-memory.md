---
id: EXT-NOXIA-ECO-20261007-relational-observation-memory
title: Relational Observation–Memory Architecture — Ecosystem anchor
status: open
source: NOXIA
target: ECO
created: 2026-10-07
requested_by: T.P.K.
priority: high
affects: [ECO, NOXIA, OTA, KG, OMNIZEDENZ]
supersedes: []
---

# Relational Observation–Memory Architecture

## Anlass

Mehrere zunächst getrennte NOXIA-Stränge konvergieren inzwischen auf dieselbe Architektur:

- epistemische Observationen mit Quelle, Zeitpunkt, Unsicherheit und Evidenz,
- relationale Spuren mit Provenienz und perspektivischer Rekonstruktion,
- lebende soziale Erinnerung,
- Schlaf und deterministische Konsolidierung,
- Kreativitäts- und Cognition-Modi,
- verteilte Beobachtung durch NPCs, Sensoren, Fahrzeuge und externe Datenquellen.

Die Konvergenz ist projektübergreifend relevant und darf nicht als zweites NPC-Gedächtnissystem implementiert werden.

## Gemeinsamer Zyklus

```text
world event / interaction
  -> observation / trace
  -> provenance
  -> actor-scoped memory
  -> consolidation / decay / forgetting
  -> reconstruction
  -> cognition
  -> decision / action
  -> new event / interaction
```

## Architekturentscheidung

NOXIA soll bestehende Komponenten zusammenführen statt parallelisieren:

1. Observation ist die gemeinsame Eingangsgrenze für Wissen.
2. Provenienz bleibt über Kommunikation und Erinnerung erhalten.
3. Memory ist perspektivisch; eine erinnerte Behauptung ist nicht automatisch Weltwahrheit.
4. Schlaf/Konsolidierung gehört in den vorhandenen `personCognition`-Pfad.
5. Relationale Rekonstruktion ergänzt diesen Pfad um `determined / open / excluded`, Herkunft und Widerspruch.
6. Bereits materialisierte kausale Folgen werden durch spätere Rekonstruktion nicht rückwirkend verändert.
7. Routinepfade bleiben deterministisch und billig; externe Inferenz ist Eskalation, nicht Grundbetrieb.

## Wichtige begriffliche Korrektur

Der bestehende Ausdruck **Ground Truth** im Epistemic Observation Contract ist für die Engine nur als *kanonischer, bereits materialisierter Simulationszustand* zulässig.

Er soll **nicht** bedeuten, dass jedes noch offene Detail hinter der Simulation bereits vollständig bestimmt vorliegt.

Damit bleiben zwei Ebenen getrennt:

- **engine authority:** Zustände/Folgen, die für Konsistenz bereits kanonisch materialisiert sind;
- **epistemic openness:** Details, die für einen Akteur oder für die Simulation noch nicht relational bestimmt wurden.

## Forschungswert

Die Architektur ist zugleich ein experimenteller Rahmen für:

- soziale Epistemologie und Gerüchte-Provenienz,
- Gedächtnisfehler und Rekonstruktion,
- institutionelle Wissensbildung,
- verteilte Sensorfusion,
- Lernen/Kreativität bei begrenztem Compute,
- die Frage, welche Aspekte einer relationalen Ontologie in einer ausführbaren Simulation kohärent modellierbar sind.

NOXIA ist dabei **Testbett, nicht Beweis fundamentaler Physik**.

## Routing

- **NOXIA:** ausführbare Architektur und Experimente.
- **OTA:** neutrales Forschungsdossier / Paper-Entwurf.
- **KG:** Begriffe und Relationen (Observation, Trace, Provenance, Reconstruction, Consolidation, Openness).
- **Omnizedenz/AVI:** ontologische und physikalische Hypothesen; Bell/CHSH/I3322 bleiben getrennte Fundamentaltests.
- **ECO:** Cross-Project-Governance und Vermeidung konkurrierender Implementierungen.

## Nächster technischer Schritt

PR #431 nicht als isolierte Prompt-Memory-Schicht behandeln. Vor Merge gegen Observation, `person_memories`, `personCognition` und relationale Runtime reconciliieren.
