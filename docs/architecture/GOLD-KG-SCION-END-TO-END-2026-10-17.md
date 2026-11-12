# Gold across scales – End-to-End-Handoff / SCION-Eignungsprüfung

**Stand:** 2026-10-17
**Status:** reproduzierbarer Integrations-Audit; keine Freigabe zum SCION-Runtime-Einbau, keine Kanonentscheidung

## Bestehende Zuständigkeiten und Aufträge

- KUE: `KUE-SCI-0195-2026-DE` (naturwissenschaftliche Grundlagen; Publikations-/Text-Owner kueper.com)
- OTA: `OTA-SCI-0106-2026-DE` (Gold), `OTA-SCI-0107-2026-DE` (STAR), `OTA-SCI-0105-2026-DE` (CMS/LHCb, anderer Messgegenstand)
- KG: `external-tasks/open/KG-REQ-20261006-gold-across-scales.md`
- SSF: `external-tasks/open/SSF-REQ-20261006-gold-across-scales.md`
- OTA: `external-tasks/open/OTA-REQ-20261006-gold-across-scales.md`

Die Aufträge dürfen nicht durch neue parallele Requests vervielfacht werden. KG hält semantische Identitäten/Relationen/Metadaten; vollständige Dokumenttexte und lokale Autoren-/Lerninhalte bleiben in den entsprechenden Projekten.

## Aktueller Befund

KUE/OTA-Quelltexte sind vorhanden. Der Gold-KG-Auftrag und der darauf abhängige SSF-Auftrag sind **offen**. Der geprüfte KG-Verzeichnisbaum unter `documents/` enthält keine explizit benannte Gold-Dokumentreferenz; dies ist ein **Prüfhinweis**, noch kein Beweis, dass in exports oder relationalen Entitäten keinerlei Gold-Wissen existiert. Es wurde kein verifizierter automatischer Abschluss der Kette KUE/OTA → KG → SSF gefunden.

## End-to-End-Test, ohne neue Architektur

1. **Detect:** Bei Änderung an den vier Gold-Dokumenten den stabilen Dokument-ID-/Quellenbezug ermitteln.
2. **Deduplicate:** Bestehenden KG-Auftrag und bestehende KG-Entitäten/Exporte prüfen; keine neue semantische Gold-Entität erstellen, wenn eine passende kanonische existiert.
3. **Validate:** KG-Dokumentreferenzen (ID, contentOwner, version, sourcePath, status, provenance) und Beziehungen nach `docs/DOCUMENT-ARCHITECTURE.md` prüfen.
4. **Route:** Fehlende Daten als begründete Ergänzung im KG-Auftrag; KG-seitig erzeugte Änderung und Validierung abwarten.
5. **Handoff:** Erst danach SSF-Arbeitsauftrag mit tatsächlichen KG-IDs ergänzen; keine hartcodierten Ersatz-IDs und kein wissenschaftlicher Volltext-Duplikat.
6. **Verify:** Auflösbare KUE/OTA-Dokumentverweise, evidenztreue STAR/QCD-Abgrenzung, wiederholbarer KG-Export und SSF-Konsumtest. Negative Prüfung/Blocker ausdrücklich dokumentieren.

## KG-Curator-Finding (provisorisch)

- **Klasse:** `POSSIBLE_CROSS_PROJECT_IMPACT` + `MISSING_RELATION` (Letzteres erst nach vollständiger Exportsichtung bestätigbar)
- **Subject:** Gold/Au, `KUE-SCI-0195`, `OTA-SCI-0105/0106/0107`
- **Owner:** KG für Relations-/Registry-Korrektur, SSF für Didaktik
- **Risiko:** mittel: Wissenschafts-/Fiktionsvermischung, Duplikat-Entität, verfrühte SSF-Konsumation
- **Disposition:** bestehenden KG-Auftrag fortführen; **keinen** neuen autonomen Task erzeugen.

## SCION-Frage

SCION nur als möglicher Ausführungsadapter für **isolierte, bounded** Teilaufgaben evaluieren: pro Zielrepo ein agent/worktree, read-only Prüfung → Vorschlag/Diff → bestehende Validierung/Review/Owner-Gate. Keine Autonomie zur Schaffung wissenschaftlicher Fakten, Änderung von Kanon, Main-Merge oder zur Umgehung von source-of-truth-Vorgaben.

**Messgrößen eines SCION-Piloten gegenüber bestehendem Worker:** Zahl zuverlässig erkannter Dokumentänderungen; Duplikate; nicht auflösbare IDs; offene Übergaben; Zeit bis zur korrekt validierten Übergabe; Anzahl unbegründeter Änderungen; tatsächliche zusätzliche Ausführungskosten. Ein SCION-Mehrwert ist nur dann belegt, wenn er reproduzierbar eine bestehende Lücke schließt. Der bloße Name „SCION“ begründet keine Integration.

**Stop-Bedingungen:** unklare Projektberechtigung, unentscheidbare Eigentümerschaft, fehlende kanonische IDs, konkurrierende Änderungsaufträge, fehlende PR-/Review-Gates. Keine Laufzeitänderung vor Pilotfreigabe.
