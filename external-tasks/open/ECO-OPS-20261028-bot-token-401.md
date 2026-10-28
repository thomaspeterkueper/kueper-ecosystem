---
id: ECO-OPS-20261028-bot-token-401
title: KUEPER_BOT_TOKEN liefert HTTP 401 – fünf Workflows ausgefallen
status: open
created: 2026-10-28
requested_by: T.P.K.
priority: critical
estimated_effort: low
type: operations / credentials
---

# ECO-OPS-20261028-bot-token-401 — KUEPER_BOT_TOKEN liefert HTTP 401

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** open
**Created:** 2026-10-28
**Type:** operations / credentials

## Anlass

Seit etwa 24.10.2026 meldet der Governance-Sweep alle 21 registrierten Repositories als nicht erreichbar (HTTP 401, `status/governance-sweep.md`, erzeugt 27.10.). Alle betroffenen Workflows nutzen `secrets.KUEPER_BOT_TOKEN`:

| Workflow | Befund (Läufe 24.–28.10.2026) | scheiternder Schritt |
|---|---|---|
| KUEPER Automated PR Review | 89 von 96 Läufen gescheitert | „Discover direct PRs from registry“ |
| KUEPER Autonomous Ecosystem Loop | 6 von 6 gescheitert | „Re-evaluate parked tasks“ |
| OTA Tech Object Audit | gescheitert | „Checkout OTA source“ |
| OTA Workqueue Research | gescheitert | „Select evidence-worthy OTA workqueue items“ |
| Governance-Sweep | läuft, findet aber nur 401 | – |

Folge: Seit 23.10.2026 kommen keine neuen Einträge mehr in `research/queue`, und offene External Tasks werden nicht mehr in den Task-Bus übernommen. Vier Tage lang hat das niemand bemerkt.

Der Agent Worker V7 läuft weiter erfolgreich (94/94); er nutzt den Token offenbar nicht für die betroffenen Schritte.

## Owner-Handlung (nur Thomas)

1. Neues Fine-grained-Token für `KUEPER_BOT_TOKEN` anlegen (Rechte wie bisher, nur die registrierten Repos) und in den Repository-Secrets von `kueper-ecosystem` ersetzen.
2. **Ablaufdatum notieren** – in die Secrets-Inventur aus ECO-OPS-20261028-secret-health (nur Datum, nie der Wert).

## Stand 28.10.2026, 13:50 Uhr

- Owner-Handlung erledigt: Token von Thomas regeneriert und Secret ersetzt.
- Nachweis: PR Review Run 40691372914 (12:52 UTC) erfolgreich, inklusive „Discover direct PRs from registry“.
- Offen: Ablaufdatum in die Secrets-Inventur übernehmen; Governance-Sweep, Autonomous Loop und OTA-Workflows beim nächsten Lauf prüfen.

## Gewünschte Änderung

Nach der Erneuerung durch Thomas:

- Je einen Lauf von PR Review, Autonomous Loop, OTA Tech Object Audit und Governance-Sweep per `workflow_dispatch` anstoßen und Ergebnis prüfen.
- Prüfen, ob in der Ausfallzeit PRs ohne Review gemergt wurden; falls ja, nachträglich reviewen.

## Erwartetes Ergebnis

- Die vier Workflows laufen wieder grün.
- `status/governance-sweep.md` zeigt keine `repository_unreachable`-Funde mehr.
- Neue Einträge erscheinen wieder in `research/queue`.

## Hinweise

Verhindern, dass das wieder unbemerkt passiert: ECO-OPS-20261028-secret-health und ECO-OPS-20261028-heartbeats.
