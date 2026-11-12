---
id: ECO-OPS-20261028-security-baseline
title: Kostenlose Sicherheitsprüfungen für alle Repos aktivieren
status: open
created: 2026-10-28
requested_by: T.P.K.
priority: low
estimated_effort: low
type: operations / security
---

# ECO-OPS-20261028-security-baseline — Kostenlose Sicherheitsprüfungen

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** open
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
