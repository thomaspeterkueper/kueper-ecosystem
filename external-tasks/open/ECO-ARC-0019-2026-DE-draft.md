---
signature: "ECO-ARC-0019-2026-DE"
title: "Mehrfach-Agenten-Zusammenarbeit — Protokoll für gleichzeitige Bearbeitung"
series: "ARC"
seriesNumber: 19
year: 2026
language: "DE"
version: "v1.0"
status: "ENTWURF"
accessLevel: 0
epistemicStatus: ["W"]
tags: ["Governance", "Multi-Agent", "Konfliktvermeidung", "Source-of-Truth", "Protokoll"]
relatedDocuments: ["ECO-ARC-0014-2026-DE", "ECO-ARC-0017-2026-DE"]
summary: "Protokoll für den Fall, dass mehrere Agenten-Sessions (unterschiedliche KI-Systeme oder Instanzen) gleichzeitig an denselben Ökosystem-Repositories arbeiten. Sechs Regeln: Herkunftskennzeichnung in Commits, verbindliches Read-before-Write, explizite Single-Source-of-Truth-Erklärung je Datentyp, Task-Claiming vor Bearbeitung, ein festes Konfliktauflösungsprinzip und ein Verfallsprozess für erkannte Altmuster. Anlass: unbemerkte Parallelarbeit zweier Agenten-Sessions am Lernmodul-Bestand des Knowledge Graph (learning/*.yaml vs. exports/kxf-learning-modules-0.1.json)."
---

# THE KUEPER ECOSYSTEM
## Architecture Decision Series

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## MEHRFACH-AGENTEN-ZUSAMMENARBEIT — PROTOKOLL FÜR GLEICHZEITIGE BEARBEITUNG

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| | |
|---|---|
| **Signatur:** | ECO-ARC-0019-2026-DE |
| **Version:** | 1.0 (Entwurf) |
| **Status:** | ENTWURF — zur Kanonisierung durch den Kurator |
| **Bezug:** | ECO-ARC-0014 (KD-Normierung), ECO-ARC-0017 (Domain-Granularität) — beide selbst Beispiele für Drift, die aus unabgestimmter Arbeit entstand |

**Kurator:** Thomas Peter Küper · Juli 2026

---

> **[KN-00] Kuratornotiz**
>
> *Anlass: Zwei unabhängige Agenten-Sessions (unterschiedliche KI-Systeme) arbeiten
> gleichzeitig am selben Repository, ohne voneinander zu wissen. Sichtbar geworden
> an `learning/*.yaml` versus `exports/kxf-learning-modules-0.1.json` — zwei
> parallele Register für Lernmodule, die auseinanderliefen: unterschiedliche
> `unlocks`-Listen für dasselbe Modul, eine Datei mit `layer: L3` bei einer
> L1-nummerierten ID, 22 von 32 Dateien auf einem längst migrierten Alt-Schema.
> Dieses Dokument verhindert, dass sich das wiederholt.*
>
> *— T.P.K.*

---

## I. Grundsatz `[W]`

**Mehrere Agenten dürfen gleichzeitig an einem Repository arbeiten. Sie müssen aber
so arbeiten, dass ein Dritter — Mensch oder Agent — aus dem Repository allein
rekonstruieren kann, wer wann was warum geändert hat, und welche von mehreren
konkurrierenden Datenquellen gerade gilt.**

Stille Parallelarbeit ohne diese Rekonstruierbarkeit ist die eigentliche Ursache
der Drift-Fälle dieser Session (KD/KNOW, Entity-Feldnamen, `learning/` vs.
`exports/`) — nicht böser Wille, sondern fehlende gegenseitige Sichtbarkeit.

---

## II. Sechs Regeln `[W]`

### 1. Herkunftskennzeichnung in Commits

Jeder Agent committet unter einer **stabilen, unterscheidbaren Identität**
(`git config user.name`/`user.email`), die die Art des Agenten erkennen lässt
(z. B. `claude-kg-agent`, `chatgpt-kg-agent`). Keine geteilten oder anonymen
Commit-Identitäten für automatisierte Agenten.

### 2. Verbindliches Read-before-Write

Vor jeder Änderung: den Remote-Stand frisch holen (nicht auf lokalem Cache
arbeiten), die Zieldatei(en) tatsächlich lesen, erst dann schreiben. Nach dem
Schreiben: gegen den zwischenzeitlich möglicherweise weitergewanderten Remote
rebasen, nicht blind pushen. Diese Regel ist nicht neu — sie war in diesem
Repository bereits impliziter Standard — wird hier aber erstmals explizit für
alle Agenten kanonisiert.

### 3. Explizite Single-Source-of-Truth-Erklärung je Datentyp

Für jeden Datentyp, der an mehr als einem Ort im Repository abgelegt werden
könnte (wie Lernmodule aktuell in `learning/*.yaml` **und**
`exports/kxf-learning-modules-0.1.json`), muss ein maschinenlesbarer Vermerk
existieren, welcher Ort **kanonisch** ist und welcher **abgeleitet**,
**veraltet** oder **verboten**. Ohne einen solchen Vermerk gilt: der Ort, den
Konsumenten (SSF, NOXIA, OTA) tatsächlich einlesen, ist automatisch kanonisch;
alle anderen Orte für denselben Datentyp sind bis zur Klärung als **veraltet**
zu behandeln, nicht als gleichberechtigte Zweitquelle.

### 4. Task-Claiming vor Bearbeitung

Vor Beginn substanzieller Arbeit an einem offenen `external-task` oder Request:
den Task mit `status: in_progress` und dem Agenten-Kennzeichen aus Regel 1
markieren, committen, **dann erst** arbeiten. Verhindert, dass zwei Agenten
denselben Task parallel und widersprüchlich bearbeiten.

### 5. Konfliktauflösungsprinzip

Bei widersprüchlichen Datenständen für denselben kanonischen Gegenstand (zwei
verschiedene `unlocks`-Listen für dasselbe Modul, zwei verschiedene
Domain-Zuordnungen etc.) gilt, sofern nicht anders vom Kurator entschieden:

1. Die Version, die sich auf einen **formalen Request** (external-task,
   `REQ:L3:*`) zurückführen lässt, geht der Version vor, die ohne
   nachvollziehbaren Auftrag entstand.
2. Bei zwei formal beauftragten, aber widersprüchlichen Versionen: **nicht
   automatisch mergen oder eine Seite stillschweigend bevorzugen** — als Konflikt
   an den Kurator eskalieren (analog zu den in dieser Session mehrfach genutzten
   Normierungsanfragen ans Ökosystem).
3. Nie beide Zustände nebeneinander stehen lassen, ohne den Widerspruch
   mindestens zu vermerken.

### 6. Verfallsprozess für erkannte Altmuster

Wird ein veraltetes Parallelmuster erkannt (wie `learning/`s 22 unmigrierte
Dateien), wird es **nicht** stillschweigend ignoriert oder einseitig gelöscht,
sondern als eigener, benannter Klärungs-Task an den Kurator gestellt — mit
Empfehlung, aber ohne eigenmächtige Entscheidung über Migration versus
Löschung versus Beibehaltung.

---

## III. Geltungsbereich `[W]`

Gilt für alle Repositories des KUEPER-Ökosystems, sobald mehr als eine
Agenten-Session in einem Zeitraum von wenigen Tagen produktiv daran schreibt.
Bei Einzel-Agenten-Betrieb (wie im Regelfall dieser Session) bleiben die
Regeln 2 (Read-before-Write) und 3 (Source-of-Truth-Erklärung) weiterhin
verbindlich — sie schützen auch gegen Drift zwischen aufeinanderfolgenden
Sessions desselben Agenten.

---

## IV. Offene Punkte `[OFFEN]`

| **Punkt** | **Status** |
|---|---|
| Technische Umsetzung der Source-of-Truth-Vermerke (Formatvorschlag: `registry/source-of-truth.json` je Repo) | [OFFEN] — Vorschlag, keine Festlegung |
| Automatisierte Prüfung (CI-Job, der Task-Claiming-Konflikte oder unvermerkte Parallelschreibung erkennt) | [OFFEN] |
| Rückwirkende Anwendung auf bereits bestehende Drift-Fälle (KD/KNOW, `learning/` vs. `exports/`) | [OFFEN] — läuft über die bereits gestellten Einzel-Klärungs-Tasks |

---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Revisionsverlauf**

| **Datum** | **Vermerk** |
|---|---|
| 2026-07-21 | v1.0 (Entwurf): Erstfassung nach Entdeckung paralleler, unabgestimmter Agenten-Arbeit am KG-Lernmodulbestand. Sechs Regeln: Herkunftskennzeichnung, Read-before-Write, Source-of-Truth-Erklärung, Task-Claiming, Konfliktauflösung, Altmuster-Verfallsprozess. |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*Für das KUEPER Ecosystem*

Signatur: ECO-ARC-0019-2026-DE
