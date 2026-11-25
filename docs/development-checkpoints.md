# Entwicklungscheckpoints – auffindbarer Arbeitsstand je Repository

```
Stand:   25.11.2026 – erste Fassung (EXT-NOXIA-ECO-20261124-001, Claude-Lauf „Ökosystem-Kreislauf“)
Version: 1.0.0
Status:  gültig für alle registrierten Repositories; Einführung schrittweise (Abschnitt 7)
```

## 1. Zweck

Lange KI-Chats dürfen nicht die einzige Quelle für Entwürfe, Implementierungsstände und offene Arbeit sein. Ein neuer, berechtigter Chat oder Agent soll den aktuellen Stand eines Workstreams aus dem Repository selbst finden – ohne alte Chat-Historie.

Dieses Dokument legt dafür einen einheitlichen **Einstieg** und ein **Mindestformat** fest. Es schafft keine neue Aufgabenverwaltung.

## 2. Grundsätze

1. **Keine zweite Task-Wahrheit.** Offene Aufgaben bleiben, wo sie heute stehen: `external-tasks/` (Audit-Projektion der State Plane, ECO-ARC-0027), GitHub-Issues und PRs. Ein Checkpoint verweist auf sie, er kopiert sie nicht.
2. **Fachlich im zuständigen Repository.** Der Checkpoint eines Workstreams liegt im Repository, das für ihn Source of Truth ist (`docs/source-of-truth.md`). `kueper-ecosystem` hält nur diese Regel und die Abdeckungsübersicht (Abschnitt 6).
3. **Vorhandenes weiterverwenden.** Hat ein Repository schon eine Form (Teilprojekt-Dateien, Handoffs, Backlog), wird sie über den Einstieg referenziert, nicht umgebaut oder dupliziert.
4. **Belegter Stand statt Erinnerung.** Ein Checkpoint nennt Branch, PR und die zuletzt geprüfte Revision (Commit), nicht „fast fertig“.
5. **Vertraulichkeit.** Inhalte privater Repositories bleiben dort. Öffentliche Register – auch dieses Dokument – nennen für private Repositories nur, *ob* ein Einstieg besteht, keine Workstream-Titel, Inhalte oder privaten Links.

## 3. Einstieg

Jedes Repository mit laufender Entwicklungsarbeit hat **genau einen** Einstieg, in dieser Reihenfolge:

1. `docs/development/README.md` – bevorzugt, oder
2. ein Abschnitt `## Entwicklungsstand` in der `README.md`, der auf den vorhandenen Ort verweist (z. B. `docs/workstreams/`).

Der Einstieg listet die aktiven Workstreams mit je einer Zeile und einem Link auf ihren Checkpoint. Ein Repository ohne laufende Entwicklung (reine Inhalts- oder Archivrepos) braucht keinen Einstieg; seine offene Arbeit steht in `external-tasks/open/`.

`README.md`, `AGENTS.md` bzw. `CLAUDE.md` des Repositories verweisen – soweit vorhanden – mit einem Satz auf den Einstieg.

## 4. Checkpoint je Workstream

Ein Workstream ist eine zusammenhängende Arbeit, die über mehrere Sitzungen läuft. Sein Checkpoint (eigene Datei oder Abschnitt im Einstieg) enthält mindestens:

| Feld | Inhalt |
|---|---|
| Ziel | ein bis zwei Sätze, was am Ende gelten soll |
| Status | `geplant` · `implementiert` · `getestet` · `integriert` (Abschnitt 5) |
| Branch / PR | Arbeitsbranch und PR-Link, falls vorhanden |
| Letzte verifizierte Revision | Commit-Kürzel und Datum, an dem der Stand zuletzt geprüft wurde |
| Tests | welche Prüfungen laufen, mit welchem Ergebnis |
| Offene Schritte | Verweise auf Tasks, Issues oder PRs – keine eigene Aufgabenliste |
| Risiken / offene Fragen | inkl. Rückfragen an Thomas |
| Abschlusskriterien | woran „integriert“ erkannt wird |
| Maßgebliche Dokumente | Spezifikationen, Entscheidungen, Protokolle |

Vorlage:

```md
## <Workstream>

- Ziel: …
- Status: geplant | implementiert | getestet | integriert
- Branch / PR: `…` · #…
- Letzte verifizierte Revision: `abc1234` (JJJJ-MM-TT)
- Tests: …
- Offene Schritte: external-tasks/open/…, #…
- Risiken / offene Fragen: …
- Abschlusskriterien: …
- Maßgebliche Dokumente: …
```

## 5. Statusstufen und Pflege

- `geplant` – Ziel und Abschlusskriterien stehen, noch kein Code bzw. Text auf einem Branch.
- `implementiert` – Änderung liegt auf einem Branch oder PR, Prüfungen noch nicht vollständig grün.
- `getestet` – Prüfungen des Repositories grün für die genannte Revision.
- `integriert` – auf dem Default-Branch gemergt und dort geprüft. Danach wird der Workstream aus dem Einstieg entfernt oder als abgeschlossen markiert.

Der Checkpoint wird **bei jedem wesentlichen Arbeitsschritt im selben Commit** aktualisiert (neuer Branch, PR, Merge, Statuswechsel, neue offene Frage). Wer – Mensch, Claude-Lauf oder DeepSeek-Worker – einen Workstream fortsetzt, liest zuerst den Checkpoint.

## 6. Abdeckung (Inventur 25.11.2026)

Erhoben lesend über die Repository-Bäume der Default-Branches. Private Repositories nur mit Ja/Nein.

| Repository | Sichtbarkeit | Vorhandene Form | Einheitlicher Einstieg |
|---|---|---|---|
| `kueper-ecosystem` | öffentlich | `status/`-Berichte, `docs/operations/claude-laeufe.md` | ja – [`docs/development/README.md`](development/README.md) |
| `noxiagame` | privat | ja (Teilprojekt-Dateien je Chat) | Verweis aus README fehlt – Umschlag an NOXIA |
| `kueper-knowledge-graph` | privat | ja (Handoffs) | nein – Umschlag an KG |
| `solarsciencefoundation` | öffentlich | `docs/ROADMAP.md`, `docs/handoffs/` | nein – Umschlag an SSF |
| `kueper.com` | öffentlich | `docs/backlog/` | nein – Umschlag an KUE |
| `kueper-engineering` | privat | einzelne Handoff-Dateien | nein – bei nächster Entwicklungsarbeit |
| `buecherwelten` | privat | ja (Migrations-Checkpoints) | nein – bei nächster Entwicklungsarbeit |
| übrige registrierte Repositories | – | nur `external-tasks/` | nicht nötig, solange keine Entwicklung läuft |

## 7. Einführung

1. Diese Regel und der Pilot in `kueper-ecosystem` (`docs/development/README.md`).
2. Repositories mit laufender Entwicklung (NOXIA, KG, SSF, KUE) erhalten je einen Umschlag aus `.kueper/outbox/` und legen ihren Einstieg selbst an – fremde Source of Truth wird nicht von hier aus geändert.
3. Neue Projekte: Abschnitt „Entwicklungsstand“ in `docs/onboarding-template.md`.
4. Übrige Repositories: Einstieg bei der ersten Entwicklungsarbeit, die über eine Sitzung hinausgeht.

**Maschinelle Abdeckungsprüfung – bewusst noch nicht:** Der Collector (`tools/collector/collect.py`) läuft laut `status/README.md` in keinem Workflow, eine Prüfung dort bliebe wirkungslos. Der Governance-Sweep läuft täglich, legt aber für jeden neuen Fund automatisch einen Task an; eine Pflichtprüfung würde für jedes Repository ohne Einstieg einen Task erzeugen. Eine Erweiterung erfolgt erst, wenn die Einführung aus Schritt 2 abgeschlossen ist und entschieden ist, ob fehlende Einstiege als Befund gelten sollen.

## 8. Verhältnis zu anderen Regeln

- `docs/cross-repository-workflow.md` – Übergaben zwischen Repositories bleiben External Tasks.
- `docs/chat-transfer-anleitung.md` – Altchats werden weiter nach dieser Anleitung übertragen; der Checkpoint ist der Ort, an dem ein laufender Workstream danach weitergeführt wird.
- `docs/drive-exchange-standard.md` – Drive bleibt Werkstatt; ein Checkpoint darf auf ein Drive-Artefakt verweisen, macht es aber nicht kanonisch.
