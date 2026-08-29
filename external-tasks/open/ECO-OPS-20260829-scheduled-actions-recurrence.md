# Ecosystem Ops: erneuter Ausfall geplanter Agent-/Review-Läufe nach Recovery

**Origin:** KUEPER Arbeitsloop
**Target:** kueper-ecosystem
**Status:** open
**Created:** 2026-08-29
**Priority:** high
**Related:** abgeschlossener früherer Task `ECO-OPS-20260829-scheduled-actions-stall.md`

## Befund

Der zuvor als recovered archivierte Scheduling-Stall ist erneut sichtbar.

Die Workflowdefinitionen auf `main` sind weiterhin aktiv terminiert:

- `KUEPER Agent Worker V7`: `*/15 * * * *`
- `KUEPER Automated PR Review`: `7,22,37,52 * * * *`

Die letzten sichtbaren geplanten Läufe sind jedoch:

- Agent Worker V7 #866: created `2026-08-29T11:01:55Z`, erfolgreich beendet `11:20:35Z`
- Automated PR Review #80: ursprünglicher Schedule `2026-08-29T09:19:37Z`, nach Retries final erfolgreich `11:48:43Z`
- Canon Conflict Loop #35: schedule `2026-08-29T11:40:40Z`, erfolgreich

Bei Prüfung gegen ca. `2026-08-29T13:12Z` fehlen damit mehrere erwartete Agent-Worker- und PR-Review-Cron-Slots. Normale Repository-Schreibzugriffe funktionieren, und die zuletzt sichtbaren Läufe endeten erfolgreich. Das ist daher eine Scheduling-/Workflow-Dispatch-Anomalie, nicht einfach ein einzelner fehlgeschlagener Job.

## Untersuchung / sichere nächste Schritte

1. Prüfen, ob beide Workflows im Actions-UI weiterhin als enabled angezeigt werden.
2. Je einen manuellen `workflow_dispatch` auf `main` auslösen, ohne Parameteränderung.
3. Danach mindestens zwei reguläre Cron-Fenster beobachten.
4. Wenn manuelle Dispatches funktionieren, Cron aber erneut ausbleibt: Repository-/Workflow-Event-Historie und mögliche GitHub-Schedule-Deaktivierung bzw. Queue-/Concurrency-Effekte untersuchen.
5. Keine Cron-Frequenzen erhöhen und keinen No-op-Commit als künstlichen Trigger erzeugen, solange die Ursache nicht bestimmt ist.

## Akzeptanz

- Agent Worker und Automated PR Review erzeugen wieder mindestens zwei aufeinanderfolgende `event=schedule`-Runs gemäß ihren bestehenden Cron-Ausdrücken.
- Ursache oder belastbare Recovery-Maßnahme ist dokumentiert.
- Kein zusätzlicher Kosten-/Frequenzanstieg.
