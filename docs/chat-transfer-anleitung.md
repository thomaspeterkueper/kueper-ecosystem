# Wissen aus alten Chats ins KUEPER-Ecosystem transferieren

**Version:** 2.0  
**Stand:** 2026-08-30  
**Geltung:** alle KUEPER-Ecosystem-Projekte

## Zweck

Diese Anleitung beschreibt, wie Wissen aus älteren Chat-Sessions strukturiert in das KUEPER-Ecosystem überführt wird, ohne ungeprüfte Inhalte zu kanonisieren, bestehende Source-of-Truth-Grenzen zu verletzen oder Zugangsdaten unnötig offenzulegen.

Grundprinzip: **erst Bestand und Zielstruktur prüfen, dann klassifizieren, dann über External Tasks oder ausdrücklich zuständige Authoring-/Governance-Pfade übertragen.** Ein Chat ist keine Source of Truth.

## 0. Struktur-Check vor dem Transfer

Bevor Inhalte aus dem Chat übernommen werden:

1. Aktuellen Stand des betroffenen Ziel-Repositories und seines Default-Branches lesen.
2. `registry/projects.json`, vorhandene Governance-Dokumente und relevante Source-of-Truth-Regeln prüfen.
3. Prüfen, ob derselbe Inhalt bereits in GitHub, Google Drive oder einem anderen Arbeitsbestand existiert.
4. Auf Signatur-/ID-Lücken und Kollisionen achten. Eine vorhandene Signatur niemals stillschweigend neu verwenden.
5. Bei widersprüchlichen Ständen nicht raten: Konflikt als offenen Punkt oder Request dokumentieren.
6. Erst nach diesem Read-before-Write-Schritt entscheiden, was tatsächlich übertragen werden muss.

Google Drive und andere persönliche Arbeitsablagen können **Werkstatt** sein, sind aber nicht automatisch kanonisch. GitHub-Repositories bzw. die dort festgelegten Sources of Truth bestimmen den belastbaren Ecosystem-Zustand.

## 1. Arbeitsauftrag für einen alten Chat

Für eine alte Chat-Session kann sinngemäß folgender Auftrag verwendet werden:

> Lies den gesamten Chat und identifiziere alles, was kanonisch, strukturell, wissenschaftlich, werkbezogen oder für offene Entscheidungen relevant ist. Ordne jeden Fund dem zuständigen KUEPER-Projekt zu. Prüfe vor jeder Umsetzung den aktuellen Repository-Stand. Formuliere für projektübergreifende Übergaben External Tasks. Verworfene Ideen, Smalltalk und reine Debugging-Zwischenstände werden nicht übernommen. Widersprüche oder unklare Kanonfragen werden nicht geraten, sondern sichtbar geparkt.

Die konkrete Übertragung erfolgt anschließend mit den im Ecosystem verfügbaren autorisierten Werkzeugen. Zugangsdaten gehören nicht in Chattexte, Repository-Dateien, Commits oder Tasks.

## 2. Repo-Zuständigkeiten

### Noxia-Universum

| Inhalt | Repository | Code |
|---|---|---|
| Kanon, Worldbuilding, Charaktere, Kontinuität | `noxia-universe` | NXU |
| Manuskripte, Szenen, werkbezogenes Arbeitsmaterial | `buecherwelten` | BW |
| OTA-Archivdokumente | `overtime-archive.org` | OTA |
| Mishkenaz-Sprache, Grammatik, Lexikon | `mishkenaz.org` | MSH |
| NOXIA-Spiel | `noxiagame` | NOXIA |
| Solar Science Foundation | `solarsciencefoundation` | SSF |

### Andere Universen und Buchprojekte

| Inhalt | Repository | Code |
|---|---|---|
| Endia | `endia.de` | ENDIA |
| Zereya | `zereya.de` | ZEREYA |
| Davaru | `davaru.de` | DAVARU |
| Buchprojekte / private Authoring-Arbeit | `buecherwelten` | BW |

### Philosophie und Wissenschaft

| Inhalt | Repository | Code |
|---|---|---|
| AVI-Modell | `avi-modell` | AVI |
| Omnizedenz | `omnizedenz.org` | OMNI |
| Fluíde Hermeneutik | `fluide-hermeneutics.org` | FLHERM |
| Resonanz-Ethik | `resonanceethics.org` | RESETH |
| Kontrakomologie | `contracomology` | CONTRA |
| Wissenschaftliche Veröffentlichungs-/Grundlagenebene | `kueper.com` | KUE |

### Infrastruktur und Querschnitt

| Inhalt | Repository | Code |
|---|---|---|
| Governance, Standards, Registry, Orchestrierung | `kueper-ecosystem` | ECO |
| Wissens-/Identitätsgraph, Mappings | `kueper-knowledge-graph` | KG |
| Gemeinsames Archivschema | `kueper-archive-schema` | — |
| Autoren-Website | `thomas-kueper.de` | TKD |

Die Registry ist für die tatsächlich aktivierten Projekte maßgeblich. Diese Tabelle ist eine Arbeitsorientierung und ersetzt keine spätere Registry-Änderung.

## 3. Klassifikation jedes Fundes

Jeder relevante Fund wird einer der folgenden Kategorien zugeordnet:

- **Kanon/Primärdaten:** nur in der dafür festgelegten Source of Truth ändern.
- **Projektübergreifender Auftrag:** als External Task im Zielprojekt.
- **Werkstatt:** noch nicht kanonisches Material, das in einer ausdrücklich dafür vorgesehenen privaten Arbeitsablage bzw. Authoring-Schicht verbleibt.
- **Research Candidate:** externe Evidenz oder Hypothese; niemals automatisch kanonisieren.
- **Offene Entscheidung:** sichtbar parken/eskalieren; keine Annahme als Fakt.
- **Verwerfen:** Brainstorm, überholter Zwischenstand, reines Debugging oder explizit verworfene Idee.

## 4. External Tasks

Für projektübergreifende Übergaben bleibt `external-tasks` das kanonische Request-System.

Dateinamenskonvention:

```text
EXT-{QUELLE}-{ZIEL}-{YYYYMMDD}-{NNN}.md
```

Zielablage:

```text
external-tasks/open/
```

Vor dem Schreiben ist der aktuelle Ziel-Repository-Stand zu prüfen. Ein Task bleibt offen, bis das geforderte Ergebnis tatsächlich im Default-Branch integriert und verifiziert ist. Danach wird er nach `external-tasks/done/` überführt.

## 5. Zwei-Stufen-Zugriff

Wenn ein Transfer nicht über bereits verbundene, autorisierte Werkzeuge erfolgen kann, gilt das Zwei-Stufen-Prinzip:

1. **Read-only zuerst:** Repository-Struktur, Dateien und bestehende Regeln mit minimalen Leserechten prüfen.
2. **Write erst bei tatsächlicher Umsetzung:** Schreibrechte nur für die benötigten Repositories und nur so lange wie erforderlich bereitstellen.

Fine-grained Tokens sind gegenüber breit berechtigten klassischen Tokens zu bevorzugen. Rechte auf Contents, Actions, Workflows oder Administration dürfen nur vergeben werden, wenn die konkrete Operation sie benötigt.

**Sicherheitsregel:** Tokens, Passwörter, Service-Role-Keys und andere Secrets niemals in Klartext in Chatnachrichten, Tasks, Dokumente, Commit-Messages oder Quellcode schreiben. Wo verbundene Connectoren/Secrets zur Verfügung stehen, diese verwenden.

### 5a. Werkstatt statt vorschneller Kanonisierung

Nicht jedes wertvolle Chatergebnis gehört sofort in ein kanonisches Repository. Unfertige Szenen, Varianten, Notizen, visuelle Ideen oder noch nicht entschiedene Konzepte können in der vorgesehenen Werkstatt-/Authoring-Schicht verbleiben. Erst eine fachliche Entscheidung oder ein klarer Request führt zur Übernahme in eine kanonische Source of Truth.

## 6. Beziehungen und Folgewirkungen

Bei einer Übernahme nicht nur die neue Datei anlegen. Prüfen:

- Müssen `relatedDocuments`, Rückverweise oder Mappings **beidseitig** aktualisiert werden?
- Gibt es abhängige Repositories oder Consumer?
- Muss ein neuer External Task an ein anderes Projekt erzeugt werden?
- Ist eine Datenbank-/Knowledge-Graph-Aktualisierung erforderlich?
- Entsteht ein Konflikt mit einer bereits vorhandenen ID, Signatur oder Zeitlinie?

Automatische Folge-Requests dürfen nur aus belastbaren, bereits erkannten Abhängigkeiten entstehen; keine spekulative Request-Vermehrung.

## 7. Datenbanken und Supabase

Ein Chatergebnis ist nicht automatisch eine Datenbankmigration. Vor einer Änderung:

1. aktuelle Tabellen/Schema/Source-of-Truth prüfen,
2. feststellen, ob GitHub oder die Datenbank primär ist,
3. Änderung über den zuständigen Projektpfad durchführen,
4. Ergebnis mit einer Testabfrage verifizieren.

Keine SQL-Anweisung aus einem alten Chat ungeprüft gegen einen aktuellen Datenbestand ausführen.

## 8. Kontrolle vor dem Löschen eines Chats

Ein alter Chat kann erst als vollständig transferiert gelten, wenn bestätigt ist:

- relevante Inhalte wurden klassifiziert,
- Ziel-Repositories wurden gegen den aktuellen Stand geprüft,
- benötigte Tasks/Änderungen wurden erstellt,
- bereits umgesetzte Änderungen sind im Default-Branch vorhanden,
- offene Konflikte/Fragen sind sichtbar dokumentiert,
- notwendige Related-Documents-/Mapping-Updates wurden berücksichtigt,
- keine Zugangsdaten wurden im Transfermaterial hinterlassen.

Erst dann sollte der Chat gelöscht werden.

## 9. Kurzcheckliste

```text
□ Chat vollständig ausgewertet
□ aktuellen Repo-/Registry-Stand geprüft
□ Drive/GitHub-/Werkstatt-Diskrepanzen geprüft
□ Signatur-/ID-Kollisionen geprüft
□ Funde klassifiziert
□ Sources of Truth respektiert
□ External Tasks nur bei echten projektübergreifenden Übergaben erstellt
□ Read-only vor Write angewendet
□ keine Secrets im Klartext übertragen
□ Related Documents / Mappings beidseitig geprüft
□ Datenbankänderungen separat verifiziert
□ offene Fragen sichtbar geparkt
□ Ergebnis im Default-Branch bzw. zuständigen System verifiziert
```

## 10. Betriebsprinzip

Der Transferprozess ist kein einmaliges „Kopieren von Chatwissen“, sondern eine kontrollierte Reconciliation zwischen historischem Gespräch und aktuellem Ecosystem-Zustand. **Der aktuelle Repository-Zustand gewinnt gegenüber alten Chatannahmen.** Wenn der alte Chat eine inzwischen überholte Aussage enthält, wird sie nicht wieder eingeführt.