-- ECO-OPS-20261028-llm-fallback (Entscheidung Thomas, 14./15.11.2026):
-- eigene Tagesbudgets für die Ausweichmodelle über das Vercel AI Gateway.
-- Rein ergänzend: keine bestehende Zeile und keine Funktion wird geändert.
--   gateway        Claude Haiku 5.5 (low) und Gemini 3 Flash (medium/high auf Flash-Stufe)
--   gateway-heavy  Gemini 3 Flash als Ersatz für DeepSeek-Pro-Eskalationen
-- Zusammen höchstens 12 Aufrufe pro UTC-Tag, davon höchstens 2 für schwere Aufgaben.
insert into ecosystem.llm_budget_policy(provider, enabled, max_daily_calls, max_daily_pro_calls)
values ('gateway', true, 10, 0),
       ('gateway-heavy', true, 2, 0)
on conflict (provider) do nothing;
