# Drive-Exchange- und Asset-Workshop-Standard

Status: verbindlich (`ECO-ARC-0039`)  
Stand: 2026-11-24  
Geltung: alle registrierten Repositories mit Google-Drive- oder Asset-/Spezifikations-Workflow

## 1. Zweck

Dieser Standard beschreibt Google Drive als repositoryübergreifende **Austausch- und Arbeitsfläche (Exchange/Workshop)**. Er legt fest, wie Entwürfe, Spezifikationen, Reviews, LLM-/Agent-Übergaben sowie echte Bild- und Arbeitsdaten gemeinsam bearbeitet werden, ohne die Source of Truth des jeweiligen Repositories zu verwässern.

Verbindlich ist die Entscheidung [`decisions/ECO-ARC-0039-2026-DE.md`](../decisions/ECO-ARC-0039-2026-DE.md). Dieses Dokument ist die operative Ausführung: Struktur, Promotion-Ablauf, Metadaten, Datenschutz und Auffindbarkeit.

Grundsatz:

> **Drive ist Werkstatt und Austausch, nicht Source of Truth.** Kanonisch wird ein Artefakt erst durch bewusste Übernahme in das zuständige Repository.

## 2. Rollen

| Fläche | Verantwortung | Source of Truth? |
| --- | --- | --- |
| Zuständiges Repository | Produktiver Code, Schemas, Migrations, freigegebene und optimierte Runtime-Assets, lokale fachliche Dokumentation, repo-eigene Tasks und Checkpoints | **ja**, im eigenen Zuständigkeitsbereich |
| Google Drive — Exchange/Workshop | Entwürfe, Spezifikationen, Reviews, LLM-/Agent-Übergaben, Referenzmaterial, hochauflösende Bilddaten, nicht produktive Asset-Varianten | **nein** |
| Google Drive — Spiegel | Lese- und Sicherungskopie kanonischer KUE-/OTA-Dokumente (`ECO-ARC-0037`, `status/drive-mirror.json`) | **nein** |
| Knowledge Graph | Kanonische semantische Entitäten, Relationen, IDs und Mappings | **ja**, für die semantische Ebene |

Regeln:

- Drive darf **keine** parallele Code-, Task-, Wissens-, Asset- oder KG-Wahrheit etablieren.
- Ein Drive-Artefakt wird nicht dadurch kanonisch, dass es in Drive liegt, verlinkt, in einem Chat erwähnt oder von einem Agenten erzeugt wurde.
- Der Knowledge Graph bleibt für kanonische semantische Entitäten und Relationen zuständig; Drive referenziert sie höchstens, definiert sie aber nicht.
- Der bestehende Drive-Spiegel ist ein anderer Anwendungsfall als der Exchange und wird nicht in diesen umgebaut.

## 3. Exchange-Struktur

Für Projekte mit Drive-Anbindung ist ein klar benannter Exchange-Bereich vorgesehen:

```text
<Projekt>/
└── Exchange/
    ├── incoming/          neu eingegangene, ungeprüfte Artefakte
    ├── specs/             Spezifikationen, Konzepte, Reviews, Übergaben
    ├── graphics/          Bild- und Asset-Arbeitsdaten
    │   ├── buildings/
    │   ├── vehicles/
    │   ├── spacecraft/
    │   ├── interiors/
    │   ├── maps/
    │   └── references/
    ├── reviewed/          freigegebene Artefakte vor/bei der Übernahme
    └── archive/           integrierte, verworfene oder überholte Varianten
```

Regeln:

- Der Bereich heißt eindeutig `Exchange` und liegt in einem für das Projekt erkennbaren Drive-Bereich.
- Die Unterstruktur darf projektspezifisch erweitert werden (z. B. weitere Asset-Kategorien). Für Projekte, die Gebäude, Fahrzeuge, Raumfahrzeuge, Innenräume oder Karten bearbeiten, sind die genannten Ordner der gemeinsame Ausgangspunkt.
- `incoming/` ist kein dauerhafter Ablageort. Neue Artefakte werden zeitnah triagiert.
- Bestehende Ablagen müssen nicht migriert oder umbenannt werden. Der konkrete `NOXIA/Exchange`-Ordner bleibt NOXIA-Arbeitsbereich.
- Die Struktur begründet keine öffentliche Sichtbarkeit. Zugriffsrechte richten sich nach Abschnitt 7.

## 4. Promotion-Lifecycle

```text
incoming -> specs/graphics -> reviewed -> Repository -> archive
```

### 4.1 Statuswerte

| Status | Bedeutung | Typische Ablage |
| --- | --- | --- |
| `incoming` | neu eingegangen, ungeprüft, noch keinem Ziel zugeordnet | `incoming/` |
| `review` | in Arbeit oder Begutachtung, noch nicht freigegeben | `specs/`, `graphics/<kategorie>/` |
| `reviewed` | fachlich/gestalterisch freigegeben; Übernahme ins Repository steht aus oder läuft | `reviewed/` |
| `integrated` | bewusst ins zuständige Repository übernommen; Commit/PR referenziert | `archive/` (oder aktiver Arbeitsordner mit Verweis) |
| `archived` | nicht mehr aktiv, aber für Provenienz oder Review aufbewahrt | `archive/` |
| `rejected` | verworfen/abgelehnt; Aufbewahrung nur, wenn Provenienz oder Review es verlangt | `archive/` |

Der Status steht im Metadaten-Header (Abschnitt 6). Ablage und Status sollen zusammenpassen; Abweichungen werden im Metadaten-Header begründet.

### 4.2 Ablauf

1. **Eingang (`incoming`)**
   - Artefakt in `incoming/` ablegen und Metadaten-Header bzw. `README.md` beginnen.
   - Noch keine Aussage über Kanonizität, Zielpfad oder Freigabe.

2. **Triage (`review`)**
   - Zuständiges Repository und Artefakttyp bestimmen.
   - Nach `specs/` oder `graphics/<kategorie>/` verschieben und Status auf `review` setzen.
   - Wenn keine Zuständigkeit oder kein Nutzen erkennbar ist: nach `archive/` verschieben (`archived` oder `rejected`).

3. **Review (`reviewed`)**
   - Inhalt, Format, Maßstab/Dimensionen, Rechte und offene Fragen prüfen.
   - Freigegebene Artefakte nach `reviewed/` verschieben und Status auf `reviewed` setzen.
   - Ein Drive-Review ersetzt **nicht** die Review-, Test- und Merge-Gates des Ziel-Repositories.

4. **Promotion vorbereiten**
   - Ziel-Repository, Zielpfad und gewünschte Form (Runtime-Asset, Spec, Dokument) festlegen.
   - Bei fremder Zuständigkeit: External Task unter `external-tasks/open/` im Ziel-Repository anlegen; keine Direktänderung.
   - Rechte, Lizenz und Datenschutz klären. Nur freigegebene, für die Anwendung optimierte Runtime-Assets sind zur Übernahme bestimmt.

5. **Übernahme (Repository)**
   - Bewusster Merge über den normalen Repository-Weg (Branch, PR, Checks).
   - Danach im Drive-Artefakt Ziel-Repository, Zielpfad und möglichst Commit/PR eintragen und Status auf `integrated` setzen.

6. **Archivierung (`archive`)**
   - Die Arbeitskopie nach `archive/` verschieben, sofern sie nicht weiterhin aktiv benötigt wird.
   - Überholte oder verworfene Varianten werden archiviert, nicht stillschweigend überschrieben, wenn sie für Provenienz oder Review relevant sind.
   - Wird eine integrierte Fassung weiterbearbeitet, entsteht eine neue Revision mit eigenem Status; die kanonische Fassung im Repository bleibt maßgeblich.

7. **Rückfluss**
   - Änderungen am kanonischen Artefakt erfolgen im Repository.
   - Die Drive-Kopie wird zur Referenz oder veraltet; sie wird nicht nachträglich zur kanonischen Quelle.
   - Soll eine neue Werkstatt-Runde beginnen, wird eine neue Revision angelegt und erneut durch den Lifecycle geführt.

### 4.3 Promotion-Gate

Nicht übernommen wird, wenn:

- der Status nicht `reviewed` ist,
- Rechte, Lizenz oder Datenschutz ungeklärt sind,
- das Ziel-Repository nicht zuständig ist,
- die Metadaten für die Übernahme nicht ausreichen,
- die Änderung eigentlich als External Task in ein fremdes Repository gehört.

## 5. Bild- und Assetdaten

Drive darf ausdrücklich echte Binär- und Bilddaten enthalten, insbesondere:

- PNG, WebP, JPEG, SVG und Renderings,
- Grundrisse, Draufsichten, Seiten-/Frontansichten,
- Maßstabs- und Dimensionsstudien,
- Referenzfotos,
- Fahrzeug-, Gebäude-, Raumfahrzeug- und Innenraumkonzepte,
- Textur-, Karten- und Visualvarianten,
- weitere Arbeitsformate, sofern Zugriffs-, Rechte- und Lizenzgrenzen geklärt sind.

Das Repository enthält dagegen nur die tatsächlich benötigten, freigegebenen und für die Anwendung optimierten Runtime-Assets.

Regeln:

- Hochauflösende Quelldaten, Varianten und Zwischenstände dürfen in Drive bleiben; ein Provenienzverweis im Repository kann genügen.
- Die Übernahme eines Bildes oder Assets ist ein bewusster Review-Schritt; es gibt keinen automatischen Binär-Transfer.
- Dateiformat, Auflösung, Kompression und Benennung des Runtime-Assets folgen den Regeln des Ziel-Repositories.
- Rechte und Lizenz müssen vor Übernahme und vor jeder Veröffentlichung geklärt sein. Unklare Rechte blockieren die Promotion.
- Referenzfotos und personenbezogene Bilddaten unterliegen Abschnitt 7.

## 6. Mindestmetadaten

Für Spezifikationen und relevante Asset-Sammlungen wird ein Metadaten-Header bzw. eine `README.md` empfohlen. Mindestens, soweit anwendbar, anzugeben sind:

| Feld | Inhalt |
| --- | --- |
| Titel / Objektname | Klarer Name der Spezifikation oder Sammlung |
| Object-ID | Stabile Objekt-/Projekt-ID, falls vorhanden |
| Repository | Zuständiges Repository |
| Status | `incoming`, `review`, `reviewed`, `integrated`, `archived` oder `rejected` |
| Datum / Revision | Datum und Revisionsstand |
| Quelle | Urheber, Quelle oder Generierungsquelle, soweit bekannt |
| Maßstab / Dimensionen | Maßstab bzw. Dimensionen, falls relevant |
| Repository target | Zielpfad im Repository, falls bereits bekannt |
| Integration | Commit/PR-Referenz nach Übernahme |
| Offene Fragen | Bekannte Unsicherheiten |

Vorlage:

```markdown
# <Titel / Objektname>

Object-ID: <stabile Objekt-/Projekt-ID, falls vorhanden>
Repository: <zuständiges Repository>
Status: <incoming | review | reviewed | integrated | archived | rejected>
Datum: <YYYY-MM-DD>
Revision: <v1, v2, ...>
Quelle: <Urheber / Quelle / Generierungsquelle, soweit bekannt>
Maßstab: <Maßstab bzw. Dimensionen, falls relevant>
Repository target: <Zielpfad, falls bekannt>
Integration: <Commit/PR-Referenz nach Übernahme>
Offene Fragen: <bekannte Unsicherheiten>
```

### 6.1 Beispiel-Asset

```text
graphics/vehicles/surface/cargo-rover/
├── concept-v1.png
├── concept-v2.png
├── top-view.png
├── side-view.png
├── dimensions.svg
└── README.md
```

Beispiel-Metadaten:

```markdown
# Cargo Rover

Object-ID: cargo_rover
Repository: noxiagame
World body: Moon
Status: reviewed
Datum: 2026-11-24
Revision: v2
Quelle: Konzeptskizze T.P.K., Zwischenstand
Maßstab: 1:1 reference
Runtime asset: not yet integrated
Repository target: public/assets/vehicles/cargo_rover/moon/
Integration: —
Offene Fragen: Reifendimensionen für Mondgravitation noch offen
```

`World body` und `Runtime asset` sind projektspezifische Zusatzfelder; sie ergänzen die Mindestmetadaten, ersetzen sie aber nicht.

## 7. Datenschutz und Zugriffsgrenzen

- Private oder sensible Forschungs-/Personendaten dürfen nur in dafür berechtigten Drive-Bereichen liegen.
- Die Zugriffsregeln des jeweiligen Projekts gelten auch für Drive-Arbeitsdaten, insbesondere `data_sensitivity` und `access_policy` in `registry/projects.json` sowie `ECO-ARC-0030` für private Manuskriptbestände.
- Öffentliche ECO-Indizes (README, Registry, Dashboard, Collector-Ausgaben) dürfen keine privaten Drive-Inhalte, privaten URLs oder vertrauliche Metadaten spiegeln.
- Ein Collector oder Dashboard darf höchstens freigegebene Metadaten/Referenzen indexieren. Drive-Bereiche werden nicht automatisch durchsucht oder gescrapt.
- Binärdaten werden nicht automatisch in öffentliche Repositories kopiert. Jede Übernahme ist ein bewusster Review-Schritt.
- External Tasks, Commit-Nachrichten und öffentliche Repositories enthalten keine privaten Drive-URLs, Zugangsdaten oder vertraulichen Metadaten.
- Secrets gehören nicht in geteilte Drive-Artefakte; maßgeblich ist [`docs/operations/SECRETS_INVENTORY.md`](operations/SECRETS_INVENTORY.md).
- Das Entziehen von Zugriff ersetzt keine Löschung. Aufbewahrung und Löschung folgen den Regeln des zuständigen Projekts; Provenienzrelevantes wird archiviert statt stillschweigend entfernt.

## 8. Auffindbarkeit und Checkpoint-Abstimmung

Der Standard ist mit dem Entwicklungscheckpoint-/Chat-Übergabestandard aus `EXT-NOXIA-ECO-20261124-001` abgestimmt: Der lokale Checkpoint bleibt der Einstieg, der Drive-Exchange-Block ergänzt ihn. Neue Chats und Agenten sollen ohne alte Chat-Historie erkennen können:

- ob ein Workstream einen Drive-Exchange nutzt,
- wo die freigegebenen Arbeitsartefakte liegen,
- welches Repository kanonisch zuständig ist,
- welcher Stand bereits integriert wurde.

Dafür hält der **lokale** Checkpoint des Workstreams einen Drive-Exchange-Block fest. Empfohlene Form:

```markdown
## Drive-Exchange
- Genutzt: ja | nein
- Exchange-Referenz: <stabile Referenz auf den freigegebenen Exchange-Bereich>
- Zuständiges Repository: <Repository / Code>
- Arbeitsartefakte: <Pfad und Status, Kurzliste>
- Zuletzt integriert: <Artefakt -> Repo-Pfad, Commit/PR>
- Offen: <nächste Promotion-Schritte / Unsicherheiten>
```

Regeln:

- Der Checkpoint bleibt im zuständigen Repository; ECO führt keine zweite Checkpoint- oder Task-Wahrheit.
- In öffentlichen Registern und Repositories steht nur eine freigegebene Referenz, keine private Drive-URL und keine vertrauliche Metadatenliste.
- Externe Tasks bleiben die kanonische Schnittstelle für Änderungen an fremden Repositories; der Drive-Exchange ersetzt sie nicht.
- Bis der Checkpoint-Standard aus `EXT-NOXIA-ECO-20261124-001` umgesetzt ist, darf dieselbe Information ersatzweise in `README.md`, `AGENTS.md` oder der lokalen Entwicklungsdokumentation stehen.

## 9. Rollout in den Repositories

Der Standard gilt als Governance repositoryübergreifend. Lokale Änderungen entstehen nur, wenn ein Repository tatsächlich einen Drive-Exchange nutzt oder einen Verweis für seine Agenten benötigt.

Adoptions-Checkliste für ein betroffenes Repository:

```text
□ Exchange-Bereich benannt (bestehender Ordner darf bleiben)
□ Zuständiges Repository und Promotion-Zielpfade geklärt
□ Metadaten-/README-Vorlage übernommen
□ Statuswerte und Promotion-Gate bekannt
□ Datenschutz-/Zugriffsgrenzen geprüft
□ Checkpoint verweist auf Exchange-Referenz und letzten Integrationsstand
□ Fremdzuständigkeit läuft über external-tasks/open/ im Ziel-Repository
```

Regeln:

- Kein Repository kopiert diesen Standard; es verweist auf `kueper-ecosystem`.
- Lokale Änderungen laufen über das jeweilige External-Task-Verfahren des Repositories.
- ECO führt keine zentrale Liste privater Drive-Ordner und keine Kopie lokaler Asset-Metadaten.
- Bestehende Drive-Nutzungen werden nicht rückwirkend kanonisiert oder zwangsmigriert.

## 10. Abgrenzung

Dieser Standard ist **nicht**:

- ein zweites Task- oder Checkpoint-System,
- eine Backup-Pflicht für Repositories,
- ein Ersatz für Repository-Review, Tests oder Merge-Gates,
- eine Erlaubnis, fremde Zuständigkeiten direkt zu ändern,
- eine Freigabe zur Veröffentlichung privater oder sensibler Daten,
- eine Aussage über konkrete Drive-Ordner-IDs oder Freigabeberechtigungen.
