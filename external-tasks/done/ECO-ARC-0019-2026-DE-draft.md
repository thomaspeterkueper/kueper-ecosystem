---
signature: "ECO-ARC-0019-2026-DE"
title: "Mehrfach-Agenten-Zusammenarbeit — Protokoll für gleichzeitige Bearbeitung"
status: "RESOLVED-SUPERSEDED"
resolved_by: "ECO-ARC-0033-2026-DE"
resolution_date: "2026-09-07"
---

# Auflösung des kollidierenden Entwurfs

Dieser Entwurf wurde **nicht** unter `ECO-ARC-0019-2026-DE` kanonisiert, weil diese Signatur bereits durch die akzeptierte Entscheidung **„Autonome Ecosystem- und Project-Loops“** belegt ist.

Der weiterhin gültige Inhalt wurde gegen den aktuellen Stand des Ökosystems geprüft, veraltete Mechanismen wurden verworfen bzw. korrigiert und der konsolidierte Governance-Kern wurde als **`ECO-ARC-0033-2026-DE — Mehrfach-Agenten-Zusammenarbeit`** kanonisiert.

Wesentliche Korrekturen gegenüber dem Juli-Entwurf:

- Task-Claiming erfolgt heute über die zentrale Control Plane und deren Lease-/Runtime-Zustand, nicht über konkurrierende `status: in_progress`-Edits an External-Task-Dateien.
- Source of Truth wird explizit durch Governance/Registry/Entscheidung bestimmt; die Heuristik „was ein Konsument gerade liest, ist automatisch kanonisch“ wurde verworfen.
- Branch+PR, Direct-Main-Schutz, stale-HEAD `rescan-and-replan` und CI-/Review-Gates sind inzwischen produktive Governance und wurden in die neue Entscheidung integriert.
- Auditierbarkeit verlangt eine rekonstruierbare Agent-/Task-/PR-Herkunft, aber nicht zwingend eine eigene Git-Identität je KI-Modell.

Historischer Ursprung: Entwurf vom 21.07.2026 nach paralleler Agentenarbeit am Knowledge-Graph-Lernmodulbestand.
