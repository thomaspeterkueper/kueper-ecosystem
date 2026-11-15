# Energy Grid Layer – Programmregistrierung

Status: registriert (2026-11-15)  
Repository: `kueper-ecosystem`  
Registrierung: [`EXT-ENG-ECO-20260925-energy-grid-learning-routing`](../../external-tasks/done/EXT-ENG-ECO-20260925-energy-grid-learning-routing.md)  
Betroffene Codes: `ECO`, `ENG`, `KG`, `NXU`, `NOXIA`, `OTA`; Lernpfad `SSF`  
Ausdrücklich zurückgestellt: `noxia-realtime`

## 1. Zweck

Das Programm bündelt die Energienetz-Schicht und das zugehörige Lernmodul über
mehrere Repositories: wie reale Netzforschung belegt, als Energie- und
Lernkonzepte modelliert, als Kapazitäts- und Simulationsvertrag festgelegt, in
der Geschichte des Kanons entwickelt und im Spiel als Netzbetrieb und
Lernszenario erfahrbar wird.

Kern ist die Trennung der Größen, die im Alltag oft vermischt werden:
installierte und verfügbare Erzeugung, Anschluss- und Übertragungskapazität,
Speicherleistung und -energie, Reserve, Nachfrage und tatsächlich lieferbare
Leistung (`ENG-SYS-EGCA-0001`).

## 2. Geltungsbereich

| Baustein | Bedeutung im Programm |
|---|---|
| Kapazität | Erzeugung, Netzübertragung, Speicher, Reserve und lieferbare Leistung als getrennte Größen |
| Engpässe | Netzengpass, Abregelung, flexible Lasten und Lastklassen |
| Inselbetrieb | Microgrids, Inselbetrieb und Schwarzstart |
| Profile | Terrestrische, lunare, Mars- und Orbitalprofile; standortspezifische Werte bleiben im Projekt |
| Lernmodul | Lernszenarien in NOXIA, Lernpfad in SSF; Lernfortschritt bleibt SSF |

## 3. Zuständigkeiten

| Domäne | Zuständigkeit | Beitrag |
|---|---|---|
| `kueper-ecosystem` (`ECO`) | Systemweite Governance | Programmregistrierung, Zuständigkeitsverteilung, Querverweise |
| `kueper-engineering` (`ENG`) | Systemarchitektur | Physische und Systemarchitektur, Simulations- und Kapazitätsverträge |
| `overtime-archive.org` (`OTA`) | Evidenz | Belege, Provenienz und aktuelle reale Netzforschung |
| `kueper-knowledge-graph` (`KG`) | Ontologie und kanonische IDs | Energie- und Lernkonzepte und ihre Relationen |
| `noxia-universe` (`NXU`) | Kanon | Historische und weltbauliche Folgen der Netzentwicklung |
| `noxiagame` (`NOXIA`) | Spiel und Lernen | Gameplay, UX, Balancing und Lernszenarien; keine kanonischen Definitionen |
| `solarsciencefoundation` (`SSF`) | Lernpfad | Didaktische Vermittlung und Lernfortschritt |
| `noxia-realtime` | – | Visualisierung und Laufzeitintegration erst nach stabilen Verträgen; derzeit nicht adressiert |

## 4. Stand der Folgearbeiten

Die Folgearbeiten wurden bereits ab dem 25.09.2026 in die Ziel-Repositories
geroutet. Diese Registrierung legt sie zusammen und erzeugt keine doppelten Aufträge.

| Code | External Task | Stand (15.11.2026) |
|---|---|---|
| `ENG` | `kueper-engineering/external-tasks/done/EXT-NOXIA-ENG-20260925-energy-grid-capacity-architecture.md` | erledigt: `ENG-SYS-EGCA-0001` (`systems/energy-grid-capacity-architecture-r1.md`, `systems/energy-grid-capacity-interface-r1.json`) |
| `KG` | `kueper-knowledge-graph/external-tasks/done/EXT-ENG-KG-20260925-energy-grid-learning-ontology.md` | erledigt: Energy Grid and Learning Scenario Ontology (`exports/ontology-energy-grid-learning-0.1.json`) |
| `OTA` | `overtime-archive.org/external-tasks/done/EXT-ENG-OTA-20260925-grid-congestion-curtailment-dossier.md` | erledigt: `OTA-SCI-0109-2026-DE` |
| `NXU` | `noxia-universe/external-tasks/open/EXT-ENG-NXU-20260925-energy-grid-evolution.md` | offen |
| `NXU` | `noxia-universe/external-tasks/open/EXT-ENG-NXU-20260928-energy-grid-capacity-integration.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-ENG-NOX-20260925-energy-grid-layer-learning-module.md` | offen |
| `SSF` | `solarsciencefoundation/external-tasks/open/EXT-ENG-SSF-20260928-energy-grid-capacity-learning-module.md` | offen |

## 5. Querverweise zu Nachbarprogrammen

| Nachbarprogramm | Referenz | Verhältnis |
|---|---|---|
| Robotik / MiniNode | [`robotics-mininode.md`](robotics-mininode.md) | Laden und Energiebedarf der Knoten innerhalb der Kapazitätsgrenzen |
| Adaptive Industry | [`adaptive-industry.md`](adaptive-industry.md) | Energie- und Wärmekapazität begrenzt die Fertigungsplanung; ungeklärte Kapazität führt zu fail-closed |
| Gebäude und Siedlungen | Mars Settlement Systems Kernel ([`mars-settlement-kernel.md`](mars-settlement-kernel.md)); [`living-infrastructure.md`](living-infrastructure.md) | Energie als gemeinsamer Fluss der Siedlung; keine doppelten Ressourcenzähler |
| Bergbau und Ressourcen | ENG `ENG-SYS-PRR-0001` (`systems/planetary-resource-reconnaissance-architecture-0.1.md`) | Energiebedarf von Erkundung, Abbau und Aufbereitung |
| Transport und Logistik | ENG `ENG-SYS-STL-0001` (`systems/solar-transfer-logistics-architecture-0.2.md`) | Energiebedarf und Ladeinfrastruktur von Transport |

## 6. Regeln und Abgrenzungen

- Keine neue Source of Truth. Die Zuständigkeiten aus
  [`docs/source-of-truth.md`](../source-of-truth.md) bleiben unverändert.
- Föderierte Zuständigkeit: Jede Domäne liegt in genau einem Repository;
  Änderungen anderswo laufen als External Tasks.
- Standortspezifische Werte (Kapazitäten, Lastprofile, Speichergrößen) sind
  keine universellen Konstanten und bleiben in `kueper-engineering` bzw. im
  jeweiligen Projekt.
- Lernfortschritt bleibt in `solarsciencefoundation`; NOXIA-Lernszenarien
  konsumieren KG-Ontologie und ENG-Verträge.
- `noxia-realtime` wird erst adressiert, wenn stabile Verträge existieren.
