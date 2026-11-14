# Mars Settlement Systems Kernel – Programmregistrierung

Status: registriert (2026-11-15)  
Repository: `kueper-ecosystem`  
Registrierung: [`EXT-NOXIA-ECO-20260927-mars-settlement-kernel-routing`](../../external-tasks/done/EXT-NOXIA-ECO-20260927-mars-settlement-kernel-routing.md)  
Betroffene Codes: `ECO`, `ENG`, `KG`, `NXU`, `NOXIA`, `OTA`  
Ausdrücklich zurückgestellt: `noxia-realtime` (später Konsument stabiler Verträge)

## 1. Zweck

Der Mars Settlement Systems Kernel ist die Integrationsinstanz für
Siedlungssysteme. Er verbindet die Fachprogramme, die in einer Siedlung
dieselben Stoffe, Energien und Kapazitäten nutzen, zu einem gemeinsamen Netz
aus Reservoiren, Prozessen und kapazitätsbegrenzten Verbindungen – statt
vieler isolierter Ressourcenanzeigen.

Die Integrationsinstanz ist eine Governance-Rolle: Die fachliche Festlegung
der Flüsse und Prozessverträge bleibt in `kueper-engineering`
(`ENG-SYS-MSSK-0001`).

## 2. Verbundene Systeme

| System | Registrierung bzw. Referenz |
|---|---|
| Energy Grid | `external-tasks/open/EXT-ENG-ECO-20260925-energy-grid-learning-routing.md`; ENG `ENG-SYS-EGCA-0001` (`systems/energy-grid-capacity-architecture-r1.md`) |
| ECLSS / Wasser | ENG `ENG-SYS-ECLSS-0001` (`systems/eclss-core-family-r1.md`, `systems/eclss-conserved-flow-contract-r1.json`) |
| Living Infrastructure / Mykologie | [`living-infrastructure.md`](living-infrastructure.md); [`mycology-soil-ecopoiesis.md`](mycology-soil-ecopoiesis.md) |
| Landwirtschaft, Abfall/Recycling | als Bausteine in [`living-infrastructure.md`](living-infrastructure.md) geführt; noch kein eigenes Programm |
| Adaptive Industry | [`adaptive-industry.md`](adaptive-industry.md); ENG `ENG-SYS-AFCA-0001` |
| Logistik | ENG `ENG-SYS-STL-0001` (`systems/solar-transfer-logistics-architecture-0.2.md`) |
| MiniNodes / Robotik | `external-tasks/open/EXT-ENG-ECO-20260924-robotics-program-routing.md`; ENG `ENG-SYS-MININODE-0001` (`systems/mininode-robot-swarm-platform-r1.md`) |
| Planetare Randbedingungen | [`planetary-evolution.md`](planetary-evolution.md) |

## 3. Zuständigkeiten

| Domäne | Zuständigkeit | Beitrag |
|---|---|---|
| `kueper-ecosystem` (`ECO`) | Systemweite Governance | Registrierung als Integrationsinstanz, Zuständigkeitsverteilung, Querverweise |
| `kueper-engineering` (`ENG`) | Systemverträge | Konservierte Flüsse, Prozessverträge, Resilienz und Fidelität |
| `kueper-knowledge-graph` (`KG`) | Ontologie und kanonische IDs | Kanonische Entitäten, Relationen und Einheiten |
| `overtime-archive.org` (`OTA`) | Evidenz | Empirische Kalibrierung und Provenienz |
| `noxia-universe` (`NXU`) | Kanon | Siedlungsgeschichte, Institutionen und Kultur |
| `noxiagame` (`NOXIA`) | Spiel und Lernen | Simulation, Balancing, UX und Lernmodul; keine kanonischen Definitionen |
| `noxia-realtime` | – | späterer Konsument stabiler Verträge; derzeit nicht adressiert |

## 4. Stand der Folgearbeiten

Die Folgearbeiten wurden bereits ab dem 27.09.2026 in die Ziel-Repositories
geroutet. Diese Registrierung legt sie zusammen und erzeugt keine doppelten Aufträge.

| Code | External Task | Stand (15.11.2026) |
|---|---|---|
| `ENG` | `kueper-engineering/external-tasks/done/EXT-NOXIA-ENG-20260927-mars-settlement-systems-kernel.md` | erledigt: `ENG-SYS-MSSK-0001` (`systems/mars-settlement-systems-kernel-r1.md`, `systems/mars-settlement-systems-kernel-interface-r1.json`) |
| `KG` | `kueper-knowledge-graph/external-tasks/done/EXT-ENG-KG-20260927-settlement-systems-kernel-ontology.md` | erledigt: `ONT:KG:SETTLEMENT-SYSTEMS-KERNEL-0.1` |
| `KG` | `kueper-knowledge-graph/external-tasks/done/EXT-ENG-KG-20260928-mars-settlement-systems-kernel-relations.md` | erledigt: Ontologie auf v0.1.1 erweitert |
| `OTA` | `overtime-archive.org/external-tasks/done/EXT-ENG-OTA-20260927-mars-settlement-closure-evidence.md` | erledigt: `OTA-SCI-0112-2026-DE` |
| `NXU` | `noxia-universe/external-tasks/open/EXT-ENG-NXU-20260927-mars-settlement-development-model.md` | offen |
| `NXU` | `noxia-universe/external-tasks/open/EXT-ENG-NXU-20260928-mars-settlement-systems-kernel-canonization.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-ENG-NOX-20260927-mars-settlement-simulation-gameplay.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-ENG-NOXIA-20260928-mars-settlement-systems-kernel-integration.md` | offen |

Die Übergabe an `noxia-realtime` (Ereigniszuordnung) hat ENG laut eigenem
Erledigt-Vermerk angelegt; sie liegt außerhalb der in `registry/projects.json`
geführten Repositories und wird hier nicht weiter verfolgt.

## 5. Regeln

- **Gemeinsame Reservoire und Flüsse:** Nachgelagerte Systeme (Energie,
  Lebenserhaltung, Biologie, Landwirtschaft, Abfall, Industrie, Logistik,
  Robotik) nutzen die gemeinsamen Reservoire und Flüsse des Kernels und legen
  keine eigenen, doppelten Ressourcenzähler an.
- **Epistemische Trennung:** physische Realität ≠ Beobachtung ≠
  Schätzung/Modell ≠ Akteurswissen. Der physische Zustand ist maßgeblich;
  Sensor-, Zwillings- und Akteursebene bleiben getrennt.
- Keine neue Source of Truth. Die Zuständigkeiten aus
  [`docs/source-of-truth.md`](../source-of-truth.md) bleiben unverändert;
  Änderungen in anderen Repositories laufen als External Tasks.
- Standortspezifische Werte bleiben in `kueper-engineering` bzw. im
  jeweiligen Projekt und werden nicht zu universellen Konstanten.
