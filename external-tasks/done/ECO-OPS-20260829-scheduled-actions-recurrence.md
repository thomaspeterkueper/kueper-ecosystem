# Ecosystem Ops: erneuter Ausfall geplanter Agent-/Review-Läufe nach Recovery

**Origin:** KUEPER Arbeitsloop  
**Target:** kueper-ecosystem  
**Status:** done  
**Created:** 2026-08-29  
**Completed:** 2026-08-30  
**Priority:** high

## Ausgangslage

Die nativen GitHub-`schedule`-Läufe von Agent Worker V7 und Automated PR Review waren wiederholt ausgeblieben. Die Recovery-Anforderung verlangte eine belastbare externe Auslösung, Doppeltrigger-Schutz und beobachtbare Start-/Finish-Zustände.

## Umgesetzte Lösung

Am 2026-08-30 wurde die Scheduler-Control-Plane auf dem aktuellen `main` integriert und produktiv verifiziert:

- Supabase `pg_cron` ist primärer Scheduler.
- GitHub Actions bleibt Executor.
- Native GitHub-`schedule`-Trigger bleiben als Fallback bestehen.
- `scheduler_run_id` wird beim externen `workflow_dispatch` mitgegeben.
- Vor teurer Ausführung wird eine Supabase-gestützte Lease mit Cooldown erworben.
- Doppeltrigger werden vor Worker-/Reviewer-Ausführung billig übersprungen.
- Start- und Finish-Heartbeat werden in `ecosystem.scheduler_runs` gespeichert.
- `github_run_id` wird beim Abschluss persistiert.
- `public.kueper_scheduler_health()` macht verpasste bzw. veraltete Läufe sichtbar.

Die aktuelle Umsetzung wurde über PR #57 integriert; ein unmittelbar entdeckter YAML-Parserfehler wurde über PR #58 korrigiert. Der veraltete Draft PR #45 wurde anschließend als superseded geschlossen.

## End-to-End-Verifikation

Kontrollierte Produktionsdispatches ergaben:

- `agent-worker-v7`: `dispatch_requested → started → succeeded`, GitHub Run ID `33311554115`.
- `pr-review-agent`: `dispatch_requested → started → succeeded`.
- Beide Health-Einträge waren nach Abschluss `stale = false`.
- GitHub nahm die Supabase-Dispatches mit HTTP 204 an.
- Die externen Cron-Jobs wurden danach wieder aktiviert:
  - Agent Worker: `*/15 * * * *`
  - PR Review: `7,22,37,52 * * * *`

Damit sind die technischen Akzeptanzkriterien dieses Incidents erfüllt. Provider-spezifische Billing-Probleme sind ein separater Ausführungs-/Providerzustand und kein Scheduler-Defekt.
