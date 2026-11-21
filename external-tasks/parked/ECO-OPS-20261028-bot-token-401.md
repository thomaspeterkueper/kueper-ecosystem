---
id: ECO-OPS-20261028-bot-token-401
title: KUEPER_BOT_TOKEN liefert HTTP 401 – fünf Workflows ausgefallen
status: parked
created: 2026-10-28
requested_by: T.P.K.
priority: critical
estimated_effort: low
type: operations / credentials
---

# ECO-OPS-20261028-bot-token-401 — KUEPER_BOT_TOKEN liefert HTTP 401

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** parked
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

## Nachprüfung 28.10.2026 (Agent, ab ca. 14:20 UTC)

### Wirkung der Token-Erneuerung

| Workflow | Lauf (UTC) | Ergebnis |
|---|---|---|
| Automated PR Review | 40689277061, 12:37 | Fehlschlag am Schritt „Discover direct PRs from registry“ (alter Token), unmittelbar vor der Erneuerung |
| Automated PR Review | 40691372914, 12:52 | success, inklusive Registry-Discovery |
| Automated PR Review | 40700385241, 13:52 | success, alle Schritte |
| Automated PR Review | 40702784117, 14:07 | billig übersprungen (Scheduler-Lease, erwartete Doppeltrigger-Unterdrückung; kein Token-Fehler) |
| Autonomous Ecosystem Loop | 40702567557, 14:05 | success, alle Schritte (u. a. Re-Evaluate, Ingest, Outbox) |

Der Schritt „Discover direct PRs from registry“ ruft `GET /repos/{repo}/pulls` für die Registry-Repositories in alphabetischer Reihenfolge auf und bricht bei jeder Nicht-200-Antwort ab (`tools/review/direct_pr_intake.py`, `github_open_prs`/`discover`). Lauf 40700385241 lief mit `--max-prs 50`; bei derzeit 56 offenen PRs wurde der Cap erreicht. Abgefragt wurden dadurch 19 der 21 Repositories, darunter `thomaspeterkueper/overtime-archive.org` (OTA) und alle Repositories mit offenen PRs. Wegen des Caps `--max-prs 50` nicht mehr abgefragt wurden `thomas-kueper.de` und `zereya.de`; für diese beiden und als Gesamtbestätigung bleibt der Governance-Sweep am 29.10. maßgeblich.

### Warum kein eigener `workflow_dispatch` möglich war

Dem Agentenprozess werden GitHub-Zugangsdaten bewusst entzogen (`tools/worker/agent_worker_v74.py:56`: `KUEPER_BOT_TOKEN`, `KUEPER_WORKFLOW_TOKEN`, `GH_TOKEN`, `GITHUB_TOKEN`); `gh auth status` ist im Agenten unauthentifiziert. Die Scheduler-Control-Plane erlaubt Dispatch nur für `agent-worker-v7` und `pr-review-agent` (`supabase/migrations/20260829143000_external_scheduler_control_plane.sql`, `kueper_scheduler_dispatch`); einen generischen Dispatch gibt es nicht. Ein manueller Anstoß der vier Workflows war aus dieser Umgebung daher nicht möglich.

### Restverifikation durch die planmäßigen Läufe

Governance-Sweep und OTA Tech Object Audit sind tägliche Cron-Jobs; die beiden Research-Loops ebenso. Nächste planmäßige Läufe (UTC):

| Workflow | Nächster Lauf | Erwartung |
|---|---|---|
| Knowledge Research Loop | 2026-10-29, 03:23 (`23 3 * * *`) | neue Datei unter `research/queue` |
| OTA Workqueue Research | 2026-10-29, 03:53 (`53 3 * * *`) | neue Datei unter `research/queue` |
| OTA Tech Object Audit | 2026-10-29, 04:47 (`47 4 * * *`) | „Checkout OTA source“ erfolgreich, Audit grün |
| Governance-Sweep | 2026-10-29, 06:05 (`5 6 * * *`) | `status/governance-sweep.md` ohne `repository_unreachable` |

`status/governance-sweep.md` enthält bis dahin unverändert die 21 alten 401-Funde vom 28.10., 12:42 UTC (letzter Lauf vor der Erneuerung); der letzte Eintrag in `research/queue` stammt vom 23.10.2026 (`RES-20261023-C4FA4833.json`). Beides ist erwartet und kein neuer Fehler. **Der Task bleibt bis zur bestätigten Wiederherstellung geparkt und wird nicht vorab geschlossen.** Sollte einer der vier Läufe am 29.10. nicht grün sein, bleibt der Task offen und der Fehlschlag ist als neuer Incident zu erfassen.

### Nachträgliche Reviews der ohne KUEPER-Review gemergten PRs

Ermittlung: GitHub-Suche über alle Repositories des Owners nach gemergten PRs im Ausfallfenster (`is:pr is:merged merged:2026-10-23..2026-10-28 user:thomaspeterkueper`); für jeden Treffer Prüfung, ob ein Kommentar „KUEPER automated review“ vorliegt. 20 PRs ohne Review wurden anhand des vollständigen Diffs nachträglich geprüft. Ein Schreibzugriff auf andere Repositories war nicht möglich; die Review-Ergebnisse sind hier dokumentiert.

| Repository | PRs | Ergebnis |
|---|---|---|
| noxiagame | #513, #515, #516, #517, #518, #519, #521, #522, #523, #524, #527 | keine blockierenden Funde |
| kueper.com | #21 | keine Funde |
| kueper.com | #22 | 1 Governance-Fund (niedrig) |
| kueper.com | #24 | 1 Formatierungsfund (niedrig) |
| solarsciencefoundation | #76, #77, #78, #80, #81, #82 | keine blockierenden Funde |

**kueper.com #22 („SCI: Gold durch Kerntransmutation …“):** Die neuen Dateien `external-tasks/open/KUE-EXT-GOLD-KG-2026.md` und `external-tasks/open/KUE-EXT-GOLD-SSF-ACADEMY-2026.md` sind an KG bzw. SSF adressiert, liegen aber im `external-tasks/open` von kueper.com und nutzen kein kanonisches ECO-ARC-0006-Frontmatter (`id`, `source`, `target`, `status`). Der Ingest überspringt Dateien mit abweichendem `target`; ohne Frontmatter würde eine solche Datei als Aufgabe an kueper.com selbst eingespeist. Die beiden Aufträge erreichen KG/SSF damit nicht. Inhaltlich sind Artikel und Auftragstexte sauber und evidenzbewusst.

**kueper.com #24 („Research: covert consciousness …“):** Im Abschnitt „Studiendesign und methodische Präzisierung“ stehen literale `\n\n`-Escapes im Markdown; sie erscheinen als Text statt als Absatzumbrüche. Inhaltlich sind Quellen, Endpunkte und Grenzen sauber getrennt.

**noxiagame #517:** Für die Legacy-Datei `EarthSurfaceLogisticsConsole.tsx` wird die ESLint-Regel `react-hooks/set-state-in-effect` gezielt abgeschaltet; im PR begründet und auf diese Datei beschränkt. Kein blockierender Fund, aber eine bewusste Prüf-Ausnahme.

**Querschnitt:** In allen 20 Diffs keine Secrets, kein `eval`/`exec`, keine deaktivierten Tests oder `.only`-Marker, keine neuen Workflow-Berechtigungen.

### Ergebnis gegenüber den Abnahmekriterien (Stand 29.10.2026, 00:20 UTC)

| Kriterium | Stand |
|---|---|
| PR Review grün | erfüllt (40691372914, 40700385241) |
| Autonomous Loop grün | erfüllt (40702567557) |
| OTA Tech Object Audit grün | **offen** – Lauf 29.10. 04:47 UTC prüfen |
| Governance-Sweep ohne `repository_unreachable` | **offen** – Lauf 29.10. 06:05 UTC prüfen; alter Bericht (21 × HTTP 401) bleibt bis dahin stehen |
| Neue Einträge in `research/queue` | **offen** – Läufe 29.10. 03:23/03:53 UTC prüfen; letzter Eintrag vom 23.10. |
| PRs ohne Review nachträglich geprüft | erfüllt (20 PRs) |

**Gesamtstatus:** Drei Abnahmekriterien sind noch nicht verifiziert. Der Task ist deshalb `parked`, nicht `done`; eine Schließung erfolgt erst nach bestätigter Wiederherstellung (siehe `## Rückfrage`).

### Nebenbefund (nicht Teil dieses Tasks)

Beim Prüfen des Ingests fiel auf: `tools/loop/ingest_external_tasks.py` zählt auch bereits vorhandene Tasks gegen `KUEPER_MAX_EXTERNAL_INGEST` (Standard 5) und bricht dann die Schleife ab. Da `ecosystem` in der Registry zuerst kommt und dort derzeit 39 offene External Tasks liegen, werden pro Lauf nur die ersten fünf Dateien betrachtet; später sortierte Tasks anderer Repositories kommen erst an die Reihe, wenn der Kopf der Liste abgearbeitet ist. Das ist ein vom Token unabhängiger Engpass. Ob der Deckel als reine Arbeits-/Kostengrenze bewusst so gewählt ist, ist eine eigene Entscheidung und wurde hier nicht geändert.

## Rückfrage

**Blocker:** Drei Abnahmekriterien lassen sich erst nach den planmäßigen Läufen am 29.10.2026 prüfen (Knowledge Research Loop 03:23 UTC, OTA Workqueue Research 03:53 UTC, OTA Tech Object Audit 04:47 UTC, Governance-Sweep 06:05 UTC). Vor 06:05 UTC belegen `status/governance-sweep.md` und `research/queue` nur den alten Ausfallzustand; daraus folgt weder Erfolg noch Misserfolg. Der Task bleibt deshalb `parked` und wird nicht vorab auf `done` gesetzt.

**Wiederaufnahme:** Der Parked-Reevaluation-Loop (`tools/loop/reevaluate_parked.py`, alle 15 Minuten im Autonomous Ecosystem Loop) prüft diesen Task automatisch und öffnet ihn wieder, sobald der Repository-Zustand die fehlende Voraussetzung zeigt:

- `status/governance-sweep.md` wurde nach dem 29.10.2026, 06:05 UTC neu erzeugt und enthält keine `repository_unreachable`-Funde mehr;
- in `research/queue` liegen neue Einträge mit Datum ab 29.10.2026.

**Abschließende Abnahme:** Nach der Wiederaufnahme prüft der nächste Task-Lauf zusätzlich die vier Workflow-Ergebnisse vom 29.10.2026 (über die öffentliche GitHub-Actions-API, dafür sind keine Schreib-Credentials nötig):

1. Knowledge Research Loop, 03:23 UTC – grün und neue Datei unter `research/queue`;
2. OTA Workqueue Research, 03:53 UTC – grün und neue Datei unter `research/queue`;
3. OTA Tech Object Audit, 04:47 UTC – grün, insbesondere Schritt „Checkout OTA source“;
4. Governance-Sweep, 06:05 UTC – grün und `status/governance-sweep.md` ohne `repository_unreachable`.

Erst wenn alle vier Läufe grün sind und beide Repository-Belege vorliegen, wird der Task auf `done` gesetzt. Schlägt einer der Läufe fehl, bleibt der Task offen und der Fehlschlag wird als neuer Incident erfasst; ein fehlgeschlagener Lauf erfüllt die Abnahmekriterien nicht nachträglich. Ein gerouteter Follow-up-Request an `ECO` ist nach `docs/autonomous-loops.md` ausgeschlossen (Source und Target wären identisch); die Verifikation bleibt daher Bestandteil dieses Tasks.

## Hinweise

Verhindern, dass das wieder unbemerkt passiert: ECO-OPS-20261028-secret-health und ECO-OPS-20261028-heartbeats.
