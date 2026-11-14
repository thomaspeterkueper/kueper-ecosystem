# Planetary Evolution / Geosphäre–Biosphäre-Kopplung – Programmregistrierung

Status: registriert (2026-11-14)  
Repository: `kueper-ecosystem`  
Registrierung: [`EXT-NOXIA-ECO-20260925-planetary-evolution-routing`](../../external-tasks/done/EXT-NOXIA-ECO-20260925-planetary-evolution-routing.md)  
Betroffene Codes: `ECO`, `ENG`, `KG`, `NXU`, `NOXIA`, `OTA`  
Ausdrücklich zurückgestellt: `noxia-realtime`

## 1. Zweck

Das Programm bündelt die gekoppelte Entwicklung von Geosphäre, Hydrosphäre,
Atmosphäre und Biosphäre über geologische Zeiträume („Deep Time“) als
Querschnittsthema mehrerer Repositories: von der Evidenz über kanonische Prozesse
und Systemverträge bis zu Planetengeschichte, prozeduraler Generierung und
wissenschaftlicher Rekonstruktion im Spiel.

## 2. Geltungsbereich

| Baustein | Bedeutung im Programm |
|---|---|
| Geosphäre–Biosphäre-Kopplung | Tektonik, Relief, Erosion/Verwitterung, Drainage, Sediment, Nährstofffluss, Produktivität, Kohlenstoffeinlagerung, Redox/Oxygenierung |
| Proxies und Rekonstruktion | Probe → Messung → Proxy → Interpretation → rekonstruierter Zustand → Kausalhypothese |
| Mehrere Zeitskalen | Gekoppelte Modelle von Ereignis- bis Äonenmaßstab, ensemble- und unsicherheitsfähig |
| Planetengeschichte | Verborgene Geschichte eines Planeten als Kanon- und Generierungsgegenstand |
| Künftiges Terraforming | spätere Erweiterung; keine aktuelle Umsetzungszusage |

## 3. Zuständigkeiten

| Domäne | Zuständigkeit | Beitrag |
|---|---|---|
| `kueper-ecosystem` (`ECO`) | Systemweite Governance | Programmregistrierung, Zuständigkeitsverteilung, Querverweise |
| `overtime-archive.org` (`OTA`) | Evidenz | Proxies, Provenienz und Forschungsunsicherheit |
| `kueper-knowledge-graph` (`KG`) | Kanonische Prozesse und Relationen | Prozesse, Proxies, Zustände und Relationen für Kausalhypothesen |
| `kueper-engineering` (`ENG`) | Systemverträge | Verträge für gekoppelte Systeme über mehrere Zeitskalen |
| `noxia-universe` (`NXU`) | Kanon | Planetengeschichte und xenobiologischer Kanon |
| `noxiagame` (`NOXIA`) | Spiel und Lernen | Prozedurale Geschichte, Rekonstruktions-Gameplay, Lernen über Deep Time; keine kanonischen Definitionen |
| `noxia-realtime` | – | spätere Visualisierung erst nach stabilen Verträgen; derzeit nicht adressiert |

## 4. Stand der Folgearbeiten

Die Folgearbeiten wurden bereits ab dem 25.09.2026 in die Ziel-Repositories
geroutet. Diese Registrierung legt sie zusammen und erzeugt keine doppelten Aufträge.

| Code | External Task | Stand (14.11.2026) |
|---|---|---|
| `KG` | `kueper-knowledge-graph/external-tasks/done/EXT-OTA-KG-20260925-geosphere-biosphere-coupling-ontology.md` | erledigt: `ONT:KG:GEOSPHERE-BIOSPHERE-COUPLING-0.1` (`exports/ontology-geosphere-biosphere-coupling-0.1.json`) |
| `ENG` | `kueper-engineering/external-tasks/done/EXT-NOXIA-ENG-20260925-planetary-evolution-coupling-model.md` | erledigt: `ENG-AUTH-PLANEVOL-0001` (`systems/planetary-evolution-coupling-authority-r1.md`) |
| `OTA` | `overtime-archive.org/external-tasks/open/EXT-NOXIA-OTA-20260925-geosphere-biosphere-deep-time.md` | offen |
| `NXU` | `noxia-universe/external-tasks/open/EXT-OTA-NXU-20260925-coupled-planetary-histories.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-ENG-NOX-20260925-planetary-evolution-generator-deep-time-learning.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-ENG-NOXIA-20261018-planetary-evolution-reconstruction.md` | offen |

## 5. Querverweise zu Nachbarprogrammen

| Nachbarprogramm | Referenz | Verhältnis |
|---|---|---|
| Planetare Fernerkundung | [`planetary-remote-sensing.md`](planetary-remote-sensing.md) | Liefert Beobachtungen, aus denen Rekonstruktionen entstehen; Beobachtung ist nicht die verborgene Geschichte |
| Systemgenerierung | ENG `systems/impact-surface-evolution-architecture-v0.1.md`; NOXIA-Generator (Tabelle oben) | Prozedurale Planeten- und Oberflächenentwicklung nutzt die gekoppelten Verträge |
| Geologie und Ressourcen | ENG `systems/planetary-resource-reconnaissance-architecture-0.1.md` | Lagerstätten und Erkundung als Folge der Planetengeschichte |
| Biosphären | [`mycology-soil-ecopoiesis.md`](mycology-soil-ecopoiesis.md) | Bodenleben und Ecopoiesis als biologische Seite der Kopplung |
| Siedlungswissenschaft | [`living-infrastructure.md`](living-infrastructure.md); [`mars-settlement-kernel.md`](mars-settlement-kernel.md) | Siedlungen arbeiten auf kürzeren Zeitskalen; Planetary Evolution liefert die Randbedingungen |
| Künftiges Terraforming | – | Zukunftserweiterung; erst nach stabilen Verträgen |

## 6. Regeln und Abgrenzungen

- Keine neue Source of Truth. Die Zuständigkeiten aus
  [`docs/source-of-truth.md`](../source-of-truth.md) bleiben unverändert.
- Föderierte Zuständigkeit: Jede Domäne liegt in genau einem Repository;
  Änderungen anderswo laufen als External Tasks.
- Verborgene Geschichte ≠ rekonstruiertes Wissen: Generierung darf die exakte
  Geschichte intern speichern, Rekonstruktion arbeitet nur mit Beobachtungen und
  Schätzungen. Mehrere Geschichten können mit denselben Beobachtungen vereinbar sein.
- Epistemische Regel: physische Realität ≠ Beobachtung ≠ Schätzung/Modell ≠
  Akteurswissen. Kausalaussagen bleiben Hypothesen, bis Evidenz sie stützt.
- `noxia-realtime` wird erst adressiert, wenn stabile Verträge existieren.
