# Planetensystem-Architekturen (nicht-koplanar/retrograd) – Programmregistrierung

Status: registriert (2026-11-15)  
Repository: `kueper-ecosystem`  
Registrierung: [`EXT-NOXIA-ECO-20260925-planetary-architecture-routing`](../../external-tasks/done/EXT-NOXIA-ECO-20260925-planetary-architecture-routing.md)  
Betroffene Codes: `ECO`, `ENG`, `KG`, `NXU`, `NOXIA`, `OTA`  
Ausdrücklich zurückgestellt: `noxia-realtime`

## 1. Zweck

Das Programm bündelt die Arbeit an nicht-koplanaren und retrograden
Planetensystemen über mehrere Repositories: wie Bahnebenen, Neigungen,
Spin-Bahn-Winkel und rückläufige Umläufe belegt, modelliert, in der
Entstehungsgeschichte des Kanons erklärt, bahnmechanisch korrekt behandelt
und im Spiel erzeugt und vermittelt werden.

## 2. Geltungsbereich

| Baustein | Bedeutung im Programm |
|---|---|
| Systemgeometrie | Bahnebenen, gegenseitige Neigung, Knotenlänge, Spin-Bahn-Winkel (projiziert und 3D), prograd/retrograd |
| Entstehungsgeschichte | Mögliche Mechanismen (Streuung, Kozai-Lidov, primordiale Fehlstellung u. a.) als konkurrierende Erklärungen, nicht als feste Wahrheit |
| Bahnmechanik | Ebenenwechsel, knotenabhängige Transferfenster, Fidelitätsstufen |
| Prozedurale Generierung | Plausible nicht-koplanare Systeme in NOXIA, beobachtbar ohne Preisgabe der verborgenen Geschichte |
| Lernmodul | Vermittlung von Bahngeometrie und Unsicherheit als Teil der NOXIA-Lernmodulfamilie |

## 3. Zuständigkeiten

| Domäne | Zuständigkeit | Beitrag |
|---|---|---|
| `kueper-ecosystem` (`ECO`) | Systemweite Governance | Programmregistrierung, Zuständigkeitsverteilung, Querverweise |
| `overtime-archive.org` (`OTA`) | Evidenz | Belege, Provenienz und Forschungsstand (Fallstudien) |
| `kueper-knowledge-graph` (`KG`) | Ontologie und kanonische IDs | Entitäten und Relationen der Systemarchitektur |
| `noxia-universe` (`NXU`) | Kanon | Entstehungsgeschichte und Weltbau |
| `kueper-engineering` (`ENG`) | Systemverträge | Bahnmechanik-Verträge (Ebenenwechsel, Transferzeitpunkte) |
| `noxiagame` (`NOXIA`) | Spiel und Lernen | Prozedurale Generierung, Gameplay, Lernmodul; keine kanonischen Definitionen |
| `noxia-realtime` | – | spätere Visualisierung und Laufzeitübernahme erst nach stabilen Verträgen; derzeit nicht adressiert |

## 4. Stand der Folgearbeiten

Die Folgearbeiten wurden bereits ab dem 25.09.2026 in die Ziel-Repositories
geroutet. Diese Registrierung legt sie zusammen und erzeugt keine doppelten Aufträge.

| Code | External Task | Stand (15.11.2026) |
|---|---|---|
| `KG` | `kueper-knowledge-graph/external-tasks/done/EXT-OTA-KG-20260925-spin-orbit-architecture.md` | erledigt: `ONT:KG:SPIN-ORBIT-ARCHITECTURE-0.1` (`exports/ontology-spin-orbit-architecture-0.1.json`) |
| `ENG` | `kueper-engineering/external-tasks/done/EXT-NOXIA-ENG-20260925-inclined-orbit-transfer-contract.md` | erledigt: `ENG-CONTRACT-ORBIT-PLANE-0001` (`systems/inclined-orbit-transfer-contract-r1.md`) |
| `OTA` | `overtime-archive.org/external-tasks/open/EXT-NOXIA-OTA-20260925-gj3090b-retrograde-orbit.md` | offen (Fallstudie retrograde Bahn GJ 3090 b) |
| `NXU` | `noxia-universe/external-tasks/open/EXT-OTA-NXU-20260925-multi-history-planetary-systems.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-NXU-NOX-20260925-noncoplanar-system-generation-learning.md` | offen |
| `NOXIA` | `noxiagame/external-tasks/open/EXT-ENG-NOXIA-20261018-inclined-orbit-transfer-integration.md` | offen (Übernahme des ENG-Vertrags) |

## 5. Querverweise zu Nachbarprogrammen

| Nachbarprogramm | Referenz | Verhältnis |
|---|---|---|
| Astronomie / Planetare Fernerkundung | [`planetary-remote-sensing.md`](planetary-remote-sensing.md) | Systemgeometrie wird über Beobachtungen erschlossen; projizierte Obliquität ist nicht die 3D-Obliquität |
| Navigation | ENG `systems/inclined-orbit-transfer-contract-r1.md`; NOXIA-Integrationstask (Tabelle oben) | Ebenenwechsel und knotenabhängige Transfers; NOXIA darf vereinfacht darstellen, aber die Physik nicht umdefinieren |
| Systemgenerierung | NOXIA-Generierungstask (Tabelle oben); [`planetary-evolution.md`](planetary-evolution.md) | Generierte Systeme folgen KG-Ontologie und ENG-Verträgen; Planetary Evolution liefert die Langzeitentwicklung der Körper |
| Exploration | NOXIA `external-tasks/open/EXT-ENG-NOXIA-20260911-resource-intelligence.md`; ENG `systems/planetary-resource-reconnaissance-architecture-0.1.md` | Erkundung nutzt dieselbe Bahn- und Beobachtungsgrundlage |
| NOXIA-Lernmodulfamilie | NOXIA-Tasks oben; `solarsciencefoundation` für Lernpfade | Lernmodule konsumieren KG-Ontologie und ENG-Verträge; Lernfortschritt bleibt SSF |

## 6. Regeln und Abgrenzungen

- Keine neue Source of Truth. Die Zuständigkeiten aus
  [`docs/source-of-truth.md`](../source-of-truth.md) bleiben unverändert.
- Föderierte Zuständigkeit: Jede Domäne liegt in genau einem Repository;
  Änderungen anderswo laufen als External Tasks.
- Beobachtete Geometrie ≠ Entstehungsgeschichte: Kanon und Spiel behandeln
  Entstehungsmechanismen als Hypothesen mit Evidenzstand, nicht als Befund.
- Epistemische Regel: physische Realität ≠ Beobachtung ≠ Schätzung/Modell ≠
  Akteurswissen.
- `noxia-realtime` wird erst adressiert, wenn stabile Verträge existieren.
