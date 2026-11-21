# PR-Freigabenachweise – lesender Pilot

Der tägliche Audit erfasst für offene PRs in NOXIA, Ecosystem, KG und SSF den aktuellen Head-SHA, Draft-Status, zuletzt abgegebene Reviews je Reviewer und Check-Runs. Fehlende unabhängige Zustimmung, rote oder ausstehende Checks und fehlende Daten werden sichtbar.

**Keine Freigabeautomatik:** `evidence_present_not_release_authorization` bedeutet ausdrücklich keine Merge-Erlaubnis. Die Prüfung ist ein Beobachtungspilot und setzt weder Branch-Protection-Regeln noch Review-Anforderungen durch. Sie prüft nicht alle möglichen externen Deployment-/Vercel-Checks, Security-Befunde, Supabase-RLS, Kanon- oder Architekturfreigaben. API-Pagination wird nur teilweise unterstützt; unvollständige Abfragen werden gemeldet. Für private Repositories ist ein read-only Token mit passenden Berechtigungen erforderlich.

**Vor einer produktiven verpflichtenden Freigabekette** separat entscheiden: zuständige Reviewer, Required Checks je Repository, Notfallpfad, Branch Protection/Rulesets, Kostenlimits, Kanonfreigabe und Deploy-Gates. Der Pilot ändert keine dieser Regeln.
