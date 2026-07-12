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
