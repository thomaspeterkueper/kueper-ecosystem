# Utopia-/Mars-Chronologie als Timeline-Projektion

Status: implementiert (Projektion v0.2.0)  
Repository: `kueper-ecosystem`  
External Task: `external-tasks/done/EXT-OTA-ECO-20260911-utopia-mars-chronology-projection.md`  
OTA-Quelle: `overtime-archive.org` PR #60 (Branch `canon/utopia-mars-corridor`)  
Vertrag: ECO-ARC-0018-2026-DE (Timeline als Consumer, keine Source of Truth)

## 1. Zweck

Die geschützte Universe-Timeline nimmt den neuen Utopia-/Mars-Industrie-Strang als
eigenen Scope `Utopia/Mars` auf. Die Projektion referenziert die OTA-Dokumente nur;
sie kopiert sie nicht und ersetzt sie nicht. Vorläufige Aussagen werden nicht
kanonisiert, sondern mit `canonicality: "provisional"` geführt und sind damit
filterbar von Kanon getrennt.

## 2. Modellierte Ereignisse/Phasen

| Jahr | Ereignis (Event-ID) | OTA-Marker | Projektion |
|---|---|---|---|
| 2021 | Zhurong landet in Utopia Planitia (`EVENT:UTOPIA_MARS:zhurong_landung`) | `[R]` | `established` / `canonical` |
| 2024 | Nationale Space-Science-Roadmap bis 2050 (`EVENT:UTOPIA_MARS:space_science_roadmap_2050`) | `[R]` | `established` / `canonical` |
| ca. 2072–2075 | Robotische Vorbereitung des Kaiwu-Standorts (`EVENT:UTOPIA_MARS:robotische_vorbereitung`) | `[F/P]` | `fictional` / `provisional` |
| ca. 2076/77 | Erste permanente Besatzung in Kaiwu (`EVENT:UTOPIA_MARS:erste_besatzung`) | `[F/P]` | `fictional` / `provisional` |
| 03.12.2080 | Maryem Hamid wird in Kaiwu geboren (`EVENT:UTOPIA_MARS:maryem_hamid_geburt`) | `[K]` | `fictional` / `canonical` |
| 2087 | Große Stille als Kompetenz- und Resilienztest (`EVENT:UTOPIA_MARS:grosse_stille_kompetenztest`) | `[F/P]`, kanonische Regel | `speculative` / `provisional` |
| 2091 | Kaiwu als etablierter zweiter Marsknoten (`EVENT:UTOPIA_MARS:zweiter_marsknoten`) | `[F/P]` | `fictional` / `provisional` |

Referenzierte Dokumente: `OTA-HIS-0004-2021-DE`, `OTA-SCI-0090-2026-DE`,
`OTA-HIS-0005-2050-DE`, `OTA-META-0004-2076-DE`, `OTA-ORG-0008-2087-DE` sowie die
im Task nicht gelisteten, im selben PR ergänzten `OTA-CHR-0001-2072-DE` und
`OTA-SOC-0001-2076-DE`.

## 3. Marker-Mapping

| OTA-Marker | `epistemic_status` | `canonicality` |
|---|---|---|
| `[R]` real | `established` | `canonical` |
| `[K]` kanonisch (fiktionale Aussage) | `fictional` | `canonical` |
| `[F/P]` / `[P]` vorläufige Phase | `fictional` | `provisional` |
| `[F/P]` vorläufige Deutung (z. B. 2087) | `speculative` | `provisional` |

Mischfälle (`[K/P]`) werden nicht hochgestuft: Der kanonische Kern steht im
Summary, die Projektion des Ereignisses bleibt `provisional`. Reale Anker erhalten
bewusst keine `WORK:NOXIA:`-Relation — sie sind nicht Teil der NOXIA-Fiktion.

## 4. Eingehaltene Modellierungsregeln

- **Keine kanonische Stadtkoordinate:** Die in `OTA-SCI-0090-2026-DE` nur als
  Suchzentrum geführte Koordinate ist dort `[F/P]` und wird weder als Stadtkoordinate
  noch überhaupt im Projektionsdatensatz ausgegeben. Die endgültige Koordinate bleibt
  `[OFFEN]`.
- **Kein „Parallelmodell“:** Der Strang nutzt den bestehenden `UniverseEvent`-Vertrag
  (ECO-ARC-0018) und hängt über `relation_refs` an bestehende Anker
  (`WORK:NOXIA:generation_mars`, `CHAR:NOXIA:maryem_hamid`).
- **Keine OTA-Duplikation:** Summaries sind Projektionsparaphrasen; Inhalte und
  Kanonentscheidungen bleiben bei OTA/KG.
- **Real/Fiktion unterscheidbar:** `[R]`-Anker erscheinen als `established`
  (eigene Farbe und Filter im UI), fiktionale Fortschreibung als
  `fictional`/`speculative`.
- **Sichtbare Vorbehalte:** Der Endpunkt liefert `caveats`; die Timeline zeigt sie
  als „Projektionshinweise“.

## 5. Quellenstand und Abweichung zum Task-Text

Der External Task wurde am 11.09.2026 vor dem Merge des OTA-PR #60 (14.09.2026)
abgefasst. `OTA-META-0004-2076-DE` v1.1 setzt den Siedlungsnamen **Kaiwu (开物)**
inzwischen als `[K]` („Fest gesetzt“); die ältere Task-Annahme eines noch offenen
Stadtnamens und der Arbeitsname „Utopia-Siedlung“ sind damit überholt. Die Projektion
folgt dem aktuellen OTA-Stand, weil die Timeline Projektion des OTA ist und keine
eigene Kanonentscheidung treffen darf. Diese Abweichung wird hier und im
API-Antwortfeld `caveats` offengelegt, nicht stillschweigend ersetzt.

Weiterhin `[OFFEN]` laut Quelle: exakte Standortkoordinate, Einwohnerzahlen,
Rechtsform, Gründungsdatum im Rechtssinn, konkrete Notfallbefugnisse des Mars
Council während der Großen Stille.

## 6. Implementierung

- Projektionsdaten und Regeln: `app/internal/universe/timeline/seed-projection.ts`
- Auslieferung: `app/api/internal/universe-timeline/route.ts` (unverändert geschützt)
- UI: `app/internal/universe/timeline/page.tsx` (Projektionshinweise sichtbar)
- Absicherung: `tests/universe-projection.test.ts` (Vertrag, Marker-Mapping,
  Koordinatenverbot, Quellen-Signaturen, Cross-Project-Anker), ausgeführt über
  `npm run test:timeline` und `.github/workflows/timeline-tests.yml`

Residuum: `.github/workflows/timeline-tests.yml` wurde nicht angepasst, weil
`.github/workflows/*` in diesem Repo eine privilegierte Mutationsklasse ist
(`tools/worker/git_credentials.py`) und eine Änderung ohne `KUEPER_WORKFLOW_TOKEN`
den Task parkt. Für diesen PR greift der bestehende Pfadfilter
(`app/internal/universe/timeline/**`, `package.json`); sinnvoll wäre später ein
privilegierter Folge-PR, der die Filter um `tests/universe-projection.test.ts`
und `app/api/internal/universe-timeline/**` ergänzt.

## 7. Grenzen

Die Datei ist Seed-/Consumer-Projektion und ausdrücklich nicht kanonisch. Sobald
`kueper-knowledge-graph` eine Ereignisprojektion liefert, wird dieser Datensatz
dadurch ersetzt; die OTA-Dokumente bleiben die inhaltliche Quelle.
