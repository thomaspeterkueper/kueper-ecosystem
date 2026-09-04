# KUEPER Control Room Dashboard

Der Control Room trennt zwei Ebenen bewusst:

- **Ecosystem**: fachliche Projekte, Wissensquellen, Archive, Websites und Anwendungen, die über Registry-Integrationen und External Tasks miteinander arbeiten.
- **Products**: eigenständige operative Anwendungen, die vom Ecosystem entwickelt oder beobachtet werden können, aber nicht als fachliche Knoten in den Ecosystem-Graph gehören.

## Datenquellen

Der Dashboard-Graph erfindet keine eigene Statuslogik. Er nutzt ausschließlich bestehende Quellen:

- `registry/projects.json` für Ecosystem-Projekte, Produktionslinks und deklarierte Integrationen,
- `registry/products.json` für eigenständige Produkte,
- `external-tasks/open/` der registrierten Projekte für aktive Request-Flüsse,
- GitHub Repository-/PR-Metadaten für Erreichbarkeit, Default Branch, letzten Push und offene PRs.

## Darstellung

Deklarierte Integrationen erscheinen als ruhige gerichtete Verbindungen. Offene Cross-Repo-Requests werden als hervorgehobene animierte Kanten darübergelegt. Ein Klick auf einen Projektknoten öffnet Detailinformationen sowie – falls registriert – einen Link zur realen Website und zum Repository.

Produkte werden separat angezeigt und erhalten keine künstlichen fachlichen Beziehungen zum Ecosystem.

## Nächste Ausbaustufen

Spätere Versionen können den Request-Trace um Worker-, Review-, PR- und Merge-Zustände aus der Control-Plane-Datenbank erweitern. Diese Erweiterung soll vorhandene Lifecycle-Daten visualisieren und keine zweite Request-State-Machine einführen.
