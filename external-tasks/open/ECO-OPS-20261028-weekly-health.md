---
id: ECO-OPS-20261028-weekly-health
title: Wöchentlicher Gesundheitsbericht – wo das System hakt
status: open
created: 2026-10-28
requested_by: T.P.K.
priority: medium
estimated_effort: medium
type: operations / continuous improvement
---

# ECO-OPS-20261028-weekly-health — Wöchentlicher Gesundheitsbericht

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** open
**Created:** 2026-10-28
**Type:** operations / continuous improvement

## Anlass

Thomas will, dass das System besser wird. Dafür fehlt bisher ein Blick auf **Trends**: Die Daten liegen alle vor (GitHub-Läufe, PRs, Tasks, Research-Queue, Task-Bus), werden aber nirgends zusammengeführt. Stichprobe vom 28.10.2026:

- noxiagame: 19 offene PRs, ältester vom 30.09.; mehr als 400 Branches.
- kueper-ecosystem: 13 offene PRs; PR Review zu 93 % rot (Token).
- `research/queue`: 210 Einträge – 80 `candidate-pr`, 39 `needs-review`, 36 `validation-error`, 24 `queued`; seit 23.10. kein neuer Eintrag. Häufigster Grund für `needs-review` im Oktober: „lacks a strong source type marker“ beim Profil `philosophy-comparative`.
- noxiagame-CI: 95 % grün (gut).

## Gewünschte Änderung

Workflow `weekly-health.yml` (montags früh, plus `workflow_dispatch`), stdlib-Python, nur lesend:

1. Je registriertem Repo: Erfolgsquote je Workflow (7 Tage), längste Rotphase, offene PRs nach Alter (0–7, 8–30, > 30 Tage), Anzahl Branches, offene External Tasks nach Alter.
2. Research-Queue: Verteilung nach Status, Top-3-Fehlergründe, Durchsatz je Woche, Anteil `needs-review` je Evidenzprofil.
3. Task-Bus (über die vorhandene aggregierte RPC, keine Ledger-Details): erledigt/geparkt/fehlgeschlagen je Woche, Anteil Fallback (sobald ECO-OPS-20261028-llm-fallback steht).
4. Ausgabe `status/health-weekly.md` mit Vorwoche zum Vergleich (Pfeile ↑/↓) und **höchstens drei** konkreten Verbesserungsvorschlägen, abgeleitet aus Schwellwerten (z. B. Workflow < 80 % grün, PR > 30 Tage, Profil mit > 40 % `needs-review`).
5. Überschreitet etwas einen Schwellwert, eine rollierende Task `ECO-OPS-health-alert.md` pflegen.

## Erwartetes Ergebnis

- Jeden Montag ein kurzer Bericht, der in zwei Minuten zeigt, wo es hakt und was als Nächstes dran ist.
- Keine Schreibrechte außer auf `status/` und die rollierende Task.

## Hinweise

Der vorhandene Branch-Hygiene-Dry-Run (`branch-hygiene-dry-run.yml`) kann seine Zahlen in diesen Bericht liefern.
