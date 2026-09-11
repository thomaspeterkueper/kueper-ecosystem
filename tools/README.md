# Tools

Ausführbare Hilfsprogramme der Control Plane. Sie prüfen und normalisieren,
sie verändern keine Ziel-Repositories und geben keine Secrets aus.

## collector

`collector/collect.py` — GitHub-Collector v1 (ECO-ARC-0005, erster
Umsetzungsumfang). Vergleicht `registry/projects.json` (Soll) mit dem
GitHub-Ist-Zustand und schreibt einen normalisierten Snapshot.

```bash
GH_TOKEN=<token> python3 tools/collector/collect.py > status/snapshot.json
```

Geprüft werden: Erreichbarkeit, Default Branch, letzter Push, offene PRs,
Governance-Pflichtpfade, offene External Tasks, registrierte Integrationsziele.
Zustandswerte: `ok | warning | error | unknown | not_applicable`.
Gesamtstatus: `healthy | degraded | critical | unknown`. Ein grüner Gesamtstatus
wird nie aus fehlenden Daten abgeleitet.

## lint-external-tasks

`lint-external-tasks/lint.py` — Linter für das kanonische External-Task-Format
(ECO-ARC-0006). Prüft Dateiname, Frontmatter gegen
`schemas/external-task.schema.json` und Pflicht-Sektionen.

```bash
python3 tools/lint-external-tasks/lint.py <datei.md> ...
python3 tools/lint-external-tasks/lint.py --all <repo-root>
```

Nur stdlib, kein Netzwerk, exit 1 bei Verstoß (CI-tauglich).

## scheduler

`scheduler/check_health.py` — deterministischer, rein lesender Health-Check
für die geplanten Workflows `KUEPER Agent Worker V7` und
`KUEPER Automated PR Review`. Primär über die Supabase-Health-RPC
`kueper_scheduler_health()`; ohne Supabase-Credentials Fallback auf die
GitHub-Actions-Run-Historie mit Slot-Abdeckung gegen die bekannten
Cron-Kadenzen. Exit-Code: `0` healthy, `1` stale, `2` Konfigurations-/
Transportfehler (fail-closed, nie ein falsch-positives „healthy").

```bash
python3 tools/scheduler/check_health.py           # auto: Supabase, sonst GitHub
python3 tools/scheduler/check_health.py --json    # maschinenlesbar
```

Abgedeckte Slots beweisen nur, dass der Trigger (externer Scheduler oder
GitHub-Cron) gefeuert hat — abgebrochene oder queued Runs zählen mit.
Der zuletzt gesehene `event=schedule`-Lauf wird separat ausgewiesen, damit
ein Stall des nativen GitHub-Cron sichtbar bleibt, auch wenn der externe
Scheduler die Kadenz trägt.
