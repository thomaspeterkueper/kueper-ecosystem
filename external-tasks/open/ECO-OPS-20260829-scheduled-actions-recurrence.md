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

Die letzten sichtbaren geplanten Läufe waren zunächst:

- Agent Worker V7 #866: created `2026-08-29T11:01:55Z`, erfolgreich beendet `11:20:35Z`
- Automated PR Review #80: ursprünglicher Schedule `2026-08-29T09:19:37Z`, nach Retries final erfolgreich `11:48:43Z`
- Canon Conflict Loop #35: schedule `2026-08-29T11:40:40Z`, erfolgreich

Bei Prüfung gegen ca. `2026-08-29T13:12Z` fehlten damit mehrere erwartete Agent-Worker- und PR-Review-Cron-Slots. Normale Repository-Schreibzugriffe funktionierten, und die zuletzt sichtbaren Läufe endeten erfolgreich. Das ist eine Scheduling-/Workflow-Dispatch-Anomalie, nicht einfach ein einzelner fehlgeschlagener Job.

## Stale-Task-Untersuchung 2026-08-29 13:56Z

Der Fehlerzustand wurde nach Überschreiten der Zwei-Stunden-Grenze bestätigt: Die GitHub-Actions-Historie enthielt keinen `event=schedule`-Lauf nach dem Canon-Conflict-Lauf von `2026-08-29T11:40:58Z`, obwohl für Agent Worker und Automated PR Review mehrere Cron-Fenster fällig waren.

## Teil-Recovery 2026-08-29 15:10Z

Die manuelle Recovery wurde im GitHub-Actions-UI ausgelöst:

- Agent Worker V7 #867: `workflow_dispatch`, gestartet `2026-08-29T14:26:02Z`.
- Automated PR Review #81: `workflow_dispatch`, gestartet `14:26:50Z`, erfolgreich beendet `14:49:32Z`.
- Automated PR Review #86: `event=schedule`, erstellt `14:33:24Z`, erfolgreich beendet `14:55:02Z`.
- Autonomous Ecosystem Loop #626 lief wieder regulär per `schedule` um `14:34:17Z` und endete erfolgreich.

Damit war der globale GitHub-Scheduler nicht mehr vollständig ausgefallen. Die Akzeptanz blieb aber unerfüllt, weil für beide Zielworkflows je zwei aufeinanderfolgende reguläre Schedule-Runs fehlen.

## Externe Recovery aktiviert 2026-08-29 15:14Z

Für Draft-PR #45 (`automation/external-scheduler-heartbeat`) wurde das dedizierte Supabase-Vault-Credential `kueper_github_dispatch_token` bereitgestellt. Die additive Control-Plane-Migration war bereits angewendet; die externen `pg_cron`-Jobs wurden daraufhin aktiviert:

- `agent-worker-v7`: `*/15 * * * *`
- `pr-review-agent`: `7,22,37,52 * * * *`

Da `main` den neuen optionalen Input `scheduler_run_id` aus PR #45 noch nicht kennt, wurde die Dispatch-Funktion vorübergehend kompatibel auf die bereits vorhandenen Inputs beschränkt. Nach zwei erwartbaren HTTP-422-Bootstrap-Versuchen liefern alle folgenden GitHub-Dispatches HTTP 204. Zwischen `15:15Z` und `16:07Z` wurden die vorgesehenen Supabase-Slots lückenlos emittiert.

Die vollständige Lease-/Heartbeat-Deduplizierung ist erst wirksam, wenn die Workflow-Änderungen aus PR #45 nach regulärem Review integriert sind. Bis dahin kann der native GitHub-Cron zusätzlich zu einem externen Dispatch erscheinen. Genau dieser Übergangsfall ist inzwischen sichtbar: Agent Worker V7 #876 wurde als `event=schedule` um `15:36:05Z` erzeugt und später `cancelled`, während externe Dispatches parallel laufen. Die bestehende GitHub-Concurrency begrenzt parallele Ausführung, verhindert im Übergang aber nicht sämtliche zusätzlichen Run-Starts.

**Betriebsentscheidung für den Übergang:** Externen Scheduler aktiv lassen, weil er die nachgewiesene GitHub-Scheduler-Lücke zuverlässig überbrückt. Keine Cron-Frequenz erhöhen und den nativen Fallback nicht entfernen. Stattdessen PR #45 regulär validieren; erst mit integriertem Lease-Guard ist die beabsichtigte kostenarme Doppeltrigger-Absicherung vollständig.

## Untersuchung / sichere nächste Schritte

1. PR #45 auf parsebare Workflowdefinitionen, Lease-/Cooldown-Verhalten und Heartbeat-Endzustände vollständig validieren.
2. Keine autonome Merge-Aktion; Integration nur über normalen Review-/Merge-Prozess.
3. Bis dahin externe Dispatch-HTTP-Ergebnisse und GitHub-Concurrency auf echte Doppel-Ausführung/Kosten beobachten.
4. GitHub-Cron als Fallback beibehalten; keine Frequenz erhöhen.
5. Nach Integration von #45 zwei externe Intervalle plus mindestens einen nativen Fallback-Fall mit `skipped`/Lease-Guard verifizieren.

## Akzeptanz

- Agent Worker und Automated PR Review werden auch bei ausbleibendem GitHub-`schedule` zuverlässig ausgelöst.
- Lease/Cooldown verhindert doppelte teure Ausführung bei externem + nativem Trigger.
- Heartbeat/Health-State macht verpasste Intervalle deterministisch sichtbar.
- Ursache oder belastbare Recovery-Maßnahme ist dokumentiert.
- Kein zusätzlicher dauerhafter Kosten-/Frequenzanstieg.
