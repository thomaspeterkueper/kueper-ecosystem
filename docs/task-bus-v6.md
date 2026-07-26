# KUEPER Task Bus V6

Status: implementation foundation  
Control Plane: `kueper-ecosystem`  
State Plane: Supabase/PostgreSQL

## Ziel

V6 verschiebt den operativen Task-Zustand aus GitHub-Dateien in eine transaktionale State Plane. GitHub bleibt für Code, Pull Requests und auditierbare External-Task-Projektionen zuständig; die Datenbank entscheidet, welcher Task wann von welchem Worker bearbeitet werden darf.

## Tabellen

### `tasks`

Zentrale Task-Entität mit Lifecycle, Priorität, Payload/Result, Parent/Root/Depth, Leasing, Retry, Projektzuordnung, Repository-Kontext, Provider-/Model-Metadaten, Research-Scores, Token-/Kosten-Telemetrie und Idempotenz.

### `task_dependencies`

DAG-Kanten zwischen Tasks. Solange eine Abhängigkeit nicht `completed` ist, kann der abhängige Task nicht geclaimt werden.

### `task_runs`

Ein Datensatz pro Worker-Versuch. Dadurch bleiben Retry-Verläufe und Modellkosten nachvollziehbar.

### `task_events`

Append-only Lifecycle-Protokoll für Statusübergänge.

## Server-RPCs

- `kueper_create_task(...)` — idempotentes Erzeugen mit Parent/Root/Depth und Dependencies.
- `kueper_claim_task(...)` — atomarer Claim mit `FOR UPDATE SKIP LOCKED` und Lease.
- `kueper_start_task(...)` — Claim → Running.
- `kueper_heartbeat_task(...)` — Lease verlängern.
- `kueper_complete_task(...)` — terminaler Erfolg inklusive Ergebnis/Kosten.
- `kueper_fail_task(...)` — Retry oder terminales Failed abhängig von `max_attempts`.
- `kueper_park_task(...)` — Blockade mit optionaler Owner-Entscheidung.
- `kueper_requeue_parked_task(...)` — automatische Wiederaufnahme nur ohne Owner-Gate.
- `kueper_recover_expired_leases()` — Watchdog für abgestürzte Worker.
- `kueper_cancel_task(...)` — explizites Abbrechen nicht-terminaler Tasks.

## Worker-Protokoll

```text
create task
   ↓
pending
   ↓ claim
claimed + lease_token
   ↓ start
running
   ├─ heartbeat ───────────────┐
   │                           │
   ├─ complete → completed     │
   ├─ fail → pending/failed    │
   └─ park → parked            │
                               │
watchdog ← expired lease ──────┘
```

Ein Worker darf einen Task nur mit dem zu seinem Claim gehörenden `lease_token` verändern. Dadurch kann ein später übernommener Task nicht versehentlich von einem alten Worker abgeschlossen werden.

## Priorisierung

Der Claim berücksichtigt zunächst `priority`, danach `available_at` und Alter. Dependencies werden vor dem Claim geprüft. Ein späterer Router kann zusätzliche Scores in die Producer-Entscheidung oder in getrennte Queues einbringen, ohne das Grundschema zu ändern.

## GitHub-Beziehung

In der Übergangsphase bleiben V1–V5 aktiv. V6 ersetzt sie nicht schlagartig.

Geplanter Übergang:

1. Supabase State Plane aufsetzen.
2. Einen neuen Worker gegen Supabase betreiben.
3. bestehende GitHub-Loops parallel beobachten.
4. Cross-Repo External Tasks aus Supabase nach GitHub spiegeln.
5. nach verifiziertem Betrieb GitHub-Dateien aus der Dispatch-Rolle nehmen.

Damit gibt es keinen Big-Bang-Wechsel.

## Sicherheit

Browser und Frontends erhalten keinen direkten Schreibzugriff auf den Task Bus. Producer-Endpunkte, Dispatcher und Worker verwenden serverseitige Credentials. Die `service_role` darf niemals an Vercel-Clientcode oder Ably-Nachrichten gelangen.

## Smoke-Test

`supabase/tests/task_bus_v6_smoke.sql` testet innerhalb einer zurückgerollten Transaktion:

- idempotente Task-Erzeugung;
- Parent/Root/Depth;
- Dependency Blocking/Unblocking;
- Claim + Lease + Start + Heartbeat;
- Completion;
- Park/Requeue;
- Retry;
- Zyklenschutz.

## Nächster Implementierungsschritt

Nach erfolgreicher Migration wird der erste Supabase-Worker als GitHub Action gebaut. Er claimt genau einen Task, wählt über einen Provider Router ein Modell und meldet sämtliche Lifecycle-Übergänge zurück an Supabase. Erst danach wird der Event-Dispatcher vorgeschaltet.
