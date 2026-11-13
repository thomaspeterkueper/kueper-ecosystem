# Secrets-Inventur

```
Stand:   13.11.2026 – erste Fassung (ECO-OPS-20261028-secret-health)
Pflege:  bei jedem neuen, umbenannten oder entfernten Secret
```

Diese Datei listet **Namen, Zweck und Nutzer** aller Credentials der Control Plane. **Sie enthält niemals Werte** – auch keine gekürzten, maskierten oder Präfixe.

Quelle der Zuordnung: `secrets.*` in `.github/workflows/*.yml` und Umgebungsvariablen in `tools/` und `app/` (Stand `main`, 13.11.2026). Workflow-Zustand laut GitHub-API am selben Tag; seit 13.11.2026 sind sechs Sprachmodell-Workflows abgeschaltet und durch Claude-Läufe ersetzt (`docs/operations/claude-laeufe.md`).

Felder „Ablauf“ und „Rechteumfang“ sind nur dort eingetragen, wo sie aus dem Repository belegbar sind. Alles mit „offen – Thomas“ kann nur der Owner im jeweiligen Anbieter-Konto nachsehen.

## GitHub-Actions-Secrets (`kueper-ecosystem`)

| Secret | Zweck | Nutzende Workflows (aktiv) | Nutzende Workflows (abgeschaltet) | Anbieter | Rechteumfang | Ablauf | Erneuert durch |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `KUEPER_BOT_TOKEN` | Schreib-/Lesezugriff auf die registrierten Repos (Routing, Sweep, Audit, Branch-Hygiene) | `autonomous-loop.yml`, `governance-sweep.yml`, `branch-hygiene-dry-run.yml`, `ota-tech-object-audit.yml`, `scion-science-handoff-tests.yml`, `targeted-research.yml` | `agent-worker-v7.yml`, `canon-conflict-loop.yml`, `knowledge-research-loop.yml`, `ota-evidence-sweep.yml`, `ota-workqueue-research.yml`, `pr-review-agent.yml` | GitHub (PAT) | offen – Thomas (fine-grained? welche Repos?) | offen – Thomas | Thomas |
| `KUEPER_WORKFLOW_TOKEN` | Workflow-Dispatch aus dem Agent Worker | – | `agent-worker-v7.yml` | GitHub (PAT) | offen – Thomas | offen – Thomas | Thomas |
| `DEEPSEEK_API_KEY` | Sprachmodell-Aufrufe (Worker, Review, Recherche) | `targeted-research.yml` (manuell) | `agent-worker-v7.yml`, `canon-conflict-loop.yml`, `knowledge-research-loop.yml`, `ota-evidence-sweep.yml`, `ota-workqueue-research.yml`, `pr-review-agent.yml` | DeepSeek | API-Schlüssel, Guthaben vorab | kein Ablauf, aber Guthaben (402 bei leerem Konto) | Thomas |
| `AI_GATEWAY_API_KEY` | Vercel AI Gateway (Recherche mit Exa, `tools/research/agent-with-exa.mjs`) | `exa-gateway-smoke.yml`, `targeted-research.yml` | `knowledge-research-loop.yml`, `ota-evidence-sweep.yml`, `ota-workqueue-research.yml` | Vercel | Gateway-Schlüssel, Guthaben vorab | kein Ablauf bekannt, aber Guthaben | Thomas |
| `SUPABASE_URL` | Adresse des Task-Bus-Projekts (`ecosystem.*`) | `autonomous-loop.yml` | `agent-worker-v7.yml`, `pr-review-agent.yml` | Supabase | kein Geheimnis im engeren Sinn, aber als Secret geführt | – | – |
| `SUPABASE_SECRET_KEY` | Server-Schlüssel für den Task-Bus | `autonomous-loop.yml` | `agent-worker-v7.yml`, `pr-review-agent.yml` | Supabase | volle Datenbankrechte (Secret Key umgeht RLS) | offen – Thomas | Thomas |

Automatisch von GitHub gestellt und nicht zu pflegen: `GITHUB_TOKEN`.

## Weitere Credentials außerhalb der Actions-Secrets

| Name | Ort | Zweck | Nutzer | Anbieter | Rechteumfang | Ablauf | Erneuert durch |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `kueper_github_dispatch_token` | Supabase Vault | Externer Scheduler stößt GitHub-Workflows an (`docs/operations/external-scheduler.md`) | `public.kueper_enable_external_scheduler()` und Cron-Jobs | GitHub (PAT) | soll nur Workflow-Dispatch in `kueper-ecosystem` dürfen | offen – Thomas | Thomas |
| `SUPABASE_SERVICE_ROLE_KEY` bzw. `SUPABASE_SECRET_KEY` | Vercel-Umgebung des Dashboards | `app/api/traces`, `app/api/operations` | Control-Plane-Dashboard | Supabase | volle Datenbankrechte | offen – Thomas | Thomas |
| `SUPABASE_URL` | Vercel-Umgebung des Dashboards | wie oben | Control-Plane-Dashboard | Supabase | – | – | – |
| `VERCEL_OIDC_TOKEN` | Vercel-Laufzeit (automatisch) | Ersatz für `AI_GATEWAY_API_KEY` in `agent-with-exa.mjs`, wenn auf Vercel ausgeführt | Recherche-Agent | Vercel | kurzlebig, automatisch | automatisch | – |
| `OPENAI_API_KEY` | Umgebung beim manuellen Aufruf | `tools/loop/orchestrate.py` verlangt ihn; in keinem Workflow gesetzt | nur manuell | OpenAI | offen – Thomas | offen – Thomas | Thomas |

## Andere Projekte

Secrets der übrigen registrierten Repos (z. B. `noxiagame` mit Vercel- und Supabase-Umgebung, Cron-Routen) sind hier **nicht** erfasst; jedes Projekt führt seine Inventur selbst. Die Vercel-Umgebungsvariablen aller Projekte kann nur Thomas vollständig einsehen.

## Prüfung

`tools/ops/credential_health.py` prüft die Secrets der Control Plane ohne Werte auszugeben (Status, Ablaufdatum, Restguthaben) – siehe dort. Ein täglicher Workflow dafür ist noch nicht eingerichtet (ECO-OPS-20261028-secret-health, Rückfrage).

## Bekannte Altlasten

- `DEEPSEEK_API_KEY` und `SUPABASE_*` werden nach der Ablösung durch Claude-Läufe nur noch von `targeted-research.yml` bzw. `autonomous-loop.yml` gebraucht. Werden diese Workflows ebenfalls umgestellt, können die Secrets gelöscht werden.
- `KUEPER_WORKFLOW_TOKEN` hat seit Abschaltung von `agent-worker-v7.yml` keinen aktiven Nutzer.
- `OPENAI_API_KEY` (`tools/loop/orchestrate.py`) ist in keinem Workflow verdrahtet.
