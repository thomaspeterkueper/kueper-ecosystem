# Sicherheitsbaseline der KUEPER-Repositories

```
Stand:   13.11.2026 – Baseline, Prüfwerkzeug und Vorlagen (ECO-OPS-20261028-security-baseline)
Pflege:  nach jedem Lauf von tools/ops/enable-security.sh; neue Repos in registry/projects.json
         oder config/security-baseline.json aufnehmen
Task:    ECO-OPS-20261028-security-baseline
```

Diese Datei beschreibt, welche kostenlose Secret-Erkennung und welche
Abhängigkeits-Warnungen jedes registrierte Repository haben soll, wie der
Ist-Zustand geprüft wird und wie Abweichungen in den wöchentlichen
Gesundheitsbericht gelangen.

## Zielbild

| Kontrolle | Öffentliche Repositories | Private Repositories | Kosten |
| --- | --- | --- | --- |
| Secret-Erkennung | GitHub Secret Scanning + Push-Schutz | `gitleaks` als PR-Workflow | öffentlich kostenlos; privat Actions-Minuten |
| Abhängigkeits-Warnungen | Dependabot-Alerts + Dependabot-Sicherheitsupdates | Dependabot-Alerts + Dependabot-Sicherheitsupdates | kostenlos für alle Repositories |
| Abhängigkeits-Versionsupdates | – | Dependabot-Versionsupdates oder Renovate | kostenlos |
| Code-Scanning | CodeQL im Standard-Setup | nicht verfügbar ohne GitHub Advanced Security | öffentlich kostenlos |

**Korrektur gegenüber der Task vom 28.10.2026:** Dependabot-Alerts und
Dependabot-Sicherheitsupdates sind seit 2022 für **alle** Repositories
kostenlos, auch für private. Das Skript aktiviert sie deshalb überall.
Secret Scanning und CodeQL bleiben öffentlichen Repositories vorbehalten;
private Repositories erhalten stattdessen `gitleaks` und
Dependabot-Versionsupdates.

## Repositories und Schutzmaßnahmen

Scope: alle aktivierten GitHub-Projekte aus `registry/projects.json` plus
`extra_repositories` aus `config/security-baseline.json`. Das sind derzeit
22 Repositories: 16 öffentliche und 6 private. Die Task nennt 23 Repositories;
ein weiteres, nicht registriertes Repository ist über diesen Scope nicht
erreichbar und muss zuerst in der Registry oder der Security-Konfiguration
ergänzt werden.

### Öffentliche Repositories

| Repository | Secret-Erkennung | Abhängigkeits-Warnungen | CodeQL | Automatisierung |
| --- | --- | --- | --- | --- |
| `thomaspeterkueper/avi-modell` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/contracomology` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/davaru.de` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/endia.de` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/fluide-hermeneutics.org` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/kueper-archive-schema` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/kueper-ecosystem` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/kueper.com` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/mishkenaz.org` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/noxiagame` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/omnizedenz.org` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/overtime-archive.org` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/resonanceethics.org` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/solarsciencefoundation` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/thomas-kueper.de` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |
| `thomaspeterkueper/zereya.de` | GitHub Secret Scanning + Push-Schutz | Dependabot-Alerts + Sicherheitsupdates | Standard-Setup | `tools/ops/enable-security.sh` |

### Private Repositories

| Repository | Secret-Erkennung | Abhängigkeits-Warnungen | Versionsupdates | Datei im Ziel-Repo |
| --- | --- | --- | --- | --- |
| `thomaspeterkueper/buecherwelten` | `gitleaks`-PR-Workflow | Dependabot-Alerts + Sicherheitsupdates | Dependabot oder Renovate | `.github/workflows/gitleaks.yml`, `.github/dependabot.yml` |
| `thomaspeterkueper/kueper-engineering` | `gitleaks`-PR-Workflow | Dependabot-Alerts + Sicherheitsupdates | Dependabot oder Renovate | `.github/workflows/gitleaks.yml`, `.github/dependabot.yml` |
| `thomaspeterkueper/kueper-knowledge-graph` | `gitleaks`-PR-Workflow | Dependabot-Alerts + Sicherheitsupdates | Dependabot oder Renovate | `.github/workflows/gitleaks.yml`, `.github/dependabot.yml` |
| `thomaspeterkueper/kueper-products` | `gitleaks`-PR-Workflow | Dependabot-Alerts + Sicherheitsupdates | Dependabot oder Renovate | `.github/workflows/gitleaks.yml`, `.github/dependabot.yml` |
| `thomaspeterkueper/noxia-realtime` | `gitleaks`-PR-Workflow | Dependabot-Alerts + Sicherheitsupdates | Dependabot oder Renovate | `.github/workflows/gitleaks.yml`, `.github/dependabot.yml` |
| `thomaspeterkueper/noxia-universe` | `gitleaks`-PR-Workflow | Dependabot-Alerts + Sicherheitsupdates | Dependabot oder Renovate | `.github/workflows/gitleaks.yml`, `.github/dependabot.yml` |

`noxia-realtime` ist nicht in `registry/projects.json` geführt, sondern als
`extra_repositories`-Eintrag in `config/security-baseline.json`. Sobald das
Repository eine reguläre Registry-Rolle erhält, kann der Extra-Eintrag
entfallen.

Für `kueper-knowledge-graph` (KG), `kueper-engineering` (ENG) und
`kueper-products` (PROD) wurden am 13.11.2026 Folge-Requests unter
`.kueper/outbox/` erzeugt. `buecherwelten` und `noxia-realtime` haben keinen
routbaren Zielcode; `noxia-universe` (NXU) lag außerhalb der
Drei-Follow-up-Grenze. Dort bleibt es bei der Owner-Handlung.

## Werkzeug

`tools/ops/enable-security.sh` prüft und aktiviert die Baseline über die
GitHub-API (`gh api`). Das Skript ist idempotent: Es schreibt nur, wenn der
Ist-Zustand vom Soll-Zustand abweicht. Es schreibt **keine Dateien** in
Ziel-Repositories und gibt niemals Token-Werte aus.

```bash
# Nur prüfen, Exit 1 bei Abweichung (für Berichte und CI)
GH_TOKEN=<admin-pat> tools/ops/enable-security.sh --check

# Soll-Zustand anwenden
GH_TOKEN=<admin-pat> tools/ops/enable-security.sh

# Maschinenlesbar für den wöchentlichen Gesundheitsbericht
GH_TOKEN=<admin-pat> tools/ops/enable-security.sh --check --json

# Tabelle für den Abschnitt "Letzter Lauf" dieser Datei
GH_TOKEN=<admin-pat> tools/ops/enable-security.sh --check --markdown
```

Der Token braucht Admin-Rechte auf den Ziel-Repositories sowie Lese-/Schreib-
Zugriff auf Dependabot-Alerts, Secret Scanning und Code-Scanning-Einstellungen.
Fehlende Rechte werden je Repository als Fehler gemeldet; die übrigen
Repositories werden weiter geprüft.

Exitcodes: `0` alles in Ordnung, `1` Abweichung oder Fehler, `2` Aufruf-,
Konfigurations- oder Authentifizierungsfehler.

Zustandswerte je Kontrolle: `enabled`, `present`, `disabled`, `missing`,
`unknown`, `error`, `advanced` (CodeQL Advanced Setup vorhanden),
`not_applicable` (z. B. CodeQL für ein Repository ohne analysierbare Sprachen)
und `skipped` (Push-Schutz bewusst nicht geprüft).

## Vorlagen für private Repositories

Die Control Plane schreibt die folgenden Dateien nicht in fremde
Repositories. Das Ziel-Repository übernimmt die Vorlage selbst oder erhält
einen External Task:

- `tools/ops/templates/gitleaks.yml` → `.github/workflows/gitleaks.yml`
  (PR-Scan und Scan des Default-Branches; `on.push.branches` an den
  tatsächlichen Default-Branch anpassen).
- `tools/ops/templates/dependabot.yml` → `.github/dependabot.yml`
  (Ökosysteme des Ziel-Repositories ergänzen).

Für Organisationen verlangt `gitleaks-action@v2` zusätzlich ein
`GITLEAKS_LICENSE`-Secret. Das persönliche Konto benötigt keine Lizenz.

## Integration in den wöchentlichen Gesundheitsbericht

`ECO-OPS-20261028-weekly-health` soll die Sicherheitslage in
`status/health-weekly.md` aufnehmen. Dafür liefert
`tools/ops/enable-security.sh --check --json` ein stabiles Dokument:

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-11-13T00:00:00+00:00",
  "mode": "check",
  "repositories": [
    {
      "repository": "thomaspeterkueper/kueper-ecosystem",
      "visibility": "public",
      "result": "ok",
      "controls": {
        "dependabot_alerts": {"state": "enabled", "detail": ""},
        "dependabot_security_updates": {"state": "enabled", "detail": ""},
        "secret_scanning": {"state": "enabled", "detail": ""},
        "push_protection": {"state": "enabled", "detail": ""},
        "codeql_default_setup": {"state": "enabled", "detail": "Suite default"},
        "gitleaks_workflow": {"state": "not_applicable", "detail": ""},
        "dependency_updates": {"state": "not_applicable", "detail": ""}
      }
    }
  ],
  "summary": {
    "repositories": 22,
    "public": 16,
    "private": 6,
    "unknown": 0,
    "ok": 22,
    "action_required": 0,
    "errors": 0
  }
}
```

Der Bericht soll mindestens auflisten:

- Repositories mit `result != "ok"` und die betroffenen Kontrollen,
- die Zähler `action_required` und `errors`,
- neue offene Funde gegenüber der Vorwoche. Dafür je Repository die
  offenen Alert-Zahlen abfragen:
  `GET /repos/{repo}/dependabot/alerts?state=open`,
  `GET /repos/{repo}/secret-scanning/alerts?state=open`,
  `GET /repos/{repo}/code-scanning/alerts?state=open`;
  `gitleaks`-Funde stehen in den Workflow-Läufen des Ziel-Repositories.
  Die Zahlen der Vorwoche werden im Bericht zwischengespeichert und
  verglichen.

## Letzter Lauf

```
Noch kein Lauf mit Admin-Token. Der Agentenlauf am 13.11.2026 hatte keinen
GitHub-Token; die Tabellen oben beschreiben den Soll-Zustand.
Nach dem ersten Lauf tools/ops/enable-security.sh --check --markdown
ausführen und die Ausgabe hier einsetzen.
```

## Offene Punkte

1. **Aktivierung ausführen:** `tools/ops/enable-security.sh --check` mit einem
   Admin-Token laufen lassen und Abweichungen abarbeiten. Ohne diesen Lauf ist
   die Baseline nur definiert, nicht nachgewiesen.
2. **Private Repositories:** `gitleaks`-Workflow und
   Dependabot-/Renovate-Konfiguration in den sechs privaten Repositories
   ergänzen (Vorlagen oben). Das ist ein Eingriff in die jeweilige
   Source of Truth und erfolgt dort, nicht in der Control Plane.
3. **23. Repository:** Die Task nennt 23 Repositories, Registry plus Extra
   ergeben 22. Das fehlende Repository in `registry/projects.json` oder
   `config/security-baseline.json` ergänzen.
4. **Weekly Health:** Sicherheitsabschnitt in `weekly-health.yml` aufnehmen
   (siehe oben).
