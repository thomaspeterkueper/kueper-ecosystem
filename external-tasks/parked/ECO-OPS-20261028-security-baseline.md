---
id: ECO-OPS-20261028-security-baseline
title: Kostenlose Sicherheitsprüfungen für alle Repos aktivieren
status: parked
created: 2026-10-28
requested_by: T.P.K.
priority: low
estimated_effort: low
type: operations / security
---

# ECO-OPS-20261028-security-baseline — Kostenlose Sicherheitsprüfungen

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** parked
**Created:** 2026-10-28
**Type:** operations / security

## Anlass

17 der 23 Repos sind öffentlich. Für öffentliche Repos sind CodeQL-Code-Scanning, Secret-Scanning und Dependabot-Warnungen/-Sicherheitsupdates kostenlos; für private Repos nicht. Viele Workflows arbeiten mit mächtigen Tokens – ein versehentlich eingechecktes Secret wäre gravierend.

## Gewünschte Änderung

1. Öffentliche Repos: Dependabot-Warnungen und -Sicherheitsupdates, Secret-Scanning und CodeQL (Standard-Setup) aktivieren. Mit `gh api` als Skript `tools/ops/enable-security.sh`, das den Stand je Repo ausgibt (idempotent).
2. Private Repos (knowledge-graph, buecherwelten, kueper-engineering, kueper-products, noxia-universe, noxia-realtime): `gitleaks` als PR-Workflow und Renovate oder Dependabot-Versionsupdates.
3. Ergebnis je Repo als Tabelle in `docs/operations/SECURITY_BASELINE.md`.

## Erwartetes Ergebnis

- Jedes Repo hat Secret-Erkennung und Abhängigkeits-Warnungen.
- Neue Funde landen im wöchentlichen Gesundheitsbericht (ECO-OPS-20261028-weekly-health).

## Stand 13.11.2026 (Ökosystem-Kreislauf, Claude)

Claude-Status: wartet auf Thomas (Admin-Token und privater Rollout)

- Punkt 1 umgesetzt als `tools/ops/enable-security.sh`: idempotentes `gh api`-Skript für alle aktivierten Registry-Repositories plus `config/security-baseline.json`. Öffentliche Repos: Dependabot-Alerts/-Sicherheitsupdates, Secret Scanning samt Push-Schutz, CodeQL-Standard-Setup. Private Repos: Dependabot-Alerts/-Sicherheitsupdates sowie Prüfung auf `gitleaks`-Workflow und Dependabot-/Renovate-Versionsupdates. Optionen `--check`, `--json`, `--markdown`, `--repo`, `--no-push-protection`; Exitcodes 0/1/2. Das Skript schreibt keine Dateien in Ziel-Repositories und gibt keine Token-Werte aus.
- Punkt 2 vorbereitet: Vorlagen `tools/ops/templates/gitleaks.yml` und `tools/ops/templates/dependabot.yml`. Die Dateien müssen im jeweiligen privaten Repo liegen; die Control Plane schreibt sie nicht. Für KG, ENG und PROD wurden Folge-Requests in `.kueper/outbox/` erzeugt. `buecherwelten` und `noxia-realtime` haben keinen routbaren Zielcode; `noxia-universe` lag außerhalb der Drei-Follow-up-Grenze. Dort bleibt es bei der Owner-Handlung.
- Punkt 3 umgesetzt: `docs/operations/SECURITY_BASELINE.md` mit Zielbild, Tabelle je Repo, Werkzeug, Vorlagen, Weekly-Health-Schnittstelle und offenen Punkten. Scope derzeit 22 Repos (21 Registry plus `noxia-realtime`); die in der Task genannte Zahl von 23 Repos ist damit nicht gedeckt.
- Tests: 16 deterministische Tests in `tools/ops/test_enable_security.py` mit zustandsbehaftetem Fake-gh (Idempotenz, Check-Modus ohne Schreibzugriffe, private Pflichtdateien, CodeQL 409/422, Fehlerisolation, keine Token-Ausgabe).
- Weekly Health: `external-tasks/open/ECO-OPS-20261028-weekly-health.md` um Punkt 6 ergänzt; `enable-security.sh --check --json` ist die Schnittstelle.
- Nicht erfolgt: Aktivierung mit einem Admin-Token (im Agentenlauf am 13.11.2026 war kein GitHub-Token verfügbar) und Anlage der Workflow-/Dependabot-Dateien in den privaten Repos (fremde Source of Truth).

## Rückfrage

1. Darf der Ökosystem-Kreislauf die Aktivierung mit einem Admin-Token ausführen, sobald eines verfügbar ist? `KUEPER_BOT_TOKEN` hat vermutlich keine Admin-/Security-Rechte (`docs/operations/SECRETS_INVENTORY.md`); ein separates `SECURITY_ADMIN_TOKEN` wäre sauberer. Antwort „KUEPER_BOT_TOKEN“ oder „eigenes Secret“ genügt.
2. Sind die drei Folge-Requests für KG, ENG und PROD richtig priorisiert, oder sollen zuerst `noxia-universe` bzw. `buecherwelten` versorgt werden? Für `buecherwelten` und `noxia-realtime` gibt es keinen routbaren Zielcode.
3. Welches ist das 23. Repository aus der Task? Es ist weder in `registry/projects.json` noch in `config/security-baseline.json` enthalten. Name und Sichtbarkeit genügen.
