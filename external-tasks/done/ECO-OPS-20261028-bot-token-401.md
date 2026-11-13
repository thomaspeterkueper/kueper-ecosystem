---
id: ECO-OPS-20261028-bot-token-401
title: KUEPER_BOT_TOKEN liefert HTTP 401 – fünf Workflows ausgefallen
status: done
created: 2026-10-28
requested_by: T.P.K.
priority: critical
estimated_effort: low
type: operations / credentials
Erledigt: 2026-11-13
---

# ECO-OPS-20261028-bot-token-401 — KUEPER_BOT_TOKEN liefert HTTP 401

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** done
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
- Ablaufdatum: **kein Ablauf** (laut Thomas, 28.10.2026). In die Secrets-Inventur als „läuft nicht ab – jährlich manuell rotieren, nächste Rotation Oktober 2027“ übernehmen.
- Offen: Governance-Sweep, Autonomous Loop und OTA-Workflows beim nächsten Lauf prüfen.

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

## Abschluss 13.11.2026 (Ökosystem-Kreislauf, Claude)

Status: done  
Erledigt: 2026-11-13  
Umgesetzt: Erneuerung durch Thomas am 28.10.2026; Wirkung nachgeprüft.

- Governance-Sweep: `status/governance-sweep.md` vom 13.11.2026 enthält keine `repository_unreachable`-Funde mehr (nur 2 Info-Funde `task_addressed_to_eco`).
- Autonomous Ecosystem Loop: Läufe seit 10.11.2026 grün.
- Automated PR Review: 23 grüne Läufe seit 10.11.2026; seit 13.11.2026 abgeschaltet und durch den Claude-Lauf „Ökosystem-Kreislauf“ ersetzt (`docs/operations/claude-laeufe.md`).
- `research/queue`: wieder neue Einträge (z. B. RES-20261113-477236C3, RES-20261113-AA5ECC0E).
- OTA Tech Object Audit: Checkout des OTA mit dem Token gelingt wieder. Der Workflow scheitert seit 13.11.2026 aus einem **anderen** Grund – Metadatenfehler in OTA-TEC-0112 bis -0121 (`objectId` ≠ `mappings.noxia.objectId`); als Umschlag an OTA gemeldet (`.kueper/outbox/ota-tec-0112-0121-objectid-mismatch.json`).
- Nicht nachgeholt: nachträgliches Review von PRs, die in der Ausfallzeit 24.–28.10.2026 ohne Review gemergt wurden. Das Review läuft künftig im Ökosystem-Kreislauf.
- Vorbeugung bleibt offen in ECO-OPS-20261028-secret-health und ECO-OPS-20261028-heartbeats.
