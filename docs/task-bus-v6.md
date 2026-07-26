# KUEPER Task Bus V6

Status: implementation foundation  
Control Plane: `kueper-ecosystem`  
State Plane: bestehende `kueper-knowledge-graph` Supabase/PostgreSQL-Instanz, privates Schema `ecosystem`

## Ziel

V6 verschiebt den operativen Task-Zustand aus GitHub-Dateien in eine transaktionale State Plane. Es wird dafür keine zusätzliche Supabase-Instanz angelegt. Die bestehende Pro-Instanz des Knowledge Graph stellt nur die Infrastruktur bereit; die Task-Schicht bleibt logisch getrennt.

## Schema-Grenze

```text
Supabase: kueper-knowledge-graph
├── public / fachliche KG-Schemata
│   └── Knowledge Graph
└── ecosystem
    ├── tasks
    ├── task_dependencies
    ├── task_runs
    └── task_events
```

`ecosystem` wird nicht als fachlicher Knowledge-Graph-Namespace behandelt und muss nicht als PostgREST-API-Schema exponiert werden. Der Worker nutzt ausschließlich serverseitige `public.kueper_*`-RPCs als Fassade.

## Tabellen

### `ecosystem.tasks`

Zentrale Task-Entität mit Lifecycle, Priorität, Payload/Result, Parent/Root/Depth, Leasing, Retry, Projektzuordnung, Repository-Kontext, Provider-/Model-Metadaten, Research-Scores, Token-/Kosten-Telemetrie und Idempotenz.

### `ecosystem.task_dependencies`

DAG-Kanten zwischen Tasks. Solange eine Abhängigkeit nicht `completed` ist, kann der abhängige Task nicht geclaimt werden.

### `ecosystem.task_runs`

Ein Datensatz pro Worker-Versuch. Dadurch bleiben Retry-Verläufe und Modellkosten nachvollziehbar.

### `ecosystem.task_events`

Append-only Lifecycle-Protokoll für Statusübergänge.

## Server-RPCs

Die RPCs bleiben im `public`-Schema, sind aber nur für `service_role` ausführbar:

- `public.kueper_create_task(...)`
- `public.kueper_claim_task(...)`
- `public.kueper_start_task(...)`
- `public.kueper_heartbeat_task(...)`
- `public.kueper_complete_task(...)`
- `public.kueper_fail_task(...)`
- `public.kueper_park_task(...)`
- `public.kueper_requeue_parked_task(...)`
- `public.kueper_recover_expired_leases()`
- `public.kueper_cancel_task(...)`
- `public.kueper_add_dependency(...)`
- `public.kueper_remove_dependency(...)`

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

Ein Worker darf einen Task nur mit dem zu seinem Claim gehörenden `lease_token` verändern.

## Priorisierung

Der Claim berücksichtigt zunächst `priority`, danach `available_at` und Alter. Dependencies werden vor dem Claim geprüft. V7 ergänzt darauf Provider-, Modell-, Kosten- und Dringlichkeitsrouting.

## GitHub-Beziehung

In der Übergangsphase bleiben V1–V5 aktiv. V6 ersetzt sie nicht schlagartig. GitHub bleibt für Code, Pull Requests und auditierbare External-Task-Projektionen zuständig; Supabase entscheidet operativ, welcher Task wann von welchem Worker bearbeitet werden darf.

## Sicherheit

Browser und Frontends erhalten keinen direkten Zugriff auf das private `ecosystem`-Schema. `anon` und `authenticated` werden auf Schema, Tabellen und zustandsverändernden RPCs explizit gesperrt. `service_role` darf Tabellen lesen, mutiert Zustand aber nur über die RPC-State-Machine.

Der Supabase Secret-/Service-Key darf niemals in Vercel-Clientcode, Ably-Nachrichten, Tasks oder Logs gelangen.

## Migration

Vor dem ersten produktiven Einsatz nur diese konsolidierte Migration ausführen:

```text
supabase/migrations/20260726082000_task_bus_v6_ecosystem_schema.sql
```

Die früheren vier V6-Draft-Migrationen für `public.tasks` wurden vor dem Produktiveinsatz entfernt.

Danach:

```text
supabase/tests/task_bus_v6_smoke.sql
```

Der Smoke-Test läuft vollständig in einer Transaktion und endet mit `ROLLBACK`.

## Smoke-Test

Er prüft:

- idempotente Task-Erzeugung;
- Parent/Root/Depth;
- Dependency Blocking/Unblocking;
- Claim + Lease + Start + Heartbeat;
- Completion;
- Park/Requeue;
- Retry;
- Zyklenschutz;
- Zugriff auf die privaten Tabellen über die RPC-Fassade.

## Nächster Implementierungsschritt

Nach erfolgreicher Migration wird der erste Supabase-Worker als GitHub Action angeschlossen. Er claimt eine begrenzte Zahl von Tasks, wählt über den V7 Provider/Cost Router ein Modell und meldet sämtliche Lifecycle-Übergänge zurück an Supabase. Erst danach wird der Event-Dispatcher vorgeschaltet.
