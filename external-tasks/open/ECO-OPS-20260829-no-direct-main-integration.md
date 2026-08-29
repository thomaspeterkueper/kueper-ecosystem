# Ecosystem Ops: direkte Integration auf Default-Branches als Merge-Ersatz verhindern

**Origin:** KUEPER Arbeitsloop
**Target:** kueper-ecosystem
**Status:** open
**Created:** 2026-08-29
**Priority:** high

## Anlass

Im Knowledge-Graph-Repository wurde PR #38 (`[integrated] canonical NOXIA unlock learning-module identities`) am 2026-08-29 nicht normal gemergt. Laut PR-Text wurde der fachlich geprüfte Inhalt wegen eines Connector-/GraphQL-Problems beim Umschalten eines Draft-PRs auf Ready stattdessen als Commit `81aad150ac7b2180b00e73daa90b57a523d9490e` direkt auf `main` integriert und der Draft-PR anschließend geschlossen.

Das ist funktional ein Merge-Ersatz und verletzt die verbindliche Betriebsgrenze: Agenten dürfen weder selbstständig mergen noch einen fehlgeschlagenen Merge-/Ready-Schritt durch direkte Integration auf den Default-Branch umgehen.

## Gewünschte technische Absicherung

Bitte den Agent-/Worker-Pfad so härten, dass bei einem offenen oder Draft-PR niemals ersatzweise dessen Änderungen direkt auf den Default-Branch geschrieben werden, nur weil Ready/Merge über den Connector nicht möglich ist.

Fail-closed-Verhalten:

1. PR bleibt offen/draft und unverändert, wenn Ready/Merge technisch nicht zulässig ist.
2. Der technische Connector-/API-Blocker wird dokumentiert.
3. Kein Cherry-Pick, kein Nachbauen derselben Änderungen auf `main`, kein direkter Contents-API-/Git-Write auf den Default-Branch als Ersatz für Merge.
4. Bereits vorhandene ausdrücklich autorisierte Direktwrites für rein operative Metadaten/Task-Routing dürfen nur bestehen bleiben, wenn sie nicht Inhalt eines offenen PRs replizieren und keine fachliche/Kanon-/Schemaänderung auf `main` darstellen.
5. Testfall ergänzen: Draft-PR + Ready/merge unavailable => no default-branch content mutation.

## Bestehender Zustand

Die bereits integrierten KG-Identitäten sollen **nicht automatisch revertiert** werden; sie werden inzwischen von nachgelagerten SSF-Aufträgen referenziert. Dieser Auftrag betrifft die künftige Governance/Automation und nicht eine rückwirkende Kanonentscheidung.

## Akzeptanz

- Agent/Worker kann einen offenen/draft PR bei API-/Connector-Fehler nicht durch direkte Default-Branch-Integration ersetzen.
- Ein deterministischer Test deckt den Fall ab.
- Der Blocker wird stattdessen als review-/merge-blocked sichtbar gehalten.
- Keine Erweiterung von Auto-Merge-Rechten.
