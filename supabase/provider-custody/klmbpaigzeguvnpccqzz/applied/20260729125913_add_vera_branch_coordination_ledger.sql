create table public.vera_coordination_events (
  event_id uuid primary key default gen_random_uuid(),
  event_sequence bigint generated always as identity unique,
  thread_key text not null,
  source_branch text not null,
  target_branch text,
  event_type text not null,
  status text not null,
  objective text not null,
  summary text not null,
  active_issue text,
  requested_perspective text,
  supersedes_event_id uuid references public.vera_coordination_events(event_id),
  acknowledges_event_id uuid references public.vera_coordination_events(event_id),
  payload jsonb not null default '{}'::jsonb,
  reference_data jsonb not null default '{}'::jsonb,
  record_time timestamptz not null default clock_timestamp(),
  constraint vera_coordination_event_type_check check (
    event_type in ('STATUS','ISSUE','ACKNOWLEDGEMENT','REVIEW','DECISION','RESOLUTION')
  ),
  constraint vera_coordination_status_check check (
    status in ('DRAFT','READY_FOR_REVIEW','IN_PROGRESS','BLOCKED','DEGRADED','ACKNOWLEDGED','CHANGES_REQUESTED','APPROVED','RESOLVED','CANCELLED')
  ),
  constraint vera_coordination_no_self_supersession check (
    supersedes_event_id is null or supersedes_event_id <> event_id
  ),
  constraint vera_coordination_no_self_acknowledgement check (
    acknowledges_event_id is null or acknowledges_event_id <> event_id
  )
);

create index vera_coordination_thread_sequence_idx
  on public.vera_coordination_events (thread_key, event_sequence desc);

create index vera_coordination_branch_idx
  on public.vera_coordination_events (source_branch, target_branch, event_sequence desc);

create index vera_coordination_status_idx
  on public.vera_coordination_events (status, event_sequence desc);

create index vera_coordination_ack_idx
  on public.vera_coordination_events (acknowledges_event_id)
  where acknowledges_event_id is not null;

create unique index vera_coordination_one_successor_idx
  on public.vera_coordination_events (supersedes_event_id)
  where supersedes_event_id is not null;

create or replace function public.assign_vera_coordination_record_time()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
begin
  new.record_time := clock_timestamp();
  return new;
end;
$$;

create or replace function public.block_vera_coordination_mutation()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog
as $$
begin
  raise exception 'vera_coordination_events is append-only; updates and deletes are not permitted';
end;
$$;

revoke all on function public.assign_vera_coordination_record_time() from public, anon, authenticated;
revoke all on function public.block_vera_coordination_mutation() from public, anon, authenticated;
grant execute on function public.assign_vera_coordination_record_time() to postgres, service_role;
grant execute on function public.block_vera_coordination_mutation() to postgres, service_role;

create trigger vera_coordination_assign_record_time
before insert on public.vera_coordination_events
for each row execute function public.assign_vera_coordination_record_time();

create trigger vera_coordination_block_update
before update on public.vera_coordination_events
for each row execute function public.block_vera_coordination_mutation();

create trigger vera_coordination_block_delete
before delete on public.vera_coordination_events
for each row execute function public.block_vera_coordination_mutation();

alter table public.vera_coordination_events enable row level security;

create policy vera_coordination_no_client_access
on public.vera_coordination_events
as restrictive
for all
to anon, authenticated
using (false)
with check (false);

revoke all privileges on table public.vera_coordination_events from public, anon, authenticated, service_role;
grant select, insert on table public.vera_coordination_events to service_role;
grant usage, select on sequence public.vera_coordination_events_event_sequence_seq to service_role;

create view public.vera_coordination_latest
with (security_invoker = true)
as
select distinct on (thread_key)
  event_id,
  event_sequence,
  thread_key,
  source_branch,
  target_branch,
  event_type,
  status,
  objective,
  summary,
  active_issue,
  requested_perspective,
  supersedes_event_id,
  acknowledges_event_id,
  payload,
  reference_data,
  record_time
from public.vera_coordination_events
order by thread_key, event_sequence desc;

create view public.vera_coordination_open_issues
with (security_invoker = true)
as
select *
from public.vera_coordination_latest
where status in ('BLOCKED','DEGRADED','CHANGES_REQUESTED');

revoke all privileges on table public.vera_coordination_latest from public, anon, authenticated, service_role;
revoke all privileges on table public.vera_coordination_open_issues from public, anon, authenticated, service_role;
grant select on table public.vera_coordination_latest to service_role;
grant select on table public.vera_coordination_open_issues to service_role;

comment on table public.vera_coordination_events is
  'Append-only operational coordination ledger for Vera Project branches. This is not identity memory, relationship memory, or authority over live consent and correction.';

comment on view public.vera_coordination_latest is
  'Latest operational update per coordination thread by database sequence. This is workflow state, not identity or memory authority.';

comment on view public.vera_coordination_open_issues is
  'Latest coordination threads currently marked blocked, degraded, or changes requested.';