# Onboarding-Template: Beitritt zum KUEPER-Ökosystem

Von: KUEPER Ecosystem (zentrale Normierungs- und Standardisierungsstelle)
An: jedes neue Projekt, das dem Ökosystem beitritt
Grundlage: `decisions/ECO-ARC-0005..0008`, `docs/repository-roles.md`,
`docs/source-of-truth.md`, `docs/cross-repository-workflow.md`

**Dies ist die verbindliche, aktuell gültige Onboarding-Vorlage.** Sie wird bei
Bedarf zentral hier gepflegt — nicht als Kopie in einzelnen Chats oder Projekten.
Wer sie weitergibt, sollte auf diese Datei verlinken oder ihren aktuellen Inhalt
kopieren, statt eine ältere Version wiederzuverwenden.

Setze überall, wo `{PROJEKT}` und `{CODE}` steht, den tatsächlichen Projektnamen
und den dir zugewiesenen Ökosystem-Code ein. Beispiel-Einsetzung: `{PROJEKT}` =
`mishkenaz.org`, `{CODE}` = `MISH` (Vorschlag, wird bei Registrierung bestätigt).

---

## 0. Bevor irgendetwas anderes passiert: registrieren lassen

`{PROJEKT}` ist erst „im Ökosystem", wenn es in `registry/projects.json`
(diesem Repository) eingetragen ist. Das trägst **nicht du
selbst ein** — das ist ausschließlich Sache von `kueper-ecosystem`. Schreibe
niemals direkt in dieses Repository (auch keine Registry-Änderungen).

Um aufgenommen zu werden: stelle einen External Task an `kueper-ecosystem`
(Ziel-Code `ECO`), sobald dein Repository existiert und mindestens eine
`README.md` hat. Der Owner (Thomas) leitet Registrierungswünsche weiter oder du
stellst sie direkt, sobald du Schreibzugriff hast. Der Task enthält:

- Repository-URL, Default-Branch
- Kurzbeschreibung der Rolle (was ist `{PROJEKT}`, was speichert/verarbeitet es)
- Vorschlag für deinen Ökosystem-Code (kurz, eindeutig, z. B. `{CODE}`)
- ob du personenbezogene Daten verarbeitest (Accounts, E-Mail, Supabase o. ä.)

Die zentrale Stelle vergibt dir dann einen verbindlichen Code und trägt dich mit
Rolle und Governance-Pflichtpfaden in die Registry ein.

## 1. Dein Ökosystem-Code

Jedes Projekt hat einen kurzen, eindeutigen Code für External Tasks und
IDs (siehe ECO-ARC-0006). Aktuelle Codes stehen in der Code-Tabelle von `decisions/ECO-ARC-0006-2026-DE.md`
(Stand bei Abfassung dieses Templates: `ECO`, `KG`, `SSF`, `NOXIA`, `NXU`, `KUE`,
`OTA`, `TKD`). Schlage bei der Registrierung einen neuen, noch nicht vergebenen
Code vor (`{CODE}`). Verwende ihn ab Bestätigung konsequent in allen Task-IDs.

## 2. Pflichtstruktur in deinem eigenen Repository

Lege von Anfang an an:

```text
README.md
external-tasks/
  open/
  done/
  rejected/
```

Das ist deine Inbox für Anforderungen von anderen Projekten und dein Postausgang
für Anforderungen an andere. Leere Ordner mit `.gitkeep` halten (Konvention im
Ökosystem). Der Collector meldet fehlende Pfade als `critical`.

## 3. Cross-Repository-Kommunikation läuft ausschließlich über External Tasks

Wenn du etwas von einem anderen Projekt brauchst (Daten, eine Änderung, eine
Entscheidung) oder ein anderes Projekt etwas von dir braucht: **kein Direkt-Commit
in fremde Repos.** Stattdessen eine Datei nach folgendem, verbindlichem Format
(ECO-ARC-0006) in `external-tasks/open/` des **Ziel-Repos** legen:

Dateiname: `EXT-{SOURCE}-{TARGET}-{YYYYMMDD}-{NNN}.md`

```md
---
id: EXT-{CODE}-KG-20260101-001
title: Kurztitel
status: open
source: {CODE}
target: KG
created: 2026-01-01
requested_by: T.P.K.
priority: medium
affects: [{CODE}, KG]
supersedes: []
---

# EXT-{CODE}-KG-20260101-001 — Kurztitel

## Anlass
## Gewünschte Änderung
## Begründung
## Betroffene Repositories
## Erwartetes Ergebnis
## Hinweise (optional)
```

Bearbeitete Tasks wandern nach `external-tasks/done/` bzw. `rejected/`. Ein
Linter dafür liegt in `kueper-ecosystem/tools/lint-external-tasks/lint.py`.

## 4. Wem gehört was — bevor du eigene „Wahrheiten" anlegst

Bevor du Datenmodelle, Dokumente oder Entitäten anlegst, die auch andere
Projekte betreffen könnten: prüfe, ob es dafür schon eine Source of Truth gibt.

| Bereich | Source of Truth |
|---|---|
| Wissens-/Identitätsgraph, Entitäts-IDs, Mappings zwischen Projekten | `kueper-knowledge-graph` (KG) |
| Kanonische wissenschaftliche/MINT+-Grundlagen | `kueper.com` |
| In-universe-/Archiv-Dokumente des Noxia-Kanons (`OTA-*`) | `overtime-archive.org` (OTA) — **ausschließlich dort** |
| Universums-Primärdaten: Bücher, Figuren, Handlungen, Orte | `noxia-universe` (eigene DB) |
| Zentrale Rechtstexte (Impressum, Datenschutz, AGB) | `kueper-knowledge-graph` (`registry/legal/`) |

Verstößt dein Vorhaben dagegen (du würdest z. B. eigene `OTA-*`-Dokumente
anlegen oder eine zweite Impressums-Wahrheit pflegen), ist das ein Fall für einen
External Task an die zuständige Stelle, nicht für eigenständiges Anlegen. Nur
Inhalte, die **ausschließlich** `{PROJEKT}` betreffen, gehören allein dir.

## 5. Personenbezogene Daten (falls `{PROJEKT}` Accounts/Logins hat)

Falls du eine eigene Nutzerverwaltung (z. B. eigenes Supabase-Projekt) betreibst:

- Melde bei der Registrierung: Region, Auth-Verfahren, Session-Mechanismus
  (Cookie vs. localStorage), welche Tabellen personenbezogene Daten enthalten.
- Die Aufbewahrungspolitik ist ökosystemweit einheitlich (Owner-Vorgabe, Stand
  2026-07-12): **inaktive Konten nach 6 Monaten löschen, unbestätigte
  E-Mail-Adressen nach 1 Monat.** Wenn du Accounts führst, brauchst du einen
  entsprechenden Löschmechanismus — sonst stimmt die zentrale
  Datenschutzerklärung nicht mit deinem Ist-Zustand überein.
- Rechtstexte (Impressum, Datenschutz) nicht selbst verfassen — sie kommen
  zentral aus dem KG. Bei Bedarf per External Task anfordern.

## 6. Namenskonflikte sind nicht automatisch Fehler

Ein Name kann bewusst doppelt vergeben sein (Beispiel: „SSF" ist zugleich reale
Lernplattform und In-universe-Institution — gewollt, aus Immersions- und
Marketinggründen). Bevor du einen scheinbaren Konflikt selbst auflöst
(umbenennen, zusammenlegen), kläre per External Task an `ECO`, ob er beabsichtigt
ist.

## 7. Sichtbarkeit: das Dashboard

Sobald registriert, erscheint `{PROJEKT}` automatisch im Live-Dashboard unter
`https://kueper-ecosystem.vercel.app/dashboard` (Einstieg: `/`, der Werkzeug-Hub)
— Zustand, letzter Push, offene Tasks. Kein Zutun deinerseits nötig; das
Dashboard liest die Registry live.

## 8. Kurz gesagt

1. Erst registrieren lassen (External Task an `ECO`), dann loslegen.
2. Nie direkt in `kueper-ecosystem` oder in fremde Repos schreiben — External
   Tasks statt Direkt-Commits.
3. Vor neuen „Wahrheiten" prüfen, ob es die Zuständigkeit schon gibt (§4).
4. Bei Accounts: Löschfristen einhalten, Rechtstexte zentral anfordern.
5. Bei Unsicherheit über Zuständigkeit oder Namenskonflikten: fragen statt
   entscheiden — External Task an `ECO`.

Vollständige Regeln: `docs/` und `decisions/` in diesem Repository
(`kueper-ecosystem`).

---

## Änderungshistorie dieses Templates

| Datum | Änderung |
|---|---|
| 2026-07-12 | Erstfassung, aus dem Onboarding von `noxia-universe` und `mishkenaz.org` abgeleitet. |
