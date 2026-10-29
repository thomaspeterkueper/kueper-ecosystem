---
id: ECO-OPS-20261028-heartbeats
title: Heartbeats und Erreichbarkeits-Monitore für Worker, Crons und Websites
status: open
created: 2026-10-28
requested_by: T.P.K.
priority: high
estimated_effort: low
type: operations / monitoring
---

# ECO-OPS-20261028-heartbeats — Heartbeats und Erreichbarkeits-Monitore

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** open
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

## Stand 29.10.2026 (Routine)

- Umgesetzt: `tools/ops/heartbeat.sh`, Heartbeat-Schritt (`if: success()`) in Agent Worker V7, PR Review, Research Loop, Governance-Sweep; Doku in `docs/operations/heartbeats.md`.
- Offen: Owner-Handlung (Dienst, Secrets, Push), `/fail`-Variante optional, Status-Collector-Prüfung (`status/snapshot.json`), noxiagame-Crons.
