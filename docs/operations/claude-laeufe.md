# Claude-Läufe und DeepSeek-Workflows im Hybridbetrieb

```
Stand:   13.11.2026, 21 Uhr – Hybridbetrieb (Thomas); davor 1.0.0: vollständige Ablösung, am selben Tag zurückgenommen
Version: 2.0.0
```

Thomas, 13.11.2026:
- „Mir ging es fast darum, die GitHub Action abzulösen, da ich denke, ein Lauf mit Claude ist intelligenter.“
- „Doppelung brauchen wir nicht, ergänzen wir lieber die fehlenden Elemente in der neuen Aufgabe. DeepSeek würde ich auch nicht abschalten, spätestens morgen Mittag sollten die GitHub Actions wieder laufen, dann können wir DeepSeek auch wieder nutzen, zumindest für einen Teil der Repos, vermutlich reicht DeepSeek für viele Aufgaben.“

## Arbeitsteilung

**DeepSeek (GitHub Actions) macht die Masse, Claude die Oberstufe.** Alle Workflows sind wieder aktiv, unverändert: Autonomous Loop (Routing, Ingest in den Task-Bus, Parked-Neubewertung), Agent Worker V7, Automated PR Review, Knowledge Research Loop, OTA Workqueue Research, Canon Conflict Loop, OTA Evidence Sweep.

| Arbeit | DeepSeek-Workflows | Claude-Läufe |
| --- | --- | --- |
| Routinetasks aus `external-tasks/open` | ja – über den Task-Bus | nur in den Fällen unten |
| Tasks, die DeepSeek nicht schafft | – | ja: gescheiterte, geparkte (nicht Owner), länger als 24 Std. unberührte |
| Bugs, Sicherheit, Priorität `high`/`critical` | ja | ja, wenn nach 6 Std. kein Branch/PR existiert |
| GitHub-Issues, Draft-PRs mit CI-Fehlern oder Konflikten | – | ja (früher Lauf „Ökosystem Requests abarbeiten“) |
| PR-Review | erstes Review | **zweites Review vor dem Merge** bei PRs von Agenten, die das erste Review bestanden haben oder länger als 6 Std. offen sind |
| Recherche-Loops | ja – täglich wie bisher | **Prüfung** der Recherche-Ergebnisse der letzten 24 Std. und Übernahme gescheiterter Recherche |

**Kollisionen vermeiden:** Claude fasst keinen Task an, für den ein Branch `agent/…` oder `claude/…` jünger als 6 Stunden existiert oder ein offener PR besteht, und keinen Task, den der Agent Worker gerade bearbeitet (Hinweis im Task oder Branch). Im Zweifel liegen lassen.

**Welche Repos wer:** vorerst keine feste Aufteilung nach Repo – die Regeln oben verteilen die Arbeit. Gibt Thomas eine Liste vor („diese Repos nur Claude“), wird sie hier eingetragen.

## Lauf 1: Ökosystem-Kreislauf (alle 3 Stunden, Claude)

1. **Überblick:** Für alle Projekte mit `enabled: true` in `registry/projects.json`: `external-tasks/open/`, `external-tasks/parked/`, offene Issues, offene PRs (GitHub-REST).
2. **Auswahl** (höchstens 3 Arbeiten): (a) Bugs, Sicherheit, CI-Fehler ohne Branch/PR seit 6 Std.; (b) Draft-PRs mit CI-Fehlern oder Merge-Konflikten auf `claude/…`-Branches weiterführen; (c) GitHub-Issues ohne verknüpften PR; (d) Tasks, die DeepSeek gescheitert oder geparkt (nicht Owner) hat, oder die seit 24 Std. unberührt sind. Übersprungen: „Claude-Status: wartet auf Thomas“, `KUEPER_PARK_OWNER`, offene `## Rückfrage` an Thomas.
3. **Bearbeiten** im Ziel-Repo nach dessen README/AGENTS/CLAUDE.md und `docs/cross-repository-workflow.md`, `docs/repository-roles.md`, `docs/source-of-truth.md`: Branch `claude/<task-id>`, kleine Commits, Tests. Fremde Source of Truth nie ändern – Bedarf anderswo als Umschlag in `.kueper/outbox/`.
4. **Übernehmen:** eigener Branch, nach grünen Prüfungen Merge (Thomas' Regel); für Repos in `registry/merge-gates.json` PR und Pflichtprüfungen. Task nach `external-tasks/done/` mit `Status: done`, `Erledigt`, `Umgesetzt`. Zu Großes nach `parked/` mit konkreter Rückfrage.
5. **Zweites Review** (höchstens 3): PRs von Agenten wie in der Tabelle; Kommentar mit Befund; bei Grün und ohne Bedenken mergen.
6. **Bericht** nur, wenn etwas getan wurde oder etwas auf Thomas wartet: höchstens 8 Zeilen.

## Lauf 2: Ökosystem-Recherche (täglich 07:13 Uhr, Claude)

Läuft nach den nächtlichen Recherche-Workflows (Actions-Zeiten in UTC: 03:23, 03:53, 05:23, sonntags 04:17 – in Berlin eine Stunde später) und prüft deren Ergebnisse:

1. Neue oder geänderte Research Candidates, Recherche-Ergebnisse und daraus entstandene Requests der letzten 24 Stunden (KG `research/`, OTA-Workqueue, Canon-Conflict-Requests) lesen.
2. **Prüfen:** Stimmen die Quellen (selbst öffnen), Daten und Evidenzstufen? Ist die epistemische Klasse richtig? Fiktion als Befund? Realwissen im OTA statt in KUE? Fehlen wichtige Gegenbelege?
3. **Handeln:** Fehler direkt im selben Branch-Verfahren korrigieren (Branch `claude/recherche-pruefung-<datum>`, Validierung des Repos, dann Merge) oder, wo die Source of Truth woanders liegt, als Umschlag in die Outbox; Kanon- und Philosophiefragen mit „Claude-Status: wartet auf Thomas“.
4. **Übernehmen, was gescheitert ist:** Hat ein Recherche-Workflow in den letzten 24 Std. einen Fehler gemeldet (Actions-Lauf rot), den betroffenen Schritt selbst ausführen – mit WebSearch/WebFetch statt Exa, Ergebnisse als Dateien im selben Format.
5. Höchstens 5 Prüfungen und 1 übernommener Schritt je Lauf. Bericht höchstens 6 Zeilen.

Regeln aus `docs/knowledge-research-loop.md` gelten unverändert.

## Rückweg und Anpassung

- DeepSeek-Workflows einzeln abschalten: `gh workflow disable <datei>`; dann übernimmt der entsprechende Claude-Lauf laut Tabelle – diese Datei anpassen.
- Claude-Läufe pausieren: in den geplanten Aufgaben von Claude.
- Der frühere Claude-Lauf „Ökosystem Requests abarbeiten“ (stündlich) ist in Lauf 1 aufgegangen und abgeschaltet.
