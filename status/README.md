# Status

`snapshot.json` ist die maschinengenerierte Ausgabe von
`tools/collector/collect.py` (ECO-ARC-0005). Er hält den zuletzt ermittelten,
normalisierten Ist-Zustand aller registrierten Projekte fest.

Der Snapshot ist **kein** Source of Truth für fachliche Projektdaten. Er ist eine
Momentaufnahme des beobachteten Zustands und wird beim nächsten Collector-Lauf
überschrieben. Er enthält niemals Secret-Werte.

Feldstruktur je Projekt: `overall` (healthy|degraded|critical|unknown) plus
Einzel-`checks` (repository_reachable, open_pull_requests,
governance_required_paths, external_tasks_open, integrations).
