---
id: ECO-OPS-20261028-heartbeats
title: Heartbeats und Erreichbarkeits-Monitore für Worker, Crons und Websites
status: parked
created: 2026-10-28
requested_by: T.P.K.
priority: high
estimated_effort: low
type: operations / monitoring
---

# ECO-OPS-20261028-heartbeats — Heartbeats und Erreichbarkeits-Monitore

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** parked
**Created:** 2026-10-28
**Type:** operations / monitoring

## Anlass

Ausfälle werden heute erst bemerkt, wenn jemand nachsieht: PR Review war ab ca. 24.10.2026 zu 93 % rot; `status/snapshot.json` stammt vom 19.07.2026. Es gibt keine externe Überwachung.

## Owner-Handlung (nur Thomas)

1. Konto bei einem Heartbeat-/Uptime-Dienst anlegen (Vorschlag Better Stack Free: 10 Monitore, 10 Heartbeats, 30-s-Takt; UptimeRobot Free ist nur für nicht kommerzielle Nutzung).
2. Monitore für: noxiagame (Produktion), thomas-kueper.de, kueper.com, ecosystem-Dashboard, solarsciencefoundation.
3. Je Heartbeat eine URL anlegen und als Secret hinterlegen: `HEARTBEAT_AGENT_WORKER`, `HEARTBEAT_PR_REVIEW`, `HEARTBEAT_RESEARCH_LOOP`, `HEARTBEAT_GOVERNANCE_SWEEP`.
4. Push-Benachrichtigung aufs Handy aktivieren.

## Gewünschte Änderung

- Kleines Hilfsskript `tools/ops/heartbeat.sh` (stdlib/curl): ruft die URL aus einer Umgebungsvariablen auf; **fehlt das Secret, tut es nichts** (kein Fehler).
- Als letzter Schritt in Agent Worker V7, PR Review, Knowledge Research Loop und Governance-Sweep einbauen – nur bei Erfolg (`if: success()`), bei Fehler optional die `/fail`-Variante.
- Heartbeat-Intervall je Workflow in `docs/operations/` dokumentieren (Worker 15 Min., PR Review 15 Min., Sweep täglich).
- Status-Collector prüfen: Warum ist `status/snapshot.json` seit 19.07.2026 nicht mehr erneuert? Entweder wieder einplanen oder als ersetzt durch `/api/status` dokumentieren.

## Erwartetes Ergebnis

- Bleibt ein Heartbeat aus oder ist eine Seite nicht erreichbar, bekommt Thomas innerhalb von 30 Minuten eine Nachricht.
- Workflows ohne gesetzte Secrets laufen unverändert.

## Hinweise

Für noxiagame (minütlicher Cron `/api/cron/transits`, stündlicher `population`) gilt dasselbe – siehe EXT-ECO-NOXIA-20261028-003.

## Stand 13.11.2026 (Ökosystem-Kreislauf, Claude)

Claude-Status: wartet auf Thomas

- Skript erledigt: `tools/ops/heartbeat.sh` (tut ohne Secret nichts, gibt die URL nie aus, bricht bei Netzfehler nichts ab), 6 Tests in `tools/ops/test_heartbeat.py`.
- Dokumentation erledigt: `docs/operations/heartbeats.md` mit Intervallen und Vorlage für den Workflow-Schritt.
- Status-Collector geklärt: `collect.py` läuft in keinem Workflow, `snapshot.json` ist seit 19.07.2026 eingefroren; `/api/status` rechnet live. Als ersetzt dokumentiert (`status/README.md`).
- Lage geändert: Agent Worker, PR Review und Knowledge Research Loop sind seit heute abgeschaltet. Heartbeats lohnen sich nur noch für `governance-sweep.yml`, `autonomous-loop.yml` und `ota-tech-object-audit.yml`.
- Offen: Owner-Handlung 1–4 (Konto, Monitore, Secrets, Push) und der Einbau in die Workflows (`.github/`, reviewpflichtig).

## Rückfrage

1. Darf der Ökosystem-Kreislauf den Heartbeat-Schritt in `governance-sweep.yml`, `autonomous-loop.yml` und `ota-tech-object-audit.yml` einbauen (Secrets `HEARTBEAT_GOVERNANCE_SWEEP`, `HEARTBEAT_AUTONOMOUS_LOOP`, `HEARTBEAT_OTA_AUDIT`; ohne gesetztes Secret wirkungslos)? „ja“ genügt.
2. Sollen auch die beiden Claude-Läufe einen Heartbeat senden? Dann bräuchte jeder Lauf die Heartbeat-URL im Auftragstext – sie ist kein starkes Geheimnis, wäre dann aber im Lauf-Prompt sichtbar. „ja“ oder „nein“.
