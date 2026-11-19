# Ideenwerkstatt – sichere Erstintegration

Stand: 2026-11-19. Entwurf, keine Produktionsfreigabe.

- Read-only Route: `/dashboard/ideas`; 18 redaktionelle Einträge aus kueper.com Draft #31 als versionierter Snapshot.
- **Fail closed**: Nur mit `Authorization: Bearer <KUEPER_IDEAS_ADMIN_TOKEN>` und gesetzter serverseitiger Variable. Ohne Token keine Inhalte. Token niemals in Client-Code oder öffentlichen Links verwenden.
- Bestehende Dashboard-Authentifizierung konnte nicht als gesicherte Rollenprüfung bestätigt werden; daher bewusst **keine Navigation und keine allgemeine Freigabe**. Die endgültige Admin-Anbindung muss die vorhandene Identity-/Session-Infrastruktur nutzen.
- Keine neuen GitHub-Issues, keine External Tasks, keine automatische Veröffentlichung, keine produktiven Schreibfunktionen.
- Kein zweiter Datenspeicher: JSON ist ein **temporärer Snapshot**, nicht kanonisch. Vor Aktivierung GitHub-basierte Quelle und Berechtigungen definieren und den Snapshot durch einen serverseitig abgesicherten Read-Adapter ersetzen.
- Vor Merge: Build/Typecheck, Auth-Tests (`npm run test:ideas`: fehlender/falscher/richtiger Token, fehlendes/leeres Secret), Datenschutz- und Vercel-Deployment-Prüfung. Danach interne Navigation ergänzen.
- Quellen- und Doppelungsprüfung der Einträge erfolgt vor ihrer fachlichen Überführung; Ideen sind keine verifizierten wissenschaftlichen Aussagen.
