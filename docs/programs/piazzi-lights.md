# Piazzi-Lights / Ceres 2091 – Zuständigkeitsgrenze

Status: registriert (2026-11-15)  
Repository: `kueper-ecosystem`  
Registrierung: [`EXT-NXU-ECO-20260921-piazzi-lights-engineering-handoff`](../../external-tasks/done/EXT-NXU-ECO-20260921-piazzi-lights-engineering-handoff.md)  
Betroffene Codes: `ECO`, `NXU`, `ENG`, `OTA`, `NOXIA`  
Ausdrücklich zurückgestellt: `noxia-realtime` (erst nach stabilen Verträgen)

## 1. Zweck

Piazzi-Lights ist die dauerhafte menschliche Siedlung auf Ceres im Zeithorizont
2065–2091 (`noxia-universe/spaces/noxia/infrastructure/NXU-CERES-PIAZZI-LIGHTS-2091.md`).
Die NOXIA-Autorenarbeit hat am 21.09.2026 die verbleibende technische
Schließung an `kueper-engineering` übergeben. Diese Registrierung hält die
Zuständigkeitsgrenze zwischen Autorenarbeit und Engineering fest, damit sie
überall dort greift, wo Cross-Repository-Abhängigkeiten entstehen.

Die Registrierung ist eine Governance-Rolle: Kanon bleibt in `noxia-universe`,
technische Festlegungen bleiben in `kueper-engineering`.

## 2. Zuständigkeiten

| Domäne | Zuständigkeit | Beitrag |
|---|---|---|
| `kueper-ecosystem` (`ECO`) | Systemweite Governance | Zuständigkeitsgrenze, Routing-Regel, Querverweise |
| `kueper-engineering` (`ENG`) | Technische Schließung | Struktur, Lagerung/Aufhängung, künstliche Schwerkraft, Abschirmung, Versorgung, ECLSS, Energie, Thermik, ISRU, Bauablauf, Fehlermodi |
| `overtime-archive.org` (`OTA`) | Evidenz | biologische und Strahlungsfragen, für die Validierung nötig ist |
| `noxia-universe` (`NXU`) | Kanon | Übernahme oder Ablehnung der Engineering-Schließung; Figuren, Beziehungen, Gesellschaft, Alltag, Institutionen, Szenen |
| `noxiagame` (`NOXIA`) | Spiel | Konsument; keine kanonischen oder technischen Festlegungen |
| `noxia-realtime` | – | späterer Konsument stabiler Verträge; derzeit nicht adressiert |

## 3. Routing-Regel

- Technische Fragen zu Struktur, Lagerung/Aufhängung, künstlicher Schwerkraft,
  Abschirmung, Versorgung, ECLSS, Energie, Thermik, ISRU, Bauablauf und
  Fehlermodi gehen an `kueper-engineering`.
- `overtime-archive.org` übernimmt Evidenzfragen, wo biologische oder
  Strahlungsvalidierung nötig ist.
- Die NOXIA-Autorenarbeit konsumiert die Engineering-Rückmeldung und setzt
  die technische Detailoptimierung nicht parallel fort.
- Spiel- und Echtzeit-Implementierungen schreiben die Torus-Parameter erst
  dann als endgültig fest, wenn `noxia-universe` die Schließung kanonisiert hat.

## 4. Parameterstatus

Die Autorenparameter (u. a. ~120 permanente Bewohner 2091, Arbeitsband
~100–140; ~8–15 Personen unter 18; Torus 180 m Hauptdurchmesser / ~90 m
Hauptradius / ~18 m Röhre; Wohnebene ~99 m; ~3,0 rpm für ~1 g; stationäre
lokale Abschirmung um das rotierende Druckhabitat) gelten als
**provisional-selected**, nicht als geschlossene technische Tatsachen,
solange `noxia-universe` die Engineering-Schließung nicht übernommen hat.

Für keinen g-Wert, keine Drehrate und keinen Expositionsplan wird
behauptet, er sei für Schwangerschaft, Kindheit oder lebenslange
Entwicklung sicher.

## 5. Stand der Folgearbeiten

| Code | External Task | Stand (15.11.2026) |
|---|---|---|
| `ENG` | `kueper-engineering/external-tasks/done/EXT-NXU-ENG-20260921-piazzi-lights-technical-closure.md` | erledigt: `ENG-SYS-PLH-0001` (`systems/piazzi-lights-habitat-architecture-r1.md`); keine zwingende Änderung der Autorengeometrie |
| `NXU` | `noxia-universe/external-tasks/open/EXT-ENG-NXU-20260921-piazzi-lights-canonization.md` | offen – bis zur Übernahme bleiben die Parameter provisional-selected |
| `OTA` | `overtime-archive.org/external-tasks/done/EXT-ENG-OTA-20261018-ceres-child-freighter-birth-canonicalization.md` | erledigt (angrenzende Evidenzfrage Ceres) |

Diese Registrierung erzeugt keine doppelten Aufträge.

## 6. Regeln

- Keine neue Source of Truth. Die Zuständigkeiten aus
  [`docs/source-of-truth.md`](../source-of-truth.md) bleiben unverändert;
  Änderungen in anderen Repositories laufen als External Tasks.
- Standortspezifische Werte (Ceres, Piazzi-Lights) bleiben in
  `kueper-engineering` bzw. `noxia-universe` und werden nicht zu universellen
  Konstanten.
- Bezüge zum [`Mars Settlement Systems Kernel`](mars-settlement-kernel.md)
  und zum [`Energy Grid Layer`](energy-grid.md) sind fachlich naheliegend,
  aber nicht festgelegt; eine Kopplung wird bei Bedarf als External Task an
  `kueper-engineering` geroutet.
