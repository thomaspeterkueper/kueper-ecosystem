# Adaptive Industry – Programmregistrierung

Status: registriert (2026-11-15)  
Repository: `kueper-ecosystem`  
Registrierung: [`EXT-NOXIA-ECO-20260925-adaptive-industry-routing`](../../external-tasks/done/EXT-NOXIA-ECO-20260925-adaptive-industry-routing.md)  
Betroffene Codes: `ECO`, `ENG`, `KG`, `NXU`, `NOXIA`, `OTA`  
Ausdrücklich zurückgestellt: `noxia-realtime`

## 1. Zweck

Das Programm bündelt adaptive Fertigung, digitale Zwillinge und Physical AI
über mehrere Repositories: wie reale industrielle Fähigkeiten belegt, als
Entitäten und Zustände modelliert, als Anlagen-, Zwillings- und
Steuerungsarchitektur festgelegt, in der Geschichte des Kanons entwickelt und
im Spiel als Produktion und Lernmodul erfahrbar werden.

## 2. Geltungsbereich

| Baustein | Bedeutung im Programm |
|---|---|
| Anlage und Steuerung | Physische Anlage, Sensorik/Aktorik, deterministische Steuerung, Fertigungsbetrieb |
| Digitaler Zwilling | Zustandsschätzung mit Aktualität, Unsicherheit und Abweichung von der Realität |
| Physical AI | Planung und Optimierung oberhalb der Steuerung; KI beratend/überwachend, ohne implizites Recht, Sicherheitsgrenzen zu übersteuern |
| Material und Qualität | Materialprovenienz, Bestandsabgleich, Qualität, Wartung, energiebewusste Planung |
| Rekonfiguration | Validierungsklassen für Umbauten; Betrieb im degradierten oder getrennten Zustand |
| Produktions-Gameplay | Produktion, UX, Balancing und Lernmodul in NOXIA |

## 3. Zuständigkeiten

| Domäne | Zuständigkeit | Beitrag |
|---|---|---|
| `kueper-ecosystem` (`ECO`) | Systemweite Governance | Programmregistrierung, Zuständigkeitsverteilung, Querverweise |
| `overtime-archive.org` (`OTA`) | Evidenz | Reifegrad, Belege und Provenienz; Hersteller-Roadmaps getrennt von realen Fähigkeiten |
| `kueper-knowledge-graph` (`KG`) | Ontologie und kanonische IDs | Industrielle Entitäten, Zustände und Relationen |
| `kueper-engineering` (`ENG`) | Systemverträge | Anlagen-, Zwillings- und Steuerungsarchitektur und Schnittstellen |
| `noxia-universe` (`NXU`) | Kanon | Historische, soziale und außerirdische Entwicklung der Industrie |
| `noxiagame` (`NOXIA`) | Spiel und Lernen | Produktions-Gameplay, UX, Balancing, Lernmodul; keine kanonischen Definitionen |
| `noxia-realtime` | – | spätere Visualisierung und Laufzeitintegration erst nach stabilen Verträgen; derzeit nicht adressiert |

## 4. Stand der Folgearbeiten

Die Folgearbeiten wurden bereits ab dem 25.09.2026 in die Ziel-Repositories
geroutet. Diese Registrierung legt sie zusammen und erzeugt keine doppelten Aufträge.

| Code | External Task | Stand (15.11.2026) |
|---|---|---|
| `OTA` | `overtime-archive.org/external-tasks/done/EXT-NOXIA-OTA-20260925-adaptive-factory-physical-ai-dossier.md` | erledigt: `OTA-SCI-0110-2026-DE` |
| `KG` | `kueper-knowledge-graph/external-tasks/done/EXT-OTA-KG-20260925-adaptive-manufacturing-ontology.md` | erledigt: `ONT:KG:ADAPTIVE-MANUFACTURING-0.1` (`exports/ontology-adaptive-manufacturing-0.1.json`) |
| `ENG` | `kueper-engineering/external-tasks/done/EXT-NOXIA-ENG-20260925-adaptive-factory-control-architecture.md` | erledigt: `ENG-SYS-AFCA-0001` (`systems/adaptive-factory-control-architecture-r1.md`, `systems/adaptive-factory-control-interface-r1.json`) |
| `NXU` | `noxia-universe/external-tasks/open/EXT-ENG-NXU-20260925-adaptive-manufacturing-evolution.md` | offen |
| `NXU` | `noxia-universe/external-tasks/open/EXT-ENG-NXU-20260928-adaptive-factory-control-integration.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-ENG-NOX-20260925-adaptive-factory-gameplay-learning.md` | offen |

## 5. Querverweise zu Nachbarprogrammen

| Nachbarprogramm | Referenz | Verhältnis |
|---|---|---|
| Energy Grid Layer | `external-tasks/open/EXT-ENG-ECO-20260925-energy-grid-learning-routing.md`; ENG `ENG-SYS-EGCA-0001` (`systems/energy-grid-capacity-architecture-r1.md`) | Energie- und Wärmekapazität begrenzt die Fertigungsplanung; ungeklärte Kapazität führt zu fail-closed |
| MiniNode / Roboterschwarm | [`robotics-mininode.md`](robotics-mininode.md); ENG `ENG-SYS-MININODE-0001` (`systems/mininode-robot-swarm-platform-r1.md`) | Anbindung über Fähigkeits-, Energie- und Zustandsverträge |
| Bergbau und Ressourcen | ENG `ENG-SYS-PRR-0001` (`systems/planetary-resource-reconnaissance-architecture-0.1.md`) | Rohstoffe und Materialidentität am Eingang der Fertigung |
| Logistik | ENG `ENG-SYS-STL-0001` (`systems/solar-transfer-logistics-architecture-0.2.md`) | Material- und Teilefluss zwischen Standorten |
| Gebäude und Siedlungen | Mars Settlement Systems Kernel ([`mars-settlement-kernel.md`](mars-settlement-kernel.md)); [`living-infrastructure.md`](living-infrastructure.md) | Fertigung nutzt gemeinsame Reservoire und Flüsse der Siedlung; keine doppelten Ressourcenzähler |
| NOXIA-Lernmodulfamilie | NOXIA-Task oben; `solarsciencefoundation` für Lernpfade | Lernmodule konsumieren KG-Ontologie und ENG-Verträge; Lernfortschritt bleibt SSF |

## 6. Regeln und Abgrenzungen

- Keine neue Source of Truth. Die Zuständigkeiten aus
  [`docs/source-of-truth.md`](../source-of-truth.md) bleiben unverändert.
- Föderierte Zuständigkeit: Jede Domäne liegt in genau einem Repository;
  Änderungen anderswo laufen als External Tasks.
- Standortspezifische Werte (Durchsatz, Prozessfenster, Energie- und
  Wärmebudgets, Personal) sind keine universellen Konstanten und bleiben in
  `kueper-engineering` bzw. im jeweiligen Projekt.
- Epistemische Regel: physischer Zustand ≠ Sensorbeobachtung ≠
  Zwillingsschätzung ≠ Akteurswissen.
- `noxia-realtime` wird erst adressiert, wenn stabile Verträge existieren.
