# Mykologie / Bodenökologie / Ecopoiesis – Programmregistrierung

Status: registriert (2026-11-14)  
Repository: `kueper-ecosystem`  
Registrierung: [`EXT-NOXIA-ECO-20260925-mycology-ecopoiesis-routing`](../../external-tasks/done/EXT-NOXIA-ECO-20260925-mycology-ecopoiesis-routing.md)  
Betroffene Codes: `ECO`, `ENG`, `KG`, `NXU`, `NOXIA`, `OTA`  
Ausdrücklich zurückgestellt: `noxia-realtime`

## 1. Zweck

Das Programm bündelt Pilze, Myzel, Bodenleben, mikrobielle Gemeinschaften und
kontrollierte Ecopoiesis als fachliche Domäne über mehrere Repositories. Es knüpft
ausdrücklich an die bestehende Mars-Siedlungsforschung an, statt ein paralleles
Silo zu bilden.

Verhältnis zu [Living Infrastructure](living-infrastructure.md): Living
Infrastructure ist die Integrationsschicht für konservierte Flüsse zwischen
Mykologie/Bodenökologie, Lebenserhaltung, Landwirtschaft, Abfall/Recycling und
Planetarer Evolution. Dieses Programm ist die fachliche Domäne darunter. Es führt
keine eigenen Flüsse oder Ressourcenzähler ein, sondern nutzt die Reservoire und
Flüsse von Living Infrastructure und Mars Settlement Systems Kernel.

## 2. Geltungsbereich

| Baustein | Bedeutung im Programm |
|---|---|
| Mykologie | Pilze, Myzel, Fruchtkörper, Sporen, funktionale Rollen, Symbiose/Mykorrhiza |
| Bodenökologie | Mikrobielle Gemeinschaften, Substrat, Mineralisierung, Sukzession |
| Kontrollierte Ökosystemmodule | Engineered Substrate, geschlossene Nährstoffkreisläufe, Ausfall- und Degradationszustände |
| Ecopoiesis | Spätere, offene Erweiterung auf planetare Maßstäbe; keine aktuelle Umsetzungszusage |

## 3. Zuständigkeiten

| Domäne | Zuständigkeit | Beitrag |
|---|---|---|
| `kueper-ecosystem` (`ECO`) | Systemweite Governance | Programmregistrierung, Zuständigkeitsverteilung, Querverweise |
| `overtime-archive.org` (`OTA`) | Evidenz | Provenienz, Reifegrad, Unsicherheit und Konsolidierung früherer Forschung, einschließlich früherer Mars-Pilz-Arbeiten |
| `kueper-knowledge-graph` (`KG`) | Kanonische Entitäten und Relationen | Ökologische Entitäten, Prozesse, Zustände; Mapping statt Neudefinition |
| `kueper-engineering` (`ENG`) | Systemverträge | Verträge für kontrollierte Substrate und Ökosystemsimulation, angebunden an ECLSS und Settlement Kernel |
| `noxia-universe` (`NXU`) | Kanon | Siedlungs- und Ecopoiesis-Geschichte, Kultur; keine technische Dimensionierung |
| `noxiagame` (`NOXIA`) | Spiel und Lernen | Ökologie-Gameplay und Lernmodule „Hidden Biosphere“; keine kanonischen Definitionen |
| `noxia-realtime` | – | spätere Visualisierung erst nach stabilen Verträgen; derzeit nicht adressiert |

## 4. Stand der Folgearbeiten

Die Folgearbeiten wurden bereits am 25.–27.09.2026 aus Engineering und NOXIA in die
Ziel-Repositories geroutet. Diese Registrierung legt sie zusammen und erzeugt keine
doppelten Aufträge.

| Code | External Task | Stand (14.11.2026) |
|---|---|---|
| `KG` | `kueper-knowledge-graph/external-tasks/done/EXT-OTA-KG-20260925-mycology-soil-ecopoiesis-ontology.md` | erledigt: `ONT:KG:MYCOLOGY-SOIL-ECOPOIESIS-0.1` (`exports/ontology-mycology-soil-ecopoiesis-0.1.json`) |
| `KG` | `kueper-knowledge-graph/external-tasks/done/EXT-ENG-KG-20260925-settlement-biogeochemical-flows.md` | erledigt |
| `ENG` | `kueper-engineering/external-tasks/done/EXT-NOXIA-ENG-20260925-offworld-soil-ecology-architecture.md` | erledigt: `ENG-SYS-SOILECO-0001` (`systems/offworld-soil-ecology-architecture-r1.md`) |
| `ENG` | `kueper-engineering/external-tasks/done/EXT-NOXIA-ENG-20260925-ecological-life-support-integration.md` | erledigt |
| `OTA` | `overtime-archive.org/external-tasks/open/EXT-NOXIA-OTA-20260925-mycology-soil-ecopoiesis-dossier.md` | offen |
| `NXU` | `noxia-universe/external-tasks/open/EXT-ENG-NXU-20260925-fungi-mars-settlement-ecopoiesis.md` | offen |
| `NXU` | `noxia-universe/external-tasks/open/EXT-ENG-NXU-20260925-mars-living-infrastructure.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-ENG-NOX-20260925-hidden-biosphere-soil-ecology-learning.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-ENG-NOX-20260925-settlement-ecology-loop-gameplay.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-ENG-NOXIA-20260927-soil-ecology-runtime-integration.md` | offen |

Ergänzend über Living Infrastructure am 14.11.2026 geroutet:
`kueper-engineering` `EXT-ECO-ENG-20261114-001` (Flussvertrag),
`kueper-knowledge-graph` `EXT-ECO-KG-20261114-001` (Material- und
Prozessidentitäten), `overtime-archive.org` `EXT-ECO-OTA-20261114-001`
(Evidenzkonsolidierung).

## 5. Querverweise zu Nachbarprogrammen

| Nachbarprogramm | Referenz | Verhältnis |
|---|---|---|
| Living Infrastructure | [`living-infrastructure.md`](living-infrastructure.md) | Integrationsschicht für die Flüsse; dieses Programm liefert die ökologische Fachdomäne |
| Mars Settlement Systems Kernel | `external-tasks/open/EXT-NOXIA-ECO-20260927-mars-settlement-kernel-routing.md`; ENG `systems/mars-settlement-systems-kernel-r1.md` | Gemeinsame Reservoire und Flüsse; keine doppelten Ressourcenzähler |
| Planetary Evolution / Geosphäre–Biosphäre | `external-tasks/open/EXT-NOXIA-ECO-20260925-planetary-evolution-routing.md` | Langfristige Randbedingungen; Biosphären und künftiges Terraforming |
| Geschlossene Lebenserhaltung, Landwirtschaft, Abfall/Recycling | ENG `ENG-SYS-ECLSS-0001`; Living Infrastructure | Bausteine, die Substrat- und Nährstoffkreisläufe teilen |
| Ressourcen und Habitate | Mars Settlement Kernel; Adaptive Industry (`external-tasks/open/EXT-NOXIA-ECO-20260925-adaptive-industry-routing.md`) | Material- und Prozessschnittstellen über KG-Identitäten und ENG-Verträge |
| Myzelbaustoffe | [`reviews/2027-10-10-myzelbaustoffe-naturverbundenes-bauen.md`](../../reviews/2027-10-10-myzelbaustoffe-naturverbundenes-bauen.md); ENG `MYCO-0001` | Bestehende Myzel-Forschung, wird referenziert statt dupliziert |

## 6. Regeln und Abgrenzungen

- Keine neue Source of Truth. Die Zuständigkeiten aus
  [`docs/source-of-truth.md`](../source-of-truth.md) bleiben unverändert.
- Föderierte Zuständigkeit: Jede Domäne liegt in genau einem Repository;
  Änderungen anderswo laufen als External Tasks.
- Epistemische Regel: physische Realität ≠ Beobachtung ≠ Schätzung/Modell ≠
  Akteurswissen. Beobachtung und ökologische Interpretation bleiben getrennt.
- Frühere Mars-Pilz-Forschung gilt nicht als abwesend, nur weil Repository-Suchen
  nichts fanden; OTA konsolidiert den Stand.
- Ecopoiesis bleibt eine Zukunftserweiterung ohne Umsetzungszusage.
- `noxia-realtime` wird erst adressiert, wenn stabile Verträge existieren.
