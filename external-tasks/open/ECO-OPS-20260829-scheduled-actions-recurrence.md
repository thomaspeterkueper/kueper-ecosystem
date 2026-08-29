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

## Stale-Task-Untersuchung 2026-08-29 13:56Z

Der Fehlerzustand ist nach Überschreiten der Zwei-Stunden-Grenze erneut bestätigt: Die GitHub-Actions-Historie enthält weiterhin keinen `event=schedule`-Lauf nach dem Canon-Conflict-Lauf von `2026-08-29T11:40:58Z`, obwohl für Agent Worker und Automated PR Review inzwischen mehrere weitere Cron-Fenster fällig waren.

Der verbundene GitHub-Connector erlaubt das Lesen der Workflow-Runs, stellt in dieser Sitzung aber keinen autorisierten `workflow_dispatch`-/`enable workflow`-Endpunkt bereit. Deshalb kann die vorgesehene reversible Recovery-Maßnahme nicht aus dem Arbeitsloop selbst ausgelöst werden. Ein Code- oder Cron-Umbau wäre ohne nachgewiesene Ursache riskanter und wird ausdrücklich nicht als Ersatz vorgenommen.

**Konkreter nächster Schritt:** Im GitHub-Actions-UI den Enabled-State von `KUEPER Agent Worker V7` und `KUEPER Automated PR Review` prüfen und je einen manuellen Run auf `main` auslösen. Anschließend zwei reguläre Cron-Fenster beobachten. Wenn die manuellen Läufe funktionieren, aber `event=schedule` weiterhin fehlt, Queue-/Concurrency- und Schedule-Deaktivierungsursache weiter untersuchen.

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
