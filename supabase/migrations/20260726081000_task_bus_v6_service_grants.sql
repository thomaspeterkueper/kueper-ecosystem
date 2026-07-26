-- KUEPER Ecosystem V6 — explicit server-side privileges.
-- RLS is still enabled; service_role is the trusted backend role used by PostgREST.

grant usage on schema public to service_role;
grant select, insert, update, delete on table public.tasks to service_role;
grant select, insert, update, delete on table public.task_dependencies to service_role;
grant select, insert, update, delete on table public.task_runs to service_role;
grant select, insert, update, delete on table public.task_events to service_role;
grant usage, select on sequence public.task_events_id_seq to service_role;

grant execute on function public.kueper_create_task(text,text,text,jsonb,text,uuid,uuid[],text,text,timestamptz,integer,text,text,text,text,numeric,numeric,jsonb) to service_role;
grant execute on function public.kueper_cancel_task(uuid,text) to service_role;
grant execute on function public.kueper_claim_task(text,integer,text,text[]) to service_role;
grant execute on function public.kueper_start_task(uuid,uuid) to service_role;
grant execute on function public.kueper_heartbeat_task(uuid,uuid,integer) to service_role;
grant execute on function public.kueper_complete_task(uuid,uuid,jsonb,text,text,bigint,bigint,numeric) to service_role;
grant execute on function public.kueper_fail_task(uuid,uuid,text,integer) to service_role;
grant execute on function public.kueper_park_task(uuid,uuid,text,boolean) to service_role;
grant execute on function public.kueper_requeue_parked_task(uuid) to service_role;
grant execute on function public.kueper_recover_expired_leases() to service_role;
