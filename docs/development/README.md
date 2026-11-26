# Entwicklungsstand – kueper-ecosystem

```
Stand: 25.11.2026 (Pilot nach docs/development-checkpoints.md, EXT-NOXIA-ECO-20261124-001)
Letzte verifizierte Revision von main: f7c93ce (25.11.2026)
```

Einstieg nach [`docs/development-checkpoints.md`](../development-checkpoints.md). Offene Aufgaben stehen in `external-tasks/open/`, offene PRs auf GitHub – hier nur Verweise und Stand.

| Workstream | Status | Checkpoint |
|---|---|---|
| Hybridbetrieb Claude-Läufe / DeepSeek-Workflows | integriert, laufend gepflegt | unten |
| Automatisiertes PR-Review (erstes Review) | integriert, Nacharbeit offen | unten |
| OTA → KUE-Zuordnung und Begutachtung | integriert, laufend | unten |
| Drive-Spiegel KUE/OTA | integriert, laufend | unten |
| CI-/Worker-Effizienz (#136) | implementiert, nicht gemergt | unten |
| Entwicklungscheckpoints (diese Regel) | integriert (Stufe 1), Einführung läuft | unten |

## Hybridbetrieb Claude-Läufe / DeepSeek-Workflows

- Ziel: DeepSeek-Workflows erledigen Routinetasks, Claude-Läufe die Oberstufe (Kreislauf, Recherche-Prüfung, KG-Merge).
- Status: integriert; Regeln werden bei Entscheidungen von Thomas fortgeschrieben.
- Branch / PR: direkt über `claude/…`-Branches mit Merge.
- Letzte verifizierte Revision: `c7209bb` (24.11.2026, Version 2.4.0).
- Tests: keine eigenen; Workflows laufen unverändert.
- Offene Schritte: Tasks mit „Claude-Status: wartet auf Thomas“ in `external-tasks/parked/`.
- Risiken / offene Fragen: keine bekannten.
- Abschlusskriterien: laufender Betrieb, kein Abschluss vorgesehen.
- Maßgebliche Dokumente: [`docs/operations/claude-laeufe.md`](../operations/claude-laeufe.md).

## Automatisiertes PR-Review (erstes Review)

- Ziel: Agent-PRs werden vor dem Merge unabhängig geprüft (PASS / CHANGES_REQUIRED / REVIEW_ERROR).
- Status: integriert; letzte Änderung Fairness der PR-Erkennung (#152).
- Branch / PR: #152 gemergt; #137 (Abbruch überholter Testläufe) offen.
- Letzte verifizierte Revision: `33511f4` (25.11.2026, `.github/workflows/pr-review-agent.yml`).
- Tests: `review-head-dedup-tests.yml`, Unittests unter `tools/review/`.
- Offene Schritte: #137.
- Risiken / offene Fragen: Einzelne Läufe enden mit REVIEW_ERROR, wenn das Review-Token den kombinierten Commit-Status eines Ziel-Repositories nicht lesen darf (HTTP 403, zuletzt `overtime-archive.org`, 25.11.2026). Token-Rechte sind Einstellungssache von Thomas.
- Abschlusskriterien: keine REVIEW_ERROR aus Rechtefehlern.
- Maßgebliche Dokumente: [`docs/architecture/AUTOMATED_PR_REVIEW_AGENT.md`](../architecture/AUTOMATED_PR_REVIEW_AGENT.md).

## OTA → KUE-Zuordnung und Begutachtung

- Ziel: werkneutrale Realteile aus OTA-Dokumenten nach kueper.com verlagern (ECO-ARC-0037/0038).
- Status: integriert; Begutachtung läuft täglich, Requests an KUE über `external-tasks/`.
- Letzte verifizierte Revision: `fb4bc74` (25.11.2026, `status/ota-kue-zuordnung.md`).
- Tests: keine maschinellen; Prüfberichte unter `reviews/`.
- Offene Schritte: offene `EXT-OTA-KUE-*` in `kueper.com/external-tasks/open/`.
- Risiken / offene Fragen: Quellenprüfung 2026-11 mit ungeprüften Angaben (`status/quellenpruefung-2026-11.md`).
- Abschlusskriterien: alle Zeilen der Zuordnungsinventur haben einen Stand.
- Maßgebliche Dokumente: [`status/ota-kue-zuordnung.md`](../../status/ota-kue-zuordnung.md).

## Drive-Spiegel KUE/OTA

- Ziel: Drive als Lese- und Sicherungskopie; GitHub bleibt Source of Truth.
- Status: integriert, Abgleich durch geplante Aufgabe.
- Letzte verifizierte Revision: `82bc09d` (25.11.2026, `status/drive-mirror.json`).
- Offene Schritte: Altbestand `onlyInDrive` – Regeln in `docs/operations/claude-laeufe.md` („Drive-Fassungen selbst entscheiden“).
- Abschlusskriterien: Altbestand vollständig nach `checked` überführt.
- Maßgebliche Dokumente: [`docs/drive-exchange-standard.md`](../drive-exchange-standard.md).

## CI-/Worker-Effizienz (#136)

- Ziel: weniger Leerlauf und doppelte Läufe in den Actions.
- Status: implementiert, nicht gemergt (Änderungen unter `.github/` brauchen Freigabe von Thomas).
- Branch / PR: #134, #135, #137 (Drafts).
- Offene Schritte: Issue #136.
- Abschlusskriterien: PRs gemergt, Laufzeiten im Wochenbericht gesunken.

## Entwicklungscheckpoints

- Ziel: jeder Workstream ist ohne Chat-Historie auffindbar.
- Status: integriert (Regel und dieser Pilot); Einstiege in KG, SSF und kueper.com angelegt (26.11.2026), NOXIA offen (`noxiagame/external-tasks/open/EXT-ECO-NOXIA-20261125-001.md`).
- Branch / PR: `claude/EXT-NOXIA-ECO-20261124-001`.
- Offene Schritte: Umschläge in `.kueper/outbox/` (`…--development-checkpoint.json`).
- Abschlusskriterien: Einstieg in allen Repositories mit laufender Entwicklung; danach Entscheidung über eine maschinelle Abdeckungsprüfung.
- Maßgebliche Dokumente: [`docs/development-checkpoints.md`](../development-checkpoints.md).
