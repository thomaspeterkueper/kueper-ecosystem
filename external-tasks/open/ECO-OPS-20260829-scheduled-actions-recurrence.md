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

Ein reiner Cron-Umbau innerhalb GitHub Actions wäre keine belastbare Reparatur: beide Workflows sind korrekt terminiert und der Fehler trat bereits nach zwischenzeitlicher Recovery erneut auf.

## Architekturentscheidung 2026-08-29 14:28Z

Freigegeben ist eine robuste Control-Plane-Lösung:

1. Supabase wird primärer Scheduler für Agent Worker und PR Review.
2. GitHub Actions bleibt Executor.
3. Native GitHub-`schedule`-Trigger bleiben als Fallback bestehen.
4. Eine Supabase-Lease plus Cooldown verhindert Doppelverarbeitung und doppelte LLM/API-Kosten.
5. Dispatch/Start/Finish werden als Heartbeat gespeichert und sind über eine Health-RPC prüfbar.

## Implementierungsstand

Auf Branch `automation/external-scheduler-heartbeat` ist die technische Umsetzung vorhanden:

- additive Migration `20260829143000_external_scheduler_control_plane.sql`
- `ecosystem.scheduler_runs` und `ecosystem.scheduler_leases`
- allow-listed Supabase→GitHub-Dispatcher nur für Agent Worker und PR Review
- explizite, idempotente Enable-/Disable-RPCs für `pg_cron`
- Health-RPC zur Stale-Erkennung
- stdlib-only GitHub Guard `tools/scheduler/run_guard.py`
- Lease-/Cooldown-Gating in beiden Workflows vor Node-/Claude-/Agent-Arbeit
- Terminal-Heartbeat mit GitHub Run ID
- Python- und SQL-Smoke-Tests
- Operations-Runbook `docs/operations/external-scheduler.md`

Die Migration ist absichtlich **inert**, bis ein dediziertes Dispatch-Credential vorhanden ist. Es wird dadurch noch kein zusätzlicher Cron-Traffic erzeugt.

## Verbleibender Aktivierungsblocker

Im verbundenen Supabase-Projekt ist derzeit kein Vault-Secret `kueper_github_dispatch_token` vorhanden. Der verbundene GitHub-Connector stellt das zugrunde liegende Token nicht als exportierbares Secret bereit; es darf auch nicht aus einem vorhandenen GitHub-Actions-Secret herauskopiert werden.

**Konkreter nächster Schritt:** Einen dedizierten GitHub-Token bzw. GitHub-App-Credential mit minimaler Berechtigung zum Dispatch von Actions-Workflows für `thomaspeterkueper/kueper-ecosystem` als Supabase-Vault-Secret `kueper_github_dispatch_token` hinterlegen. Danach Migration anwenden/prüfen, `select public.kueper_enable_external_scheduler();` ausführen und mindestens zwei Intervalle je Worker verifizieren.

## Akzeptanz

- Agent Worker und Automated PR Review erzeugen wieder mindestens zwei aufeinanderfolgende erfolgreiche externe Dispatch-Intervalle.
- Ein konkurrierender nativer GitHub-Schedule-Lauf wird durch Lease/Cooldown billig übersprungen.
- `public.kueper_scheduler_health()` zeigt beide Worker nicht stale.
- Ursache bzw. belastbare Recovery-Maßnahme ist dokumentiert.
- Kein zusätzlicher LLM/API-Kostenanstieg durch Doppelverarbeitung.
