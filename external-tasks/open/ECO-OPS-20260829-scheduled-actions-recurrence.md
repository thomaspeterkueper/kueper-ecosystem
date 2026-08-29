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

## Teil-Recovery 2026-08-29 15:10Z

Die manuelle Recovery wurde im GitHub-Actions-UI ausgelöst:

- Agent Worker V7 #867: `workflow_dispatch`, gestartet `2026-08-29T14:26:02Z`; beim letzten Check noch in Bearbeitung.
- Automated PR Review #81: `workflow_dispatch`, gestartet `14:26:50Z`, erfolgreich beendet `14:49:32Z`.

Danach ist mindestens ein regulärer Review-Cron wieder erschienen:

- Automated PR Review #86: `event=schedule`, erstellt `14:33:24Z`, erfolgreich beendet `14:55:02Z`.
- Auch Autonomous Ecosystem Loop #626 lief wieder regulär per `schedule` um `14:34:17Z` und endete erfolgreich.

Damit ist der globale GitHub-Scheduler nicht mehr vollständig ausgefallen. Die Akzeptanz ist aber noch nicht erfüllt: Für Agent Worker und Automated PR Review müssen jeweils mindestens zwei aufeinanderfolgende reguläre Schedule-Runs beobachtet werden. Insbesondere kann der lange manuelle Agent-Worker-Lauf die eigenen Cron-Runs aufgrund der bestehenden Concurrency-Gruppe zunächst seriell aufstauen.

Parallel wurde als robuste Abhilfe Draft-PR #45 (`automation/external-scheduler-heartbeat`) angelegt: Supabase-basierter externer Dispatch, Heartbeat und Lease/Cooldown-Deduplizierung, GitHub-Cron bleibt Fallback. Die additive Control-Plane-Migration ist bereits angewendet, die externen Cronjobs bleiben fail-closed deaktiviert, bis das dedizierte Vault-Secret `kueper_github_dispatch_token` vorhanden ist.

Beim ersten Branch-Check von PR #45 erzeugten die geänderten Workflowdateien Parse-Fehlläufe ohne Jobs. Ein YAML-Plain-Scalar mit `: ` im `echo`-Schritt wurde auf dem PR-Branch in Blocksyntax korrigiert; weitere Validierung des geänderten Heads läuft über den normalen PR-/Actions-Lifecycle. Alte Parse-Runs werden nicht erneut gestartet.

**Konkreter nächster Schritt:** Zwei weitere reguläre Cronfenster für beide Zielworkflows beobachten. Separat PR #45 validieren und erst nach vorhandenem dediziertem Vault-Credential den externen Scheduler aktivieren. Keine Merge-Aktion autonom ausführen.

## Untersuchung / sichere nächste Schritte

1. Zwei aufeinanderfolgende `event=schedule`-Läufe für Agent Worker und Automated PR Review bestätigen.
2. PR #45 auf parsebare Workflowdefinitionen, Lease-/Cooldown-Verhalten und fail-closed Aktivierung prüfen.
3. Nach Bereitstellung des dedizierten Dispatch-Credentials externen Scheduler aktivieren und echten Dispatch Agent Worker + PR Review testen.
4. GitHub-Cron als Fallback beibehalten; keine Frequenz erhöhen.
5. Bei erneutem Ausfall Heartbeat/Health-RPC statt bloßer Historienbeobachtung verwenden.

## Akzeptanz

- Agent Worker und Automated PR Review erzeugen wieder mindestens zwei aufeinanderfolgende `event=schedule`-Runs gemäß ihren bestehenden Cron-Ausdrücken.
- Ursache oder belastbare Recovery-Maßnahme ist dokumentiert.
- Kein zusätzlicher Kosten-/Frequenzanstieg.
