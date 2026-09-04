# Tools

Ausführbare Hilfsprogramme der Control Plane. Sie prüfen und normalisieren und
geben keine Secrets aus. Produktionswerkzeuge verändern Ziel-Repositories nur
über die jeweils dokumentierten, review-gesteuerten Worker-Pfade. Isolierte
E2E-Harnesses dürfen ausschließlich ihre ausdrücklich festgelegten Test-Branches
und Testpfade verändern.

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

## worker/v74_privileged_e2e.py

Deterministischer, manueller E2E-Harness für den privilegierten
Workflow-Credential-Pfad des V7.4-Workers. Er umgeht Supabase und Provider,
verändert niemals `main` und darf ausschließlich
`test/workflow-credential-smoke` sowie
`.github/workflows/_v74-e2e-target.yml` verwenden.

Der Harness prüft zusätzlich, dass der `origin` vor dem Push tatsächlich auf
`KUEPER_WORKFLOW_TOKEN` umgeschaltet wurde und dass Bot- und Workflow-Token
nicht identisch sind. Ausführung ausschließlich über den zugehörigen manuellen
GitHub-Workflow und mit anschließendem `cleanup`.
