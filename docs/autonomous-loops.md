# Autonome Loops im KUEPER Ecosystem

Status: V1  
Control Plane: `kueper-ecosystem`

## Ziel

Das Ecosystem soll nicht darauf warten, dass der Owner jedes Projekt manuell auffordert, neue Requests zu prüfen. Offene, kanonische External Tasks werden regelmäßig entdeckt, im aktuellen Zustand des zuständigen Ziel-Repositories neu bewertet und – sofern sinnvoll und ausreichend bestimmt – dort autonom bearbeitet.

## V1-Kreislauf

```text
OBSERVE
  Registry + aktuelle Default-Branch-HEADs + external-tasks/open
    ↓
SELECT
  Priorität → Alter → Task-ID
    ↓
PREFLIGHT
  Ziel-Repo frisch klonen → HEAD unmittelbar erneut prüfen
    ↓
RESCAN / REPLAN
  Request gegen aktuellen Repo-Stand neu bewerten
    ↓
ACT
  im Ziel-Repo implementieren
    ↓
VERIFY
  Tests / Build / Lint nach lokalen Repo-Regeln
    ↓
RESULT
  done oder parked + präzise Rückfrage
    ↓
PUBLISH
  Branch + PR
    ↓
MERGE GATE
  risikoarm: Auto-Merge nach Repo-Checks
  risikoreich: menschliche Review
    ↓
NEXT SWEEP
```

## Verantwortungsgrenzen

1. `kueper-ecosystem` ist Orchestrator, nicht fachliche Source of Truth.
2. Ein Task wird immer im Ziel-Repository bearbeitet.
3. Vor der Bearbeitung wird der aktuelle Default-Branch-HEAD zweimal geprüft. Hat er sich bewegt, lautet das Ergebnis `rescan-and-replan`; der alte Plan wird verworfen.
4. Ein Agent darf keine fehlende fachliche Entscheidung erfinden. In diesem Fall wird der Task `parked` und um `## Rückfrage` ergänzt.
5. Ein erfolgreich bearbeiteter Task wird im PR von `external-tasks/open/` nach `external-tasks/done/` verschoben und erhält `status: done`.
6. Änderungen an sensiblen Bereichen (`.github/`, Migrationen, Auth/Security, Infrastruktur, Lockfiles, Deployment-Konfiguration) werden niemals automatisch gemergt.
7. Andere Repositories werden aus einem Projekt-Checkout nicht direkt verändert.

## Selbst erzeugte Folge-Requests

Ein Projekt darf während seiner Arbeit neuen Bedarf erkennen. V1 erzwingt dabei weiterhin die Source-of-Truth-Grenze: Der Agent dokumentiert den Folgebedarf. Die nächste Ausbaustufe routet daraus automatisch einen kanonischen Task in die Inbox des zuständigen Ziel-Repositories.

Damit entsteht kein unkontrolliertes rekursives Schreiben zwischen Repositories.

## Agent-Adapter

V1 verwendet standardmäßig Codex CLI über:

```text
codex exec --full-auto
```

Die Ausführungsschicht ist über `KUEPER_AGENT_CMD` austauschbar. Das Request-Protokoll, die Registry und die Governance hängen daher nicht von einem bestimmten Modellanbieter ab.

## Einmalige Secrets

Der GitHub-Workflow benötigt zwei Repository-Secrets in `kueper-ecosystem`:

- `KUEPER_BOT_TOKEN`: Fine-grained GitHub Token oder GitHub-App-Token mit Contents/PR-Schreibrechten auf allen registrierten KUEPER-Repositories.
- `OPENAI_API_KEY`: API-Key für den autonomen Agentenlauf.

Secrets werden weder in Requests noch in Logs geschrieben.

## Takt

Der zentrale Sweep läuft einmal pro Stunde (`17 * * * *`) und kann zusätzlich manuell gestartet werden. Pro Sweep werden standardmäßig höchstens drei Tasks bearbeitet. Diese Grenze verhindert Task-Stürme und begrenzt Kosten; sie ist über `KUEPER_MAX_TASKS` konfigurierbar.

## Nächste Ausbaustufe

Nach Stabilisierung von V1:

1. automatisches Routing neu entdeckter Cross-Repo-Folgeaufgaben;
2. Knowledge-Expansion-Loop für Knowledge Graph / Universe / Romane;
3. multilingualer Research-Loop mit Evidenz- und Quellenbewertung;
4. Canon-Conflict-Loop: Realwissen ↔ Worldbuilding ↔ Manuskript/Spiel;
5. Budget-, Rekursions- und Relevanzgrenzen für autonome Wissensvertiefung.
