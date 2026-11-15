# System Map

Status: draft  
Repository: `kueper-ecosystem`

## 1. Zweck der Systemkarte

Diese Systemkarte beschreibt die oberste Struktur des KUEPER-Projektverbunds. Sie dient als Orientierung für Menschen und KI-Assistenten, bevor in einzelnen Repositories gearbeitet wird.

## 2. Grundmodell

```text
kueper-ecosystem
  |
  |-- definiert systemweite Architektur, Governance und Zuständigkeiten
  |
  v
kueper-knowledge-graph
  |
  |-- verwaltet semantische Entitäten, Relationen, Domains, Mappings und Exporte
  |
  +--> kueper.com
  |      öffentliche wissenschaftliche Archiv- und Publikationsschicht
  |
  +--> solarsciencefoundation
  |      Lernmodule, Lernpfade, Übungen, Fortschritt, API
  |
  +--> noxiagame
  |      spielerische Anwendung und Simulation
  |
  +--> overtime-archive.org
         werkbezogene Real/Fiction-Schicht

thomas-kueper.de
  |
  |-- öffentliche Autoren-, Werk- und Philosophieplattform
```

## 3. Rollen der Ebenen

### Governance-Ebene

`kueper-ecosystem` beschreibt, welche Regeln gelten.

Beispiele:

- Repository-Zuständigkeiten
- Source-of-Truth-Regeln
- Cross-Repository-Workflow
- ID- und Metadatenkonventionen
- Architekturentscheidungen

### Semantische Ebene

`kueper-knowledge-graph` beschreibt, wie Wissen, Entitäten und Systeme zusammenhängen.

Beispiele:

- Knowledge Domains
- Entitäten
- Relationen
- KXF-Exporte
- systemübergreifende Mappings

### Archiv- und Publikationsebene

`kueper.com` veröffentlicht und archiviert wissenschaftlich oder methodisch relevante Grundlagen. Es bleibt werkneutral und universumsunabhängig.

### Lern- und Vermittlungsebene

`solarsciencefoundation` übersetzt Wissen in didaktische Module, Lernpfade, Übungen und Fortschrittszustände.

### Anwendungsebene

`noxiagame` nutzt Wissen, Lernfortschritt und Konzepte spielerisch.

### Autoren- und Werkebene

`thomas-kueper.de` bündelt Autor, Werke, Philosophie, Projektseiten und öffentliche Darstellung.

### Fiktionale Archiv- und Anwendungsschicht

`overtime-archive.org` erlaubt werkbezogene und fiktionale Kontexte, sofern sie korrekt auf reale Grundlagen und KUE/KG-Bezüge verweisen.

## 4. Verweisrichtungen

Grundregel:

```text
Governance -> Graph -> Archiv/Lernen/Anwendung
```

Praktisch:

- `kueper-ecosystem` darf systemweite Regeln für alle Repositories definieren.
- `kueper-knowledge-graph` darf auf systemweite Regeln referenzieren und semantische Mappings anbieten.
- `kueper.com` darf auf KG- oder Ecosystem-Regeln verweisen, bleibt aber fachlich werkneutral.
- `solarsciencefoundation` darf Wissen didaktisch transformieren.
- `noxiagame` darf Wissen spielerisch anwenden.
- `overtime-archive.org` darf fiktionale Kontexte auf reale Grundlagen zurückführen.

## 5. Cross-Repository-Programme

Cross-Repository-Programme bündeln Zuständigkeiten mehrerer Repositories, ohne die
Source-of-Truth-Grenzen zu verschieben. Registrierung und Querverweise liegen in
[`docs/programs/README.md`](programs/README.md).

| Programm | Rolle | Registrierung |
|---|---|---|
| Living Infrastructure | Integrationsschicht für Mykologie/Bodenökologie, geschlossene Lebenserhaltung, Landwirtschaft, Abfall/Recycling, Planetare Evolution und künftige Ecopoiesis | [`docs/programs/living-infrastructure.md`](programs/living-infrastructure.md) |
| Mykologie / Bodenökologie / Ecopoiesis | Fachdomäne Pilze, Myzel, Bodenleben und kontrollierte Ecopoiesis; nutzt die Flüsse von Living Infrastructure | [`docs/programs/mycology-soil-ecopoiesis.md`](programs/mycology-soil-ecopoiesis.md) |
| Planetary Evolution / Geosphäre–Biosphäre | Gekoppelte Entwicklung von Geo-, Hydro-, Atmo- und Biosphäre über Deep Time; Evidenz, Kanon, Generierung und Rekonstruktion | [`docs/programs/planetary-evolution.md`](programs/planetary-evolution.md) |
| Planetare Fernerkundung / Beobachtende Astronomie | Erkenntniskette von der physikalischen Eigenschaft über Messung bis zur Schlussfolgerung; Instrumente, Entdeckungsgeschichte, Beobachtungs-Gameplay | [`docs/programs/planetary-remote-sensing.md`](programs/planetary-remote-sensing.md) |
| Planetensystem-Architekturen (nicht-koplanar/retrograd) | Bahnebenen, Neigungen und rückläufige Umläufe von der Evidenz über Kanon und Bahnmechanik bis zu Generierung und Lernmodul | [`docs/programs/planetary-architecture.md`](programs/planetary-architecture.md) |
| Adaptive Industry | Adaptive Fertigung, digitale Zwillinge und Physical AI von der Evidenz über Anlagen- und Steuerungsarchitektur bis zu Produktions-Gameplay | [`docs/programs/adaptive-industry.md`](programs/adaptive-industry.md) |
| Mars Settlement Systems Kernel | Integrationsinstanz für Siedlungssysteme: gemeinsame Reservoire und Flüsse für Energie, ECLSS/Wasser, Biologie, Landwirtschaft, Abfall, Industrie, Logistik und Robotik | [`docs/programs/mars-settlement-kernel.md`](programs/mars-settlement-kernel.md) |
| Robotik / MiniNode | Familie interoperabler autonomer Roboterknoten von der Evidenz über Ontologie und Systemarchitektur bis zu Kanon, Gameplay und realem Prototypenpfad | [`docs/programs/robotics-mininode.md`](programs/robotics-mininode.md) |

## 6. Nicht-Ziele dieser Systemkarte

Diese Datei entscheidet noch nicht im Detail über:

- konkrete ID-Formate,
- konkrete KXF-Schemas,
- konkrete Lernmodul-Strukturen,
- konkrete NOXIA-Unlock-Regeln,
- konkrete Publikationsregeln für einzelne Dokumente.

Diese Themen erhalten eigene Dokumente oder Architekturentscheidungen.
