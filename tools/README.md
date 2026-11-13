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

## ops

`ops/credential_health.py` — Credential-Check der Control Plane
(ECO-OPS-20261028-secret-health). Je Secret ein lesender Aufruf (GitHub,
DeepSeek-Guthaben, AI-Gateway-Guthaben, Supabase); Ausgabe nur Status,
Ablaufdatum und Restguthaben, niemals Werte. Fehlende Secrets gelten als
`missing`, nicht als Fehler.

```bash
python3 tools/ops/credential_health.py [--json] [--alert-file external-tasks/open/ECO-OPS-credential-alert.md]
python3 -m unittest discover -s tools/ops -p 'test_*.py'
```

Exit 1 bei `error`, `expiring` (< 14 Tage) oder `low`. Inventur:
`docs/operations/SECRETS_INVENTORY.md`.

`ops/weekly_health.py` — Wöchentlicher Gesundheitsbericht
(ECO-OPS-20261028-weekly-health). Je registriertem Repo Erfolgsquote je
Workflow (7 Tage), längste Rotphase, PRs nach Alter, Branches; dazu offene
External Tasks nach Alter und die Research-Queue (Status, Top-3-Fehlergründe,
Durchsatz je Woche, `needs-review` je Evidenzprofil). Vergleicht mit dem
letzten Bericht (↑/↓) und nennt höchstens drei Vorschläge aus Schwellwerten.
Nur lesend; ohne Token entfallen die GitHub-Kennzahlen („nicht erhoben“).

```bash
GH_TOKEN=<token> python3 tools/ops/weekly_health.py [--alert-file external-tasks/open/ECO-OPS-health-alert.md] [--no-github]
```

Schreibt `status/health-weekly.md` und `status/health-weekly.json`; die
Alert-Task wird überschrieben bzw. entfernt, sobald nichts mehr auffällt.
