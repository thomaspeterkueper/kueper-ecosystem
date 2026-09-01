# ECO-ARC — Reviewer Provider Outage Fallback (DRAFT)

Status: **proposed / not activated**
Date: 2026-09-01

## Anlass

Der Automated PR Review Agent ist aktuell technisch gesund bis zur Provider-
Ausführung, kann aber bei einem Provider-/Billing-Ausfall (z. B. HTTP 402)
keinen unabhängigen inhaltlichen Review liefern. Die Review-Queue darf in diesem
Zustand weder künstlich PASS erzeugen noch durch wiederholte Provider-Aufrufe
Kosten/Fehler verstärken.

## Ziel

Ein providerunabhängiger Fallback soll während eines Ausfalls ausschließlich
Deterministik und Transport-Sicherheit prüfen. Er darf niemals eine fachliche
Freigabe ersetzen.

## Vorgeschlagene Zustände

- `BLOCKED`: PR nicht OPEN, Head stimmt nicht mit der Queue überein oder Diff ist
  nicht deterministisch auflösbar. Keine Review-Ausführung.
- `DEFERRED_PROVIDER_UNAVAILABLE`: Head und Transport sind konsistent, aber der
  unabhängige Reviewer fehlt. Task bleibt `review_pending`.
- `PASS` und `CHANGES_REQUIRED`: weiterhin ausschließlich Ergebnis des normalen
  unabhängigen Reviewers. Der Fallback kann **keinen** dieser Zustände erzeugen.

Sensible Pfade (`.github/workflows/`, Migrationen, Governance/Decisions,
`research/candidates/`) bleiben bei Provider-Ausfall immer deferred und erhalten
keine Ersatzfreigabe.

## Vorbereiteter Code

`tools/review/provider_outage_preflight.py` implementiert nur die deterministische
Klassifikation und ist absichtlich nicht in `pr_review_agent_v04.py`, Scheduler,
Supabase-RPCs oder Workflow eingebunden. Die Tests beweisen, dass der Preflight
kein PASS erzeugt.

## Mögliche spätere Integration

Nach Owner-/Architekturfreigabe könnte v0.5 einen bekannten Provider-Ausfall vor
dem Modellaufruf erkennen, den Preflight ausführen und den Task mit einem
nicht-finalen Deferred-Grund belassen. Ein späterer gesunder Reviewer-Lauf würde
denselben exakten Head normal prüfen. Provider-Pause/Circuit-Breaking bleibt
zuständig für Retry-Zeitpunkte.

## Nicht Teil dieses Drafts

- kein alternativer LLM-Provider;
- keine neuen Secrets oder Kosten;
- keine Änderung an Review-PASS-Semantik;
- keine automatische Merge-Freigabe;
- keine Änderung an Research Evidence Gate;
- keine produktive Verdrahtung.
