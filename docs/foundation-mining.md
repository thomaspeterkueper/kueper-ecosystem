# Foundation Mining — projektübergreifender Workflow

Status: Entwurf (vorgeschlagen mit `ECO-ARC-0038-2026-DE`; verbindlich erst nach dessen Annahme)  
Repository: `kueper-ecosystem`  
Betroffene Repositories: `kueper.com` (KUE), `kueper-knowledge-graph` (KG), `solarsciencefoundation` (SSF), `overtime-archive.org` (OTA), `noxiagame` (NOXIA), perspektivisch weitere Bestands-Repositories

## 1. Zweck

Foundation Mining bezeichnet das wiederkehrende Vorgehen, mit dem bereits
vorhandene Bestände eines Repositories — zuerst OTA und SSF — auf
wiederverwendbare reale Wissenschaft untersucht und in die KUE-Realgrundlage
überführt werden.

Auslöser ist ein beobachtetes Muster: OTA-Archive und SSF-Module enthalten
neben fiktionalen, didaktischen und projektspezifischen Aussagen auch real
prüfbare wissenschaftliche Aussagen. Ohne einen ausdrücklichen Weg in die
zuständige Grundlagenquelle entstehen dieselben Aussagen mehrfach — in
unterschiedlichen Fassungen, mit unterschiedlichem Geltungsanspruch und ohne
gemeinsamen Dedup-Stand.

Foundation Mining löst das nicht durch eine neue Wissensbasis, sondern durch
eine festgelegte Zuständigkeits- und Ableitungsrichtung.

## 2. Ableitungskette

```text
Primärliteratur → KUE-Realgrundlage → KG-Identität/Relation → SSF-Didaktik bzw. OTA/NOXIA-Anwendung
```

Die Kette beschreibt **Zuständigkeiten und Ableitungsrichtung**, keine Pflicht
zur linearen technischen Verarbeitung. Kein Glied muss auf ein anderes warten,
und kein Glied darf für ein anderes entscheiden. Sie sagt nur, worüber wer
entscheidet und wo eine Aussage kanonisch wird.

| Kettenglied | Rolle im Muster | Source of Truth |
|---|---|---|
| Primärliteratur | Externe Belegebene. Belege werden gesucht und zitiert, aber nicht „besessen" | extern; vor Prüfung nicht kanonisch |
| KUE-Realgrundlage | Werkneutrale wissenschaftliche Grundlagenpublikation; hier wird eine extrahierte Aussage als reale Wissenschaft kanonisch — oder verworfen | `kueper.com` (`KUE-SCI`); tritt später ein eigenes Knowledge-Base-Repository hinzu (`docs/source-of-truth.md` §8), übernimmt es dieses Glied |
| KG-Identität/Relation | Stabile Entitäten, IDs und Relationen für das, was die KUE-Realgrundlage kanonisch führt | `kueper-knowledge-graph` |
| SSF-Didaktik | Didaktische Transformation des realen Grundlagenbestands für Lernmodule, Lernpfade, Übungen | `solarsciencefoundation` |
| OTA-/NOXIA-Anwendung | Werkbezogene bzw. spielerische Anwendung; fiktionale Überhöhung und Werk-Setzung sind dort zulässig und gewollt | `overtime-archive.org`, `noxiagame` |

Wichtig: Die Kette beschreibt die **Ableitung von Inhalten**, nicht die
Autorität von Verweisen. Die Verweisrichtung aus `docs/system-map.md`
(„Governance → Graph → Archiv/Lernen/Anwendung") bleibt unverändert gültig.
Beide Richtungen widersprechen sich nicht: die eine sagt, wer Inhalte
ableitet, die andere, wer sich auf wen berufen darf.

## 3. Extraktionsvertrag

Foundation Mining bewertet Aussagen nach der etablierten epistemischen
Klassifikation des Research-Loops (`docs/knowledge-research-loop.md`), **bevor**
etwas extrahiert wird.

Extrahierbar sind:

- `[R]` real prüfbare Aussagen;
- `[R-Anker]` reale Anker fiktionaler Aussagen (nur der Anker, nicht die Setzung);
- `[T]` Modellprämissen und `[H]` extern testbare Hypothesen — ausschließlich
  mit dieser Kennzeichnung und nie als gesichertes Wissen;
- `[S]` Spekulation nur als offene Frage, nicht als Befund.

Nicht extrahierbar sind:

- `[F]` fiktionaler Kanon und `[W]` Werk-Setzungen;
- projektbezogene Parameter jeder Art: NOXIA-Balancing-Werte, Preise,
  Produktionsraten, Unlock-Zeitpunkte, spielinterne Kennzahlen;
- didaktische Vereinfachungen aus SSF-Modulen als wissenschaftliche Aussage;
- reine In-universe-Terminologie ohne realen Anker.

Eine didaktische Vereinfachung oder ein Balancing-Wert darf damit niemals über
den Umweg „Foundation Mining" zu kanonischer realer Wissenschaft werden.

## 4. Deduplizierung gegen den KUE-Kanon

Vor jeder Übernahme wird der bestehende KUE-Kanon auf dieselbe Aussage geprüft
(inhaltlich, nicht per String-Suche). Zulässige Ergebnisse sind:

1. **Referenz/Erweiterung** — die vorhandene KUE-Publikation deckt die Aussage
   bereits ab; es wird referenziert oder ergänzt, keine zweite Publikation
   angelegt.
2. **Neue Publikation** — die Aussage ist real, wiederverwendbar und im Kanon
   noch nicht vorhanden; die Dedup-Prüfung und ihr Ergebnis werden sichtbar
   festgehalten.
3. **Zurückweisung** — die Aussage ist projekt-, werk- oder balancing-spezifisch
   oder keine reale Wissenschaft; sie bleibt im Herkunfts-Repository.

Zwei KUE-Publikationen dürfen dieselbe wissenschaftliche Aussage nicht
konkurrierend führen. Wird eine Aussage ersetzt oder präzisiert, geschieht das
als ausdrückliche Ablösung, nicht als stiller Parallelbestand.

## 5. Herkunft und Nachvollziehbarkeit

- Eine aus fremden Beständen gewonnene KUE-Realgrundlage nennt die
  auslösenden Dokumente (z. B. OTA-Signatur, SSF-Modul-ID), damit spätere
  Grounding-Audits den Weg Primärliteratur → KUE nachvollziehen können.
- Foundation Mining **verändert, verschiebt oder löscht nichts** in OTA oder
  SSF. Dortige Aussagen behalten ihren Wortlaut und ihre Claim-Klasse.
- Die Quelle bleibt Referenz, nicht Mit-Kanon: mit der Übernahme nach KUE wird
  OTA bzw. SSF nicht Source of Truth für reale Wissenschaft.

## 6. Gates

- Mining-Ergebnisse sind **nicht-kanonisch**, bis das zuständige
  Source-of-Truth-Repository sie annimmt. `auto_canonicalize: false` und
  `auto_publish: false` aus `research/policy.json` bleiben in Kraft; eine
  Veröffentlichung in der KUE-SCI-Schicht ist review-gated.
- Benötigt eine Aussage zusätzliche externe Evidenz, gilt der bestehende
  Research-Weg (Queue → Candidate → Validation) nach `ECO-ARC-0021`/`0022`.
  Foundation Mining baut keinen zweiten Recherchepfad daneben.
- Alles, was ein anderes Repository ändern soll (KG-Identität, NOXIA-Impact,
  OTA-Revision), läuft als External Task nach `ECO-ARC-0006`. Es gibt keinen
  Fremd-Commit und keine automatische Fremdänderung.

## 7. Verhältnis zu den bestehenden Loops

```text
V3 Research-Loop          Lücke im Projekt → externe Recherche → KG-Candidate
Foundation Mining         vorhandener Bestand → Extraktion → KUE-Realgrundlage
V4 Validation             Candidate/Befund → Consumer-Request
V2 Routing                Cross-Repo-Bedarf → External Task
```

Beide Richtungen teilen dieselben Grenzen: nichts wird durch bloßes
Vorhandensein kanonisch, und jede Übernahme entscheidet das zuständige
Repository. Sie unterscheiden sich nur im Auslöser — Wissenslücke dort,
vorhandener Bestand hier.

## 8. Nicht Teil dieses Musters

- keine neue Quelle der Wahrheit, kein neuer Repository-Code, kein neuer
  Registry-Eintrag;
- keine Pflicht für OTA oder SSF, ihre Bestände umzustrukturieren;
- keine neue Automation, kein Schedule, kein neues Werkzeug im
  `kueper-ecosystem` (der Auslöser bleibt eine konkrete Mining-Runde des
  zuständigen Repositories);
- keine Aussage über die Reihenfolge, in der technisch verarbeitet wird.
