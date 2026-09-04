# KUEPER Control Room Dashboard

Der Control Room trennt zwei Ebenen bewusst:

- **Ecosystem**: fachliche Projekte, Wissensquellen, Archive, Websites und Anwendungen, die über Registry-Integrationen und External Tasks miteinander arbeiten.
- **Products**: eigenständige operative Anwendungen, die vom Ecosystem entwickelt oder beobachtet werden können, aber nicht als fachliche Knoten in den Ecosystem-Graph gehören.

## Datenquellen

Der Dashboard-Graph erfindet keine eigene Statuslogik. Er nutzt ausschließlich bestehende Quellen:

- `registry/projects.json` für Ecosystem-Projekte, Produktionslinks und deklarierte Integrationen,
- `registry/products.json` für eigenständige Produkte,
- `external-tasks/open/` der registrierten Projekte für aktive Request-Flüsse,
- GitHub Repository-/PR-Metadaten für Erreichbarkeit, Default Branch, letzten Push und offene PRs,
- `ecosystem.tasks` in der Control-Plane-Datenbank für den operativen Request-Lifecycle.

## Darstellung

Deklarierte Integrationen erscheinen als ruhige gerichtete Verbindungen. Offene Cross-Repo-Requests werden als hervorgehobene animierte Kanten darübergelegt. Ein Klick auf einen Projektknoten öffnet Detailinformationen sowie – falls registriert – einen Link zur realen Website und zum Repository.

Produkte werden separat angezeigt und erhalten keine künstlichen fachlichen Beziehungen zum Ecosystem.

## Request Traces

Unter `/dashboard/traces` wird dieselbe Arbeit zusätzlich als reale Prozesskette dargestellt:

`Queue → Worker → PR → Review → Fix → Done`

Die Stufen werden aus vorhandenen Lifecycle-Feldern abgeleitet, unter anderem `created_at`, `claimed_at`, `started_at`, `pr_url`, `status`, `parent_task_id`, `root_task_id`, `blocked_reason` und `completed_at`. `REVIEW_FIX`-Tasks werden über ihre Parent-/Root-Beziehung in denselben Trace eingeordnet. Direkte PR-Reviews überspringen die Worker-Stufe sichtbar, statt einen Worker-Lauf zu erfinden.

Der Trace ist rein beobachtend und führt keine zweite State Machine ein.

## Deployment-Sicherheit

Die Trace-API läuft ausschließlich serverseitig. Für den Zugriff auf die Control-Plane wird `SUPABASE_SERVICE_ROLE_KEY` oder alternativ `SUPABASE_SECRET_KEY` als Server-Environment-Variable verwendet. Der Schlüssel darf niemals als `NEXT_PUBLIC_*` exponiert werden. Fehlt die Konfiguration, bleibt das Dashboard funktionsfähig und zeigt für die Trace-Seite einen klaren GitHub-only-Fallback.

## Weitere Ausbaustufen

Später können Scheduler-Runs, Provider-/Modell-Routing, Merge-Gates und detaillierte Review-Ereignisse ergänzt werden. Auch diese Erweiterungen sollen vorhandene operative Daten visualisieren und keine parallele Request-Logik etablieren.
