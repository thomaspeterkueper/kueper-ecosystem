---
id: ECO-OPS-20261028-llm-fallback
title: LLM-Fallback-Kette über das Vercel AI Gateway statt Warten bei 402/429
status: done
created: 2026-10-28
requested_by: T.P.K.
priority: high
estimated_effort: medium
type: operations / provider routing
---

# ECO-OPS-20261028-llm-fallback — LLM-Fallback-Kette über das Vercel AI Gateway

**Origin:** Ressourcen- und Redundanz-Analyse (Chat 28.10.2026)
**Target:** kueper-ecosystem
**Status:** done
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

## Stand 13.11.2026 (Ökosystem-Kreislauf, Claude)

Claude-Status: wartet auf Thomas

Die Lage hat sich mit der Ablösung durch Claude-Läufe (`docs/operations/claude-laeufe.md`, 13.11.2026) grundlegend geändert:

- `agent-worker-v7.yml` (nutzt `provider_router.py`) und die Recherche-Workflows `knowledge-research-loop.yml`, `ota-workqueue-research.yml`, `ota-evidence-sweep.yml`, `canon-conflict-loop.yml` sind abgeschaltet. Punkte 1–4 (Fallback in `provider_router.py`) hätten derzeit keinen aktiven Nutzer.
- Einziger aktiver DeepSeek-Nutzer ist der manuelle Workflow `targeted-research.yml`: Claude Code mit `ANTHROPIC_AUTH_TOKEN = DEEPSEEK_API_KEY` plus `agent-with-exa.mjs` über das AI Gateway (Modell `deepseek/deepseek-v4-flash-0731` aus `research/policy.json`). Punkt 5 beträfe also nur diesen manuellen Lauf.
- Nicht umgesetzt: Die Modellwahl je Stufe ist eine Kosten- und Anbieterentscheidung (Task: „nicht raten“), und `provider_router.py` umzubauen, solange niemand ihn aufruft, wäre Arbeit auf Vorrat.

## Rückfrage

Was soll mit dieser Task geschehen?

- **A – schließen:** Durch die Claude-Läufe überholt; nach `done/` mit Vermerk „überholt durch claude-laeufe.md“. Bei Rückkehr zu den DeepSeek-Workflows wieder öffnen.
- **B – nur Punkt 5:** Fallback-Kette nur für `agent-with-exa.mjs` (manuelle gezielte Recherche). Dann bitte das Ausweichmodell im AI Gateway nennen (z. B. ein Modell eines anderen Anbieters, das du freigibst).
- **C – vollständig:** wie beschrieben, obwohl `provider_router.py` derzeit ruht; ebenfalls mit Modellnamen je Stufe.

Antwort „A“, „B <Modell>“ oder „C <Modelle>“ genügt.


## Wieder geöffnet (13.11.2026)

Thomas, 13.11.2026: DeepSeek wird nicht abgeschaltet; die GitHub Actions laufen wieder und übernehmen einen Teil der Arbeit, Claude-Läufe ergänzen (`docs/operations/claude-laeufe.md`, Hybridbetrieb). Die Fallback-Kette ist damit wieder relevant. Die Rückfrage oben (A/B/C) ist hinfällig; offen bleibt nur die Wahl der Ausweichmodelle je Stufe – dafür „Claude-Status: wartet auf Thomas“.

## Entschieden (Thomas, 14.11.2026)

Ausweichmodelle über das Vercel AI Gateway (Preise laut Gateway-Katalog vom 14.11.2026, je 1 Mio. Tokens Ein-/Ausgabe):

| Stufe | Erstes Modell | Ausweichmodell |
|---|---|---|
| low | `deepseek-v4-flash` (0,13 $ / 0,26 $) | `anthropic/claude-haiku-5.5` (0,10 $ / 0,50 $) |
| medium, high, critical/SECURITY | `deepseek-v4-pro` (1,32 $ / 3,96 $) | `google/gemini-3-flash` (0,50 $ / 3,00 $) |

Hinweise für die Umsetzung (Claude, 14.11.2026):

- Der laufende Worker ist `tools/worker/agent_worker_v76.py` (nicht `agent_worker.py`); die Budget-Reservierung läuft über `kueper_claim_task_with_llm_budget` je Anbieter. Für den Anbieter `gateway` braucht es daher eine ergänzende Migration mit eigenem Tagesbudget – sonst antwortet die Reservierung mit `provider-budget-disabled`. Migration nur nach Freigabe anwenden.
- Repo-Aufgaben (Claude Code): `ANTHROPIC_BASE_URL=https://ai-gateway.vercel.sh`, `ANTHROPIC_AUTH_TOKEN=$AI_GATEWAY_API_KEY`, Modell-ID aus der Tabelle. Analyse-Aufgaben: OpenAI-kompatibel über `https://ai-gateway.vercel.sh/v1/chat/completions`.
- `agent-worker-v7.yml` braucht zusätzlich `AI_GATEWAY_API_KEY` (Secret existiert bereits, wird von den Recherche-Workflows genutzt).
- `research/policy.json`: `external_evidence.fallback_models: ["anthropic/claude-haiku-5.5"]` für `agent-with-exa.mjs`.

Freigabe Budget-Migration: Thomas, 15.11.2026


## Ergebnis (15.11.2026)

Status: done
Erledigt: 2026-11-15
Umgesetzt:

- `config/provider-policy.json` v4 mit `fallback_chain` (low → Haiku 5.5, medium/high → Gemini 3 Flash, Pro-Eskalation → Gemini 3 Flash über `gateway-heavy`); `provider_router.fallback_chain()`.
- Neuer Worker `tools/worker/agent_worker_v77.py` (V7.6 + Fallback): überspringt pausierte Anbieter schon vor dem Claim, versucht bei Budget-Ende den nächsten Anbieter, wechselt bei 402/429/503 mitten im Lauf auf das nächste Modell (eigene Reservierung über `kueper_reserve_llm_invocation`); erst wenn die ganze Kette erschöpft ist, wird wie bisher zurückgestellt. Ergebnisse tragen `provider`, `model`, `fallback_depth`. Claude Code läuft im Fallback über `https://ai-gateway.vercel.sh` (Anthropic-kompatibel), Analyse-Aufgaben über `/v1/chat/completions`.
- `agent-worker-v7.yml` startet V7.7 und bekommt `AI_GATEWAY_API_KEY`; ohne Schlüssel läuft V7.7 wie V7.6 (Warnung im Log).
- `agent-with-exa.mjs`: `providerOptions.gateway.models` aus `research/policy.json` → `fallback_models: ["anthropic/claude-haiku-5.5"]`.
- Migration `20261115040000_llm_fallback_gateway_budget.sql` angewendet: `gateway` 10/Tag, `gateway-heavy` 2/Tag (zusammen 12, davon 2 schwer).
- Tests: `test_provider_router.py` (+4), `test_agent_worker_v77.py` (12: 402 → Fallback, 429 → Fallback, Kette leer → Zurückstellen, Budget-Ende, Claim-Rennen u. a.).

Offen (Owner-Handlung, Thomas): Guthabenwarnung im AI Gateway einrichten. Live-Bewährung beim nächsten DeepSeek-Ausfall beobachten (Log-Hinweis „LLM fallback“).
