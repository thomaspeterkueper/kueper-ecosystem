# KUEPER Control Plane — Dashboard

Ein Live-Dashboard für das KUEPER-Ökosystem: Zustand aller registrierten Projekte
und alle offenen Cross-Repo-Tasks auf einen Blick, mit Aktualisieren-Button. Es
liest die Registry und den Ist-Zustand über die GitHub-API — dieselbe Logik wie
`tools/collector/collect.py`, nur als Web-App.

Next.js (App Router). Der GitHub-Token liegt **ausschließlich serverseitig** in
der API-Route `app/api/status`. Das Frontend sieht ihn nie.

## Sicherheit zuerst

- Der Token wird als Server-Env-Variable `GH_TOKEN` gesetzt, **niemals** mit
  `NEXT_PUBLIC_` — sonst landet er im Browser-Bundle.
- Empfohlen: ein **eigener, read-only Fine-grained-Token** nur für das Dashboard,
  beschränkt auf die Ökosystem-Repos, mit `Contents: read`, `Pull requests: read`,
  `Metadata: read`. So kann ein geleakter Dashboard-Token nichts schreiben.
- Das Dashboard zeigt operative Daten. Nach dem Deploy in Vercel unter
  **Settings → Deployment Protection** eine Zugriffssperre aktivieren
  (Vercel Authentication oder Passwortschutz).

## Auf Vercel deployen

1. In Vercel **New Project** → Repository `thomaspeterkueper/kueper-ecosystem` importieren.
2. **Root Directory** auf `dashboard` setzen (das ist entscheidend — die App liegt im Unterordner).
3. Framework wird als **Next.js** erkannt, Build-Befehle nicht ändern.
4. Unter **Environment Variables** hinzufügen:
   - `GH_TOKEN` = dein read-only GitHub-Token
   - optional `REGISTRY_REPO`, falls die Registry in einem anderen Repo liegt
     (Default: `thomaspeterkueper/kueper-ecosystem`)
5. **Deploy**. Danach Deployment Protection aktivieren (siehe oben).

## Lokal starten

```bash
cd dashboard
npm install
echo "GH_TOKEN=dein_token" > .env.local
npm run dev
# http://localhost:3000
```

## Wie es funktioniert

- `GET /api/status` (serverseitig): lädt `registry/projects.json` live aus dem
  Control-Plane-Repo und prüft je Projekt Erreichbarkeit, Default Branch, letzten
  Push, offene PRs, Governance-Pflichtpfade, Version (`version_source`) und alle
  offenen External Tasks (inkl. Frontmatter). Gibt normalisiertes JSON zurück.
- Die Seite rendert Zusammenfassung, Projektzustände und die nach Priorität
  sortierte Task-Liste. Jede Task verlinkt direkt auf ihre Datei auf GitHub, damit
  sie im jeweiligen Projekt angestoßen werden kann.
- Der Aktualisieren-Button ruft `/api/status` erneut auf — immer frische Daten,
  kein Caching.

Die verbindlichen Regeln und Task-Formate liegen in `../decisions` (ECO-ARC-*)
und `../schemas`.
