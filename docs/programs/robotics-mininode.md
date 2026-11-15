# Robotik / MiniNode – Programmregistrierung

Status: registriert (2026-11-15)  
Repository: `kueper-ecosystem`  
Registrierung: [`EXT-ENG-ECO-20260924-robotics-program-routing`](../../external-tasks/done/EXT-ENG-ECO-20260924-robotics-program-routing.md)  
Betroffene Codes: `ECO`, `ENG`, `KG`, `NXU`, `NOXIA`, `OTA`; Produktpfad `kueper-products`  
Ausdrücklich zurückgestellt: `noxia-realtime`

## 1. Zweck

Das Programm bündelt die Robotik rund um MiniNode über mehrere Repositories:
eine Familie kleiner, autonomer und zusammenwirkender Roboterknoten – von der
realen Evidenz über Ontologie und Systemarchitektur bis zu Kanon, Gameplay und
einem späteren realen Prototypenpfad.

MiniNode ist kein universeller Roboter, sondern eine Familie interoperabler
Knoten mit gemeinsamen Verträgen für Identität und Fähigkeiten, Aufgaben,
Energie und Laden, mechanisches Andocken, Kommunikation, Lokalisierung und
Provenienz sowie Gesundheits- und Sicherheitszustand (`ENG-SYS-MININODE-0001`).

## 2. Geltungsbereich

| Baustein | Bedeutung im Programm |
|---|---|
| Knotenklassen | Scout, Manipulation, Transport, Energie, Kommunikation, Reparatur – zugeordnet nach zertifizierten Fähigkeiten, nicht nach Aussehen |
| Schwarmkoordination | Aufgabenverteilung, Mesh-Kommunikation, verteilte Lokalisierung, Betrieb im degradierten Zustand, Aufsicht durch Menschen |
| Energie und Andocken | Laden, Akkutausch, mobile Puffer; Kopplung an Energiekapazitätsverträge |
| Feldrobotik | Bau-, Agrar- und Gartenrobotik, kooperative Manipulation |
| Realer Prototypenpfad | Gen-0-Umweltsensor als erste physische Vorstufe; der reale Garten-Roboterschwarm ist ein künftiges, kapitalabhängiges Programm und keine aktuelle Bauzusage |
| Kanon und Gameplay | Sauerländer Robotik- und MiniNode-Linie im Kanon; Schwarm-Gameplay und Lernbezug in NOXIA |

## 3. Zuständigkeiten

| Domäne | Zuständigkeit | Beitrag |
|---|---|---|
| `kueper-ecosystem` (`ECO`) | Systemweite Governance | Programmregistrierung, Zuständigkeitsverteilung, Querverweise |
| `kueper-engineering` (`ENG`) | Physische Architektur | Systemarchitektur, Schnittstellen, Prototyp-Engineering, künftiger realer Garten-Roboterschwarm |
| `kueper-knowledge-graph` (`KG`) | Ontologie und kanonische IDs | Robotik-Entitäten, Relationen und IDs |
| `overtime-archive.org` (`OTA`) | Evidenz | Technische Dossiers, Reifegrad und Provenienz; reale Fähigkeiten getrennt von Prototypen und Extrapolation |
| `noxia-universe` (`NXU`) | Kanon | Historische, kulturelle und industrielle Entwicklung der Robotik |
| `noxiagame` (`NOXIA`) | Spiel | Gameplay, Balancing, Laufzeitverträge; keine kanonischen Definitionen |
| `kueper-products` | Produktpfad | Bewertung und Übernahme prototypreifer Engineering-Baselines; keine eigene Architekturhoheit |
| `noxia-realtime` | – | Visualisierung und Steuerung erst nach stabilen Verträgen; derzeit nicht adressiert |

## 4. Stand der Folgearbeiten

Die Folgearbeiten wurden bereits ab dem 24.09.2026 in die Ziel-Repositories
geroutet. Diese Registrierung legt sie zusammen und erzeugt keine doppelten Aufträge.

| Code | External Task | Stand (15.11.2026) |
|---|---|---|
| `ENG` | `kueper-engineering/external-tasks/done/EXT-NOXIA-ENG-20260924-mininode-robot-swarm-platform.md` | erledigt: `ENG-SYS-MININODE-0001` (`systems/mininode-robot-swarm-platform-r1.md`, `systems/mininode-robot-swarm-interface-r1.json`) |
| `ENG` | `kueper-engineering/external-tasks/done/EXT-PRODUCTS-ENG-20261002-mininode-env.md` | erledigt: `ENG-SYS-MININODE-ENV-0001` (`systems/mininode-environment-sensor-gen0-r1.md`, `systems/mininode-environment-sensor-gen0-r1.json`) |
| `KG` | `kueper-knowledge-graph/external-tasks/done/EXT-ENG-KG-20260924-mininode-robotics-ontology.md` | erledigt: `ONT:KG:MODULAR-ROBOTICS-0.1` (`exports/ontology-modular-robotics-0.1.json`) |
| `OTA` | `overtime-archive.org/external-tasks/done/EXT-ENG-OTA-20260924-distributed-robotics-mininode-dossier.md` | erledigt: `OTA-TEC-0126-2026-DE` |
| `NXU` | `noxia-universe/external-tasks/open/EXT-ENG-NXU-20260924-sauerland-robotics-mininode-lineage.md` | offen |
| `NXU` | `noxia-universe/external-tasks/open/EXT-ENG-NXU-20260928-mininode-swarm-integration.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-NXU-NOX-20260924-mininode-robot-swarm-gameplay.md` | offen |
| `kueper-products` | `kueper-products/external-tasks/open/EXT-ENG-PRODUCTS-20261018-mininode-env-gen0-handoff.md` | offen |

## 5. Querverweise zu Nachbarprogrammen

| Nachbarprogramm | Referenz | Verhältnis |
|---|---|---|
| Adaptive Industry | [`adaptive-industry.md`](adaptive-industry.md) | MiniNodes binden sich über Fähigkeits-, Energie- und Zustandsverträge an Fertigung und digitale Zwillinge an |
| Mars Settlement Systems Kernel | [`mars-settlement-kernel.md`](mars-settlement-kernel.md) | Robotik nutzt die gemeinsamen Reservoire und Flüsse der Siedlung; keine doppelten Ressourcenzähler |
| Living Infrastructure | [`living-infrastructure.md`](living-infrastructure.md) | Physische Operationen und Automatisierung konsumieren die Flussverträge |
| Energy Grid Layer | `external-tasks/open/EXT-ENG-ECO-20260925-energy-grid-learning-routing.md`; ENG `ENG-SYS-EGCA-0001` | Lade- und Energiebedarf der Knoten innerhalb der Kapazitätsgrenzen |
| Planetare Fernerkundung | [`planetary-remote-sensing.md`](planetary-remote-sensing.md) | Scout-Knoten als Mess- und Erkundungsträger; Messung ≠ Schlussfolgerung |

## 6. Regeln und Abgrenzungen

- Keine neue Source of Truth. Die Zuständigkeiten aus
  [`docs/source-of-truth.md`](../source-of-truth.md) bleiben unverändert.
- Föderierte Zuständigkeit: Jede Domäne liegt in genau einem Repository;
  Änderungen anderswo laufen als External Tasks.
- Engineering erzeugt keine NOXIA-, KG- oder OTA-Identitäten; Konsum und
  Kanonisierung laufen über External Tasks der Ziel-Repositories.
- Evidenzklassen getrennt halten: demonstrierte Praxis ≠ Forschungsprototyp ≠
  Extrapolation ≠ Fiktion.
- Der reale Garten-Roboterschwarm ist ein künftiges, kapitalabhängiges
  Programm, keine aktuelle Bauzusage.
- `noxia-realtime` wird erst adressiert, wenn stabile Verträge existieren.
