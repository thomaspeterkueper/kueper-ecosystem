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

## governance-sweep.json / governance-sweep.md

Ausgabe von `tools/governance/sweep.py` (ECO-ARC-0027/0034), täglich per
`governance-sweep.yml`-Workflow aktualisiert. Prüft rein strukturell — keine
Bewertung von Inhalten, keine automatische Entscheidung: fehlende
Index-Einträge in `decisions/README.md`, „superseded"-Entscheidungen ohne
erkennbaren Verweis auf die ablösende Fassung, nahezu identische Titel unter
aktiven Entscheidungen (der ECO-ARC-0029/0033-Fall), Registry-Einträge mit
ungültiger Rolle/Codeformat/hängenden Integrationszielen, Abweichungen
zwischen Registry-Codes und der ECO-ARC-0006-Codetabelle, fehlende
Governance-Pflichtpfade je Repository, sowie offene, an `ECO` adressierte
Tasks systemweit.

Der Sweep entscheidet nichts selbst. Bei **neuen** Funden (nicht bereits im
vorherigen Bericht enthalten) legt der Workflow automatisch einen Task in
`external-tasks/open/` dieses Repositories an (`EXT-ECO-ECO-*`) — wiederholte
Meldung desselben, noch nicht behobenen Fundes erzeugt keinen weiteren Task.
