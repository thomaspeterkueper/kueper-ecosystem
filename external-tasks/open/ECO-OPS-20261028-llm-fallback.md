---
id: ECO-OPS-20261028-llm-fallback
title: LLM-Fallback-Kette über das Vercel AI Gateway statt Warten bei 402/429
status: open
created: 2026-10-28
requested_by: T.P.K.
priority: high
estimated_effort: medium
type: operations / provider routing
---

# ECO-OPS-20261028-llm-fallback — LLM-Fallback-Kette über das Vercel AI Gateway

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** open
**Created:** 2026-10-28
**Type:** operations / provider routing

## Anlass

`config/provider-policy.json` (v3) kennt genau einen Anbieter: DeepSeek. `tools/worker/agent_worker.py` behandelt `402 Insufficient Balance` als `ProviderUnavailable` und stellt die Aufgabe für 6 Stunden zurück (21600 s), bei 429/503 für 30 Minuten. Es gibt keinen zweiten Weg. Im September sind 25 Recherche-Aufträge so gescheitert.

Das Vercel AI Gateway ist bereits im Einsatz (`AI_GATEWAY_API_KEY`, Research-Loop). Es leitet bei Störungen auf andere Anbieter um, nutzt eigene Schlüssel (BYOK) zuerst und berechnet keinen Aufschlag auf Token-Preise.

## Gewünschte Änderung

1. `provider-policy.json` → Version 4 mit `fallback_chain` je Komplexitätsstufe, z. B.:
   - low: `deepseek-v4-flash` → ein zweites günstiges Modell über das Gateway
   - medium/high: `deepseek-v4-pro` → ein Modell eines anderen Anbieters über das Gateway
   - `critical`/`SECURITY`: ohne Peak-Aufschub, mit Fallback
   Die konkreten Modell-IDs aus dem Gateway-Katalog wählen, nicht raten.
2. `provider_router.py`: Bei `ProviderUnavailable` zuerst die nächste Stufe der Kette versuchen; erst wenn die ganze Kette erschöpft ist, zurückstellen. Budget-Invarianten aus `docs/control-plane/llm-budget.md` bleiben gültig (eine Reservierung je tatsächlich verwendetem Anbieter).
3. Jede Antwort protokolliert `provider`, `model`, `fallback_depth`.
4. Tests in `test_provider_router.py`: 402 → Fallback, 429 → Fallback, ganze Kette leer → Zurückstellen wie bisher.
5. Dasselbe Muster für `tools/research/agent-with-exa.mjs` (Modell aus `research/policy.json`).

## Erwartetes Ergebnis

- Ein leeres DeepSeek-Guthaben hält weder Worker noch Recherche länger als einen Lauf auf.
- `fallback_depth > 0` ist im Control Room sichtbar (Anteil je Tag).

## Hinweise

- Owner-Handlung (Thomas): Guthabenwarnung bei DeepSeek und im AI Gateway einrichten; das Gateway-Guthaben ist vorab gekauft.
- noxiagame bekommt dasselbe für NPC-Gespräche über `docs/workstreams/hospitality.md` G-7.
