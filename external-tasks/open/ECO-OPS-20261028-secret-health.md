---
id: ECO-OPS-20261028-secret-health
title: Täglicher Credential-Check und Secrets-Inventur
status: open
created: 2026-10-28
requested_by: T.P.K.
priority: high
estimated_effort: low
type: operations / credentials
---

# ECO-OPS-20261028-secret-health — Täglicher Credential-Check und Secrets-Inventur

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** open
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
