# Research Candidate Validation & Canon-Conflict-Loop

Status: V4  
Control Plane: `kueper-ecosystem`

## Zweck

V4 verbindet Research Candidates wieder mit den Projekten, ohne deren Source of Truth zu übernehmen. Ein Research Candidate wird gegen den aktuellen Stand des primären Consumer-Repositories geprüft. Nur konkrete, handlungsrelevante Folgen werden als External Tasks weitergegeben.

## Ablauf

```text
KG research/candidates/RES-*.md
        ↓
Candidate auf main vorhanden?
        ↓
Consumer-Repo aktuell klonen
        ↓
VALIDATE
  none | enrichment | verification | conflict
        ↓
none ─────────────→ Queue: validated-no-action
        ↓
Action gerechtfertigt
        ↓
External Task KG → zuständiges Projekt
        ↓
V1/V2 Project Loop
        ↓
Projekt entscheidet selbst über Kanon
```

## Klassifikation

- `none` — aktuell keine sinnvolle Folgeaktion.
- `enrichment` — Evidenz kann vorhandenes Material substanziell vertiefen.
- `verification` — eine bestehende Behauptung oder Annahme sollte überprüft werden.
- `conflict` — eine aktuelle Projektannahme kollidiert materiell mit stärkerer Evidenz und braucht eine bewusste Entscheidung.

Ein Konflikt bedeutet nicht automatisch, dass die Fiktion falsch ist. Bewusste Abweichung von Realität ist zulässig; V4 verlangt nur, dass sie als Entscheidung sichtbar wird, wenn sie relevant ist.

## Grenzen

Der Validator darf keine Canon-Dateien, Figuren, Worldbibles, Gameplay-Werte oder kanonischen KG-Strukturen verändern. Er erzeugt ausschließlich Requests an die fachlich zuständigen Projekte.

Triviale Fakten, reine Inspiration und ästhetische Vorschläge erzeugen keine Tasks.

## Takt

`.github/workflows/canon-conflict-loop.yml` läuft täglich nach dem Research-Loop und kann manuell gestartet werden. Standardmäßig werden höchstens drei Research Candidates pro Lauf geprüft; ein Candidate darf höchstens drei konkrete Consumer-Aktionen erzeugen.

## Ergebnis

Damit ist der geschlossene Wissenskreislauf erreicht:

`Projekt → Wissenslücke → Research → Candidate → Validation → Project Request → Projektentscheidung`

Der Mensch bleibt dort im Loop, wo aus Evidenz eine kreative, kanonische oder konzeptionelle Entscheidung wird.
