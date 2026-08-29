# Ecosystem Ops: Scheduled GitHub Actions seit 04:08 UTC ausgeblieben

**Origin:** KUEPER Arbeitsloop
**Target:** kueper-ecosystem
**Status:** open
**Created:** 2026-08-29
**Type:** operations / scheduling

## Befund

Am 2026-08-29 gegen 08:12 UTC zeigt die nach `event=schedule` gefilterte GitHub-Actions-Historie als jüngsten geplanten Lauf:

- `KUEPER Agent Worker V7`, Run #865, erzeugt 2026-08-29T04:08:22Z, erfolgreich abgeschlossen.

Seitdem ist in der Schedule-Historie kein weiterer `schedule`-Event sichtbar, obwohl mindestens folgende Workflows auf dem Default-Branch `main` viertelstündlich terminiert sind:

- `.github/workflows/agent-worker-v7.yml`: `*/15 * * * *`
- `.github/workflows/pr-review-agent.yml`: `7,22,37,52 * * * *`
- `.github/workflows/autonomous-loop.yml`: `7,22,37,52 * * * *`

Push- und manuell/ereignisgetriggerte Actions funktionieren weiterhin; unter anderem waren Credential-Smoke-Test, Source-Revision-Pinning, Research Config Check und OTA Evidence Sweep erfolgreich. GitHub Status meldete Actions bei der Prüfung als operational. Das spricht gegen einen allgemeinen CI-Ausfall und für einen repository-/workflow-spezifischen Scheduling-Zustand.

## Auswirkung

- neue Agenten-/Research-PRs können länger als vorgesehen ohne Automated PR Review bleiben;
- `external-tasks/open/` werden vom Agent Worker / Autonomous Loop nicht im vorgesehenen Takt aufgenommen;
- Stale-Task- und Review-Lifecycle können dadurch verzögert werden.

## Bereits geprüft

- Workflow-Dateien existieren auf `main` und enthalten weiterhin die oben genannten Cron-Auslöser.
- Letzte sichtbare geplante Runs waren erfolgreich; kein fehlgeschlagener Run liegt vor, den man einfach erneut starten könnte.
- Der frühere Workflow-Credential-Blocker ist nicht mehr aktuell: der Credential-Smoke-Test lief erfolgreich.
- Der verbundene GitHub-Connector bietet in diesem Lauf keinen sicheren `workflow_dispatch`-/Enable-Endpunkt. Deshalb wurde kein Cron auf Verdacht verändert und kein künstlicher No-op-Commit erzeugt.

## Sicherer nächster Schritt

1. In GitHub Actions einmal `KUEPER Agent Worker V7` und `KUEPER Automated PR Review` per **Run workflow** auf `main` auslösen.
2. Danach bis zum nächsten vorgesehenen Cron-Slot prüfen, ob wieder `event=schedule`-Runs erzeugt werden.
3. Falls nicht: im Actions-UI prüfen, ob die Workflows deaktiviert sind; gegebenenfalls **Enable workflow** ausführen.
4. Erst wenn Dispatch/Enable ohne Wirkung bleibt, die Workflow-Aktivierung bzw. GitHub-Schedule-Registrierung weiter untersuchen. Keine Änderung der fachlichen Agentenlogik oder Cron-Frequenz ohne separaten Befund.

## Abschlusskriterium

Der Auftrag kann nach `external-tasks/done/` verschoben werden, sobald mindestens zwei aufeinanderfolgende erwartete Cron-Slots wieder als `event=schedule` erscheinen oder eine andere eindeutige technische Ursache behoben und verifiziert ist.
