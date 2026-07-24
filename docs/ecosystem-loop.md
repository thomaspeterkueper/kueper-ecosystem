# Ecosystem Loop

Status: pilot  
Decision: `ECO-ARC-0019-2026-DE`

## Zweck

Der Ecosystem Loop beobachtet die registrierten KUEPER-Projekte, sammelt deren offene `external-tasks`, erzeugt daraus eine priorisierte Queue und prüft unmittelbar vor einer späteren Umsetzung, ob der zugrunde gelegte Repository-Stand noch aktuell ist.

Er ersetzt **nicht** den bestehenden Cross-Repository-Workflow. `external-tasks/open|done|rejected` bleibt der kanonische Request-Vertrag.

## Pilotumfang

Der Scanner beobachtet alle aktivierten Projekte aus `registry/projects.json`. `noxia` ist in `registry/loop-policy.json` als erstes Pilotprojekt markiert und wird in der Queue bevorzugt einsortiert.

Die aktuelle Stufe ist absichtlich read-only:

```text
Registry + GitHub
      │
      ▼
    Scan
      │
      ▼
   Triage
      │
      ▼
 loop-queue.json
      │
      ▼
  Preflight
      │
      ├── HEAD unverändert → eligible_for_dispatch
      │
      └── HEAD verändert   → rescan_and_replan
```

Noch **nicht** enthalten ist ein autonomer Code-Executor. Damit kann der regelmäßige Beobachtungs- und Planungsloop gefahrlos validiert werden, bevor Schreibrechte automatisiert werden.

## Execution Classes

External Tasks können optional enthalten:

```text
Execution Class: A
```

Bedeutung:

| Klasse | Bedeutung |
|---|---|
| `A` | lokal, grundsätzlich autonom ausführbar |
| `B` | projektübergreifende Koordination erforderlich |
| `C` | Owner-Entscheidung erforderlich |

Fehlt das Feld, behandelt der Loop den Task konservativ als `C`.

## Lokaler Aufruf

Voraussetzung: `GH_TOKEN` mit Leserechten auf die registrierten Repositories.

```bash
GH_TOKEN=... python3 tools/loop/loop.py scan --output loop-queue.json
```

Preflight für den ersten Queue-Eintrag:

```bash
GH_TOKEN=... python3 tools/loop/loop.py preflight --queue loop-queue.json --index 0
```

Exit-Code `3` bedeutet: Der Ziel-HEAD hat sich seit dem Scan verändert. Die Anforderung darf auf Basis dieses Plans nicht umgesetzt werden; zuerst neu scannen und planen.

## Automatischer Scan

`.github/workflows/ecosystem-loop-scan.yml` läuft stündlich sowie manuell über `workflow_dispatch`.

Er:

1. checkt das Ecosystem-Repository aus,
2. scannt alle registrierten Projekte,
3. validiert die erzeugte JSON-Queue,
4. schreibt eine kompakte GitHub-Actions-Summary,
5. lädt `loop-queue.json` als kurzlebiges Artifact hoch.

Der Workflow schreibt weder in Ziel-Repositories noch in den Default Branch.

## Sicherheitsinvarianten

1. Keine parallele Request-Infrastruktur neben `external-tasks`.
2. Kein Dispatch ohne frischen SHA-Preflight.
3. Unklassifizierte Tasks sind `C`, nicht `A`.
4. Pilotbetrieb vor systemweiter autonomer Ausführung.
5. Spätere automatische Änderungen ausschließlich PR-basiert; kein direkter Default-Branch-Write und kein Auto-Merge.

## Nächste Ausbaustufe

Nach der Beobachtung realer NOXIA-Tasks folgt ein PR-only Executor für explizit freigegebene Class-A-Aufgaben. Erst danach wird geprüft, ob weitere Projekte für autonome Ausführung freigeschaltet werden.
