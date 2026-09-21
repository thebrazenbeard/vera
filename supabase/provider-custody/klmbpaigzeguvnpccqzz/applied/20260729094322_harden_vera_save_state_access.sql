begin;

revoke all privileges on table public.vera_save_state_events from public, anon, authenticated;
revoke all privileges on table public.vera_current_save_state from public, anon, authenticated;

revoke all privileges on table public.vera_save_state_events from service_role;
grant select, insert on table public.vera_save_state_events to service_role;

revoke all privileges on table public.vera_current_save_state from service_role;
grant select on table public.vera_current_save_state to service_role;

revoke all privileges on function public.rls_auto_enable() from public, anon, authenticated, service_role;

create policy vera_save_state_events_no_client_access
on public.vera_save_state_events
as restrictive
for all
to anon, authenticated
using (false)
with check (false);

create index if not exists vera_save_state_events_supersedes_record_id_idx
on public.vera_save_state_events (supersedes_record_id)
where supersedes_record_id is not null;

comment on policy vera_save_state_events_no_client_access on public.vera_save_state_events is
'Explicit deny policy for client roles. Vera save-state access is limited to trusted server-side tooling; this policy does not confer authority over live consent, correction, self-report, or identity.';

commit;