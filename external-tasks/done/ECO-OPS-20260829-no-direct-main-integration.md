# Ecosystem Ops: direkte Integration auf Default-Branches als Merge-Ersatz verhindern

**Origin:** KUEPER Arbeitsloop
**Target:** kueper-ecosystem
**Status:** done
**Created:** 2026-08-29
**Completed:** 2026-08-30
**Priority:** high

## Anlass

Im Knowledge-Graph-Repository wurde PR #38 (`[integrated] canonical NOXIA unlock learning-module identities`) am 2026-08-29 nicht normal gemergt. Der fachlich geprüfte Inhalt wurde wegen eines Connector-/GraphQL-Problems beim Ready-/Merge-Pfad direkt auf `main` integriert. Dieser Auftrag verhindert, dass ein solcher Merge-Ersatz im autonomen Worker erneut möglich ist.

## Umgesetzte Absicherung

Der Worker installiert jetzt in jedem temporären Repository-Clone einen fail-closed Git-`pre-push`-Guard für den tatsächlich aufgelösten Default-Branch.

Damit gilt:

1. Ein Push auf `refs/heads/<default-branch>` wird lokal vor dem Netzwerkzugriff abgewiesen.
2. Der Guard wirkt nicht nur für `worker.run()`-Aufrufe, sondern auch für Git-Kommandos, die der Coding-Agent selbst innerhalb des Clones startet.
3. Worker-gesteuerte explizite Refspecs werden zusätzlich vor Credential-Auswahl geprüft.
4. Normale Task-Branches und bestehende PR-Head-Branches bleiben schreibbar.
5. Der Agent-Prompt verbietet ausdrücklich Cherry-Pick, Nachbau oder sonstige direkte Integration auf den Default-Branch als Ersatz für einen blockierten Ready-/Merge-Schritt.
6. Der REVIEW_FIX-Pfad erhält dieselbe Absicherung; er darf ausschließlich den bestehenden PR-Head aktualisieren.
7. Die bestehende Trennung `KUEPER_BOT_TOKEN` / `KUEPER_WORKFLOW_TOKEN` bleibt unverändert.

## Deterministische Tests

`tools/worker/test_direct_main_guard.py` deckt insbesondere ab:

- Pre-push auf Default-Branch => blockiert.
- Push auf PR-/Task-Branch => erlaubt.
- explizite `HEAD:main`- bzw. `HEAD:refs/heads/main`-Refspec => blockiert.
- tatsächlich installierter Hook beendet einen Agent-artigen Default-Branch-Push mit Fehlercode 41.
- Draft/Ready/Merge-unavailable-Vertrag => ein Default-Branch-Ersatzwrite wird deterministisch abgewiesen.

Der Test ist in den Agent-Worker-Workflow aufgenommen und läuft zusammen mit Provider- und Credential-Policy-Tests.

## Betriebsregel

Wenn Ready/Merge technisch nicht möglich ist, bleibt der PR offen/draft bzw. review-/merge-blocked. Der technische Blocker wird sichtbar gehalten. Es erfolgt kein Cherry-Pick, kein Nachbauen derselben Änderungen auf dem Default-Branch und kein direkter Contents-/Git-Write als Merge-Ersatz.

Die bereits am 2026-08-29 integrierten KG-Identitäten werden nicht rückwirkend revertiert.
