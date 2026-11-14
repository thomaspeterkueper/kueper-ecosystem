# Planetare Fernerkundung / Beobachtende Astronomie – Programmregistrierung

Status: registriert (2026-11-14)  
Repository: `kueper-ecosystem`  
Registrierung: [`EXT-NOXIA-ECO-20260925-planetary-remote-sensing-routing`](../../external-tasks/done/EXT-NOXIA-ECO-20260925-planetary-remote-sensing-routing.md)  
Betroffene Codes: `ECO`, `ENG`, `KG`, `NXU`, `NOXIA`, `OTA`  
Ausdrücklich zurückgestellt: `noxia-realtime`

## 1. Zweck

Das Programm bündelt planetare Fernerkundung und beobachtende Astronomie über
mehrere Repositories: wie aus physikalischen Eigenschaften Beobachtungen,
Messungen, Schlussfolgerungen und Unsicherheiten werden – in der Evidenz, im
Wissensgraphen, in Instrumentverträgen, in der Entdeckungsgeschichte des Kanons
und im Spiel.

## 2. Geltungsbereich

| Baustein | Bedeutung im Programm |
|---|---|
| Erkenntniskette | Physikalische Eigenschaft → beobachtbares Phänomen → Messung → verarbeitetes Signal → Schlussfolgerung/Hypothese → Konfidenz/Unsicherheit |
| Instrumente und Messung | Simulation von Instrumenten, Messfehlern und Beobachtungsbedingungen |
| Entdeckungsgeschichte | Wann und wie Akteure im Kanon etwas erkannt haben |
| Beobachtungs-Gameplay | Beobachten, Auswerten und Unsicherheit als Spiel- und Lernerfahrung |

## 3. Zuständigkeiten

| Domäne | Zuständigkeit | Beitrag |
|---|---|---|
| `kueper-ecosystem` (`ECO`) | Systemweite Governance | Programmregistrierung, Zuständigkeitsverteilung, Querverweise |
| `overtime-archive.org` (`OTA`) | Evidenz | Provenienz und Forschungsstand |
| `kueper-knowledge-graph` (`KG`) | Ontologie und kanonische IDs | Beobachtungs- und Inferenz-Ontologie |
| `kueper-engineering` (`ENG`) | Systemverträge | Verträge für Instrument- und Messsimulation |
| `noxia-universe` (`NXU`) | Kanon | Entdeckungsgeschichte und wissenschaftliche Kultur |
| `noxiagame` (`NOXIA`) | Spiel und Lernen | Beobachtungs-Gameplay, UX für Unsicherheit, Lernmodule; keine kanonischen Definitionen |
| `noxia-realtime` | – | spätere Visualisierung erst nach stabilen Verträgen; derzeit nicht adressiert |

## 4. Stand der Folgearbeiten

Die Folgearbeiten wurden bereits ab dem 25.09.2026 in die Ziel-Repositories
geroutet. Diese Registrierung legt sie zusammen und erzeugt keine doppelten Aufträge.

| Code | External Task | Stand (14.11.2026) |
|---|---|---|
| `KG` | `kueper-knowledge-graph/external-tasks/done/EXT-OTA-KG-20260925-planetary-remote-sensing-ontology.md` | erledigt: `ONT:KG:PLANETARY-REMOTE-SENSING-0.1` (`exports/ontology-planetary-remote-sensing-0.1.json`) |
| `ENG` | `kueper-engineering/external-tasks/done/EXT-NOXIA-ENG-20260925-observational-astronomy-instrument-contracts.md` | erledigt: `ENG-AUTH-ASTRO-OBS-0001` (`systems/observational-astronomy-instrument-authority-r1.md`) |
| `OTA` | `overtime-archive.org/external-tasks/done/EXT-NOXIA-OTA-20260925-beta-pictoris-radio-remote-sensing.md` | erledigt (Fallstudie Beta Pictoris b) |
| `OTA` | `overtime-archive.org/external-tasks/open/EXT-NOXIA-OTA-20260925-gj3090b-retrograde-orbit.md` | offen (Fallstudie retrograde Bahn) |
| `NXU` | `noxia-universe/external-tasks/open/EXT-OTA-NXU-20260925-observational-astronomy-layer.md` | offen |
| `NXU` | `noxia-universe/external-tasks/open/EXT-OTA-NXU-20260925-multi-history-planetary-systems.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-ENG-NOX-20260925-planetary-remote-sensing-learning.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-NXU-NOX-20260925-noncoplanar-system-generation-learning.md` | offen |

## 5. Querverweise zu Nachbarprogrammen

| Nachbarprogramm | Referenz | Verhältnis |
|---|---|---|
| Planetary Evolution | [`planetary-evolution.md`](planetary-evolution.md) | Fernerkundung liefert die Beobachtungen, aus denen Planetengeschichte rekonstruiert wird |
| Systemgenerierung, retrograde und nicht-koplanare Architekturen | NOXIA-Task zur nicht-koplanaren Generierung und OTA-Fallstudie GJ 3090 b (Tabelle oben) | Generierte Systeme müssen beobachtbar sein, ohne die Wahrheit preiszugeben |
| Navigation und Exploration | NOXIA `external-tasks/open/EXT-ENG-NOXIA-20260911-resource-intelligence.md`; ENG `systems/planetary-resource-reconnaissance-architecture-0.1.md` | Erkundung und Ressourcenaufklärung nutzen dieselbe Beobachtungs- und Inferenzkette |
| NOXIA-Lernmodule | NOXIA-Tasks oben; `solarsciencefoundation` für Lernpfade | Lernmodule konsumieren KG-Ontologie und ENG-Verträge; Lernfortschritt bleibt SSF |

## 6. Regeln und Abgrenzungen

- Keine neue Source of Truth. Die Zuständigkeiten aus
  [`docs/source-of-truth.md`](../source-of-truth.md) bleiben unverändert.
- Föderierte Zuständigkeit: Jede Domäne liegt in genau einem Repository;
  Änderungen anderswo laufen als External Tasks.
- Physikalische Wahrheit ≠ Wissen von Akteuren und Spielern: Spiel und Kanon
  arbeiten mit Beobachtungen und Schlussfolgerungen, nicht mit der verborgenen
  Wahrheit.
- Epistemische Regel: physische Realität ≠ Beobachtung ≠ Schätzung/Modell ≠
  Akteurswissen; konkurrierende Interpretationen und spätere Evidenz bleiben möglich.
- `noxia-realtime` wird erst adressiert, wenn stabile Verträge existieren.
