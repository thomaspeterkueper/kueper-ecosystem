# Research Candidate Merge Gate

Status: Proposal / review required  
Scope: KUEPER Knowledge Research Loop  
Control Plane: `kueper-ecosystem`

## Anlass

Der aktuelle Research Executor erstellt nach bestandener struktureller Evidence-Validierung einen Pull Request im Knowledge Graph und kann unmittelbar danach `gh pr merge --auto` aktivieren, wenn `research/policy.json:auto_merge_candidates` gesetzt ist.

Damit sind zwei voneinander verschiedene Aussagen bislang nicht sauber getrennt:

1. **Candidate-tauglich:** Der Research-Lauf erfüllt die strukturellen Evidence-Regeln und darf als nicht-kanonisches Staging-Material in `research/candidates/` vorgeschlagen werden.
2. **Merge-tauglich:** Der konkrete PR-Head ist quellengeerdet, gegen den tatsächlichen Ausgangskontext geprüft und hat die notwendige Review-Kette auf genau diesem Head bestanden.

Die jüngsten OTA-Piloten haben gezeigt, dass ein Candidate formal ausreichend wirken kann, obwohl der deklarierte Ausgangstext nicht tatsächlich in die Recherche eingegangen ist. Ein Evidence Score darf deshalb kein Ersatz für Source Grounding oder Review sein.

## Ziel

Research Candidates bleiben ausdrücklich non-canonical, werden aber trotzdem erst dann automatisch mergefähig, wenn ein separater, nachweisbarer Merge-Gate-Vertrag erfüllt ist.

Der Research Executor selbst soll ausschließlich:

- Queue-Eintrag laden,
- erforderlichen Source-Kontext laden und pinnen,
- Recherche ausführen,
- Evidence-/Strukturregeln validieren,
- Candidate-Branch und PR erzeugen,
- Queue-Status auf `candidate-pr` setzen.

Er soll **keinen Merge unmittelbar nach PR-Erzeugung vormerken oder ausführen**.

## Fail-closed Merge-Gate

Ein späterer automatischer Merge eines Research Candidates darf nur erfolgen, wenn alle folgenden Bedingungen gleichzeitig erfüllt sind:

### G1 — Candidate bleibt non-canonical

Der PR verändert ausschließlich den für den Research-Eintrag erlaubten Pfad unter `research/candidates/`. Änderungen an kanonischen KG-Entitäten, Relationen, Mappings, Schemas oder externen Tasks sperren den Auto-Merge-Pfad.

### G2 — Source Grounding

Wenn das Evidenzprofil `require_source_path=true` verlangt, müssen vor der Recherche vorhanden und erfolgreich aufgelöst sein:

- `source_repository`
- `source_path`
- gepinnter `source_ref`
- erwarteter bzw. verifizierter `source_blob_sha`

Der geladene Blob muss exakt dem erwarteten Ausgangsdokument entsprechen. Fehlt einer dieser Nachweise oder schlägt das Laden fehl, wird der Research-Eintrag `needs-review`; es darf kein Candidate-PR als mergefähig gelten.

Für Profile ohne verpflichtenden Einzel-Source-Pfad bleibt die bestehende externe Evidence-Provenienz maßgeblich; `source_grounded` darf dort nicht künstlich behauptet werden.

### G3 — Evidence Gate

Die profilspezifischen Mindestwerte für Evidence Score, Quellenzahl, Domains, URLs, starke Quellentypen, Claim-Klassifikation, Aktualitäts- und Konfliktprüfung müssen erfüllt sein.

Der Evidence Score allein erzeugt keine Merge-Berechtigung.

### G4 — Automated PR Review auf aktuellem Head

Der Automated PR Review Agent muss für den **aktuellen PR-Head-SHA** ein Ergebnis `PASS` geliefert haben.

Ein Review eines älteren Heads ist ungültig. Ändert sich der Head, fällt der Gate-Zustand automatisch auf `review-required` zurück und die vorhandene Changed-Head-Re-Review-Kette muss erneut durchlaufen werden.

### G5 — Keine offenen Blocker

Kein `CHANGES_REQUIRED`, Security-/Governance-Blocker, Canon-Konflikt oder sonstiger expliziter Review-Blocker darf für den aktuellen Head offen sein.

### G6 — Merge ist ein separater Schritt

Research-Ausführung und Merge-Entscheidung werden technisch getrennt. Der Executor erzeugt den PR; ein späterer Reconciler/Promotion-Schritt darf nach Prüfung von G1–G5 den Merge freigeben.

Bis dieser Reconciler implementiert und getestet ist, gilt fail-closed:

> Research-Candidate-PRs werden nicht automatisch gemergt.

## Empfohlene Implementierung

### Phase A — sofortige Sicherung

- `research/policy.json:auto_merge_candidates` auf `false` setzen.
- Den `gh pr merge --auto`-Pfad aus `tools/research/execute.py` entfernen oder dauerhaft deaktivieren.
- Bei Profilen mit `require_source_path=true` das Fehlen des Source-Vertrags bereits vor Start des Research-Agenten hart ablehnen.
- Dokumentation anpassen: Evidence Gate = Candidate Gate, nicht Merge Gate.

### Phase B — expliziter Merge-Reconciler

Ein eigener, kleiner Reconciler liest offene Research-Candidate-PRs und prüft deterministisch:

1. erlaubte Dateipfade,
2. Source-Grounding-Metadaten,
3. Candidate-/Evidence-Status,
4. letzten Review-Status,
5. Bindung des Review-Ergebnisses an den aktuellen Head-SHA,
6. Abwesenheit offener Blocker.

Nur bei vollständigem PASS darf er eine Merge-Freigabe erzeugen. Die eigentliche Auto-Merge-Funktion bleibt separat konfigurierbar und standardmäßig aus.

## Akzeptanztests

Mindestens folgende Fälle müssen vor Aktivierung eines automatischen Merge-Reconcilers deterministisch getestet werden:

- hoher Evidence Score, aber fehlender Source-Pfad bei verpflichtendem Profil → **kein Merge / needs-review**
- Source-Pfad vorhanden, Blob-SHA stimmt nicht → **kein Merge / needs-review**
- Source Grounding + Evidence Gate bestanden, aber kein PR Review → **kein Merge**
- Review PASS auf altem Head, danach neuer Commit → **kein Merge bis Re-Review PASS**
- aktueller Head mit CHANGES_REQUIRED → **kein Merge**
- aktueller Head mit PASS, aber unerlaubte Dateiänderung → **kein Merge**
- aktueller Head erfüllt G1–G5 → **merge-eligible**, aber nur über den separaten Reconciler

## Nicht Teil dieses Vorschlags

- keine Kanonisierung von Research Candidates
- keine automatische Publikation nach OTA oder KUE-SCI
- keine Änderung von Branch Protection
- keine Änderung fachlicher Evidence-Schwellen
- keine Entscheidung darüber, welche Research-Inhalte in den Kanon übernommen werden

## Entscheidungspunkt

Vor Umsetzung von Phase A/B ist zu bestätigen, dass die Trennung

`Research Executor → Candidate PR → Review Gate → optionaler Merge Reconciler`

als verbindlicher Lifecycle für autonome Research Candidates gelten soll.
