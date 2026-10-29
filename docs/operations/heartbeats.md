# Heartbeats

`tools/ops/heartbeat.sh <SECRET_NAME>` pingt die URL aus der gleichnamigen Umgebungsvariable (curl). Fehlt das Secret, passiert nichts. Aufruf nur bei Erfolg (`if: success()`).

| Workflow | Secret | Intervall |
|---|---|---|
| Agent Worker V7 | `HEARTBEAT_AGENT_WORKER` | 15 Min. |
| KUEPER Automated PR Review | `HEARTBEAT_PR_REVIEW` | 15 Min. |
| Knowledge Research Loop | `HEARTBEAT_RESEARCH_LOOP` | gemäß Cron des Workflows |
| Governance-Sweep | `HEARTBEAT_GOVERNANCE_SWEEP` | täglich |

Owner-Handlung (Thomas): Dienst-Konto anlegen, Heartbeat-URLs als Repository-Secrets hinterlegen, Push-Benachrichtigung aktivieren. Die Grace-Period im Dienst etwas über dem Intervall setzen.
