-- AI usage reasons may contain internal task/research context.
-- The Next.js control-room API already uses the service role, so direct anonymous
-- access to this projection is unnecessary.
revoke all on function public.kueper_ai_usage_dashboard() from public, anon, authenticated;
grant execute on function public.kueper_ai_usage_dashboard() to service_role;
