---
id: ECO-OPS-20261028-secret-health
title: Täglicher Credential-Check und Secrets-Inventur
status: parked
created: 2026-10-28
requested_by: T.P.K.
priority: high
estimated_effort: low
type: operations / credentials
---

# ECO-OPS-20261028-secret-health — Täglicher Credential-Check und Secrets-Inventur

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** parked
**Created:** 2026-10-28
**Type:** operations / credentials

## Anlass

Ein ungültiges `KUEPER_BOT_TOKEN` hat ab ca. 24.10.2026 fünf Workflows lahmgelegt (ECO-OPS-20261028-bot-token-401). Im September hat ein leeres DeepSeek-Guthaben 25 Recherche-Aufträge scheitern lassen (`402 Insufficient Balance` in `research/queue`). Beide Male gab es keine Warnung.

## Gewünschte Änderung

1. **`docs/operations/SECRETS_INVENTORY.md`** anlegen: je Secret Name, Zweck, nutzende Workflows/Projekte, Anbieter, Rechteumfang, Ablaufdatum, wer erneuert. **Niemals Werte.** Ausgangsliste aus den Workflows: `DEEPSEEK_API_KEY`, `KUEPER_BOT_TOKEN`, `AI_GATEWAY_API_KEY`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `KUEPER_WORKFLOW_TOKEN`, Vault-Secret `kueper_github_dispatch_token`; dazu die Vercel-Umgebungsvariablen der Projekte (nur Namen).
2. **Workflow `credential-health.yml`**, täglich und per `workflow_dispatch`:
   - GitHub-Tokens: `GET /user` bzw. `GET /repos/{owner}/kueper-ecosystem` – Status und, falls vorhanden, Header `github-authentication-token-expiration` auswerten.
   - DeepSeek: Guthaben-Endpunkt abfragen, Schwellwert konfigurierbar.
   - AI Gateway und Supabase: einfacher authentifizierter Lesezugriff.
   - Ausgabe nur Status/Ablaufdatum/Restguthaben, nie Werte. Bei Fehler oder Ablauf in < 14 Tagen: Workflow schlägt fehl **und** pflegt genau eine rollierende Task `ECO-OPS-credential-alert.md` (aktualisieren statt neu anlegen).
3. Tests für die Auswertelogik (ohne echte Netzaufrufe).

## Erwartetes Ergebnis

- Inventur-Datei vorhanden und vollständig für alle Workflow-Secrets.
- Ein abgelaufenes oder fast abgelaufenes Token und ein niedriges Guthaben fallen spätestens am nächsten Tag auf.
- Keine Secret-Werte in Logs, Artefakten oder Dateien.

## Hinweise

Zusammen mit ECO-OPS-20261028-heartbeats bekommt Thomas eine Push-Nachricht statt eines stillen Ausfalls.

## Stand 13.11.2026 (Ökosystem-Kreislauf, Claude)

Claude-Status: wartet auf Thomas

- Punkt 1 erledigt: `docs/operations/SECRETS_INVENTORY.md` – alle Workflow-Secrets plus Vault-Token, Dashboard-Umgebung und `OPENAI_API_KEY`, mit aktiven und abgeschalteten Nutzern. Keine Werte. Ablaufdaten und Rechteumfang der PATs sind „offen – Thomas“, weil nur im GitHub-Konto sichtbar.
- Punkt 2 teilweise: Prüflogik als `tools/ops/credential_health.py` (GitHub-Ablauf-Header, DeepSeek-Guthaben, AI-Gateway `/v1/credits`, Supabase-Lesezugriff; `--alert-file` überschreibt genau eine rollierende Datei `ECO-OPS-credential-alert.md`). Der Workflow `credential-health.yml` fehlt noch – `.github/` ist nach `docs/autonomous-loops.md` reviewpflichtig.
- Punkt 3 erledigt: 16 Tests in `tools/ops/test_credential_health.py`, ohne Netzaufrufe, inklusive Prüfung, dass keine Secret-Werte in Ausgabe oder Alert landen.
- Hinweis: Seit der Ablösung durch Claude-Läufe haben `KUEPER_WORKFLOW_TOKEN` keinen und `DEEPSEEK_API_KEY` nur noch einen aktiven Nutzer (`targeted-research.yml`).

## Rückfrage

Darf der Ökosystem-Kreislauf `.github/workflows/credential-health.yml` anlegen (täglich + `workflow_dispatch`, `permissions: contents: write` nur für das Schreiben der Alert-Datei, Secrets `KUEPER_BOT_TOKEN`, `KUEPER_WORKFLOW_TOKEN`, `DEEPSEEK_API_KEY`, `AI_GATEWAY_API_KEY`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY` als Umgebung für `tools/ops/credential_health.py`)? Alternative ohne Workflow: der tägliche Claude-Lauf prüft nur die Inventur, die Tokens selbst kann er nicht testen. Antwort „ja“ oder „Alternative“ genügt; dazu bitte – falls schnell sichtbar – die Ablaufdaten von `KUEPER_BOT_TOKEN` und `KUEPER_WORKFLOW_TOKEN` in die Inventur eintragen oder nennen.
