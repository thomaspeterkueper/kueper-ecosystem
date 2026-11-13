---
id: ECO-OPS-20261028-offsite-backup
title: Externe Sicherung der drei Supabase-Projekte und Git-Spiegel aller Repos
status: parked
created: 2026-10-28
requested_by: T.P.K.
priority: medium
estimated_effort: medium
type: operations / backup
---

# ECO-OPS-20261028-offsite-backup — Externe Sicherung von Datenbanken und Code

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** parked
**Created:** 2026-10-28
**Type:** operations / backup

## Anlass

- Supabase-Organisation „NoxiaSpace“ (Pro) mit drei Projekten: noxiagame (eu-west-1), kueper-knowledge-graph (eu-west-1), solarsciencefoundation (eu-central-1). Pro hält 7 Tage tägliche Snapshots – im selben Anbieter, nicht herunterladbar, ohne Storage-Dateien und ohne Auth-/Projekt-Konfiguration.
- Alle 23 Repositories liegen ausschließlich bei GitHub unter einem Konto.

## Owner-Handlung (nur Thomas)

1. Cloudflare-R2-Bucket anlegen (Free: 10 GB, 1 Mio. Schreib-/10 Mio. Leseoperationen im Monat, kein Egress). Zugangsdaten als Secrets `BACKUP_R2_*`.
2. Verschlüsselungsschlüssel (restic-Passwort oder age-Schlüssel) erzeugen, als Secret hinterlegen **und offline aufbewahren** – ohne ihn sind die Sicherungen wertlos.
3. Datenbank-Verbindungsstrings (nur lesend, eigener Backup-Nutzer) als Secrets.
4. Für den Git-Spiegel: Zielhost wählen (eigener Forgejo, GitLab.com für private Repos; Codeberg nur für öffentliche Repos) und Push-Zugang als Secret.

## Gewünschte Änderung

1. Workflow `offsite-backup.yml`, täglich nachts:
   - je Projekt `pg_dump --format=custom` (Schema + Daten, ohne Supabase-interne Schemas, die beim Restore stören), verschlüsseln, nach R2.
   - Storage-Buckets per `rclone` inkrementell nach R2.
   - Aufbewahrung: 14 tägliche, 8 wöchentliche, 12 monatliche Stände.
2. Workflow `restore-drill.yml`, monatlich: letzten Dump in ein temporäres Postgres im Runner einspielen, Zeilenzahlen einiger Kerntabellen gegen die Quelle prüfen, Ergebnis in `status/restore-drill.md`.
3. Workflow `git-mirror.yml`, täglich: alle Repos aus `registry/projects.json` mit `git push --mirror` zum Zielhost.
4. Alle drei melden sich über die Heartbeats aus ECO-OPS-20261028-heartbeats.
5. Kurze Wiederherstellungsanleitung `docs/operations/RESTORE.md`.

## Erwartetes Ergebnis

- Jeden Morgen ein verschlüsselter Stand aller drei Datenbanken außerhalb von Supabase.
- Monatlich ein nachgewiesener Wiederherstellungstest.
- Jedes Repo existiert zusätzlich auf einem zweiten Host.

## Hinweise

Supabase-PITR (kostenpflichtiges Add-on) erst erwägen, wenn diese Sicherung läuft.

## Stand 14.11.2026 (Ökosystem-Kreislauf, Claude)

Claude-Status: wartet auf Thomas

Geparkt ohne Umsetzung: Alle drei Workflows liegen unter `.github/` (reviewpflichtig nach `docs/autonomous-loops.md`) und brauchen Secrets, die nur Thomas anlegen kann (Owner-Handlung 1–4). Ohne Ziel und Schlüssel ließe sich nichts testen; ein Workflow mit Platzhaltern würde täglich rot laufen. `docs/operations/RESTORE.md` erst, wenn das Sicherungsformat feststeht.

## Rückfrage

1. Sind R2-Bucket und Verschlüsselungsschlüssel angelegt? Wenn ja: unter welchen Secret-Namen (Vorschlag `BACKUP_R2_ACCOUNT_ID`, `BACKUP_R2_ACCESS_KEY_ID`, `BACKUP_R2_SECRET_ACCESS_KEY`, `BACKUP_R2_BUCKET`, `BACKUP_AGE_RECIPIENT` – nur der öffentliche age-Schlüssel, der private bleibt offline)?
2. Datenbank-Zugang: je Projekt ein eigener lesender Backup-Nutzer als `BACKUP_DB_URL_NOXIA`, `BACKUP_DB_URL_KG`, `BACKUP_DB_URL_SSF` – einverstanden?
3. Git-Spiegel: welcher Zielhost (Forgejo, GitLab.com oder keiner vorerst)?
4. Darf der Ökosystem-Kreislauf danach `offsite-backup.yml`, `restore-drill.yml` und `git-mirror.yml` unter `.github/workflows/` anlegen?
