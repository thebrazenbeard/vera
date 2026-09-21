create table public.brigit_coordination_events (
  event_id uuid primary key default gen_random_uuid(),
  event_sequence bigint generated always as identity unique,
  thread_key text not null,
  source_branch text not null,
  target_branch text null,
  event_type text not null check (event_type in ('STATUS','ISSUE','ACKNOWLEDGEMENT','REVIEW','DECISION','RESOLUTION')),
  status text not null check (status in ('DRAFT','READY_FOR_REVIEW','IN_PROGRESS','BLOCKED','DEGRADED','ACKNOWLEDGED','CHANGES_REQUESTED','APPROVED','RESOLVED','CANCELLED')),
  objective text not null,
  summary text not null,
  active_issue text null,
  requested_perspective text null,
  supersedes_event_id uuid null references public.brigit_coordination_events(event_id),
  acknowledges_event_id uuid null references public.brigit_coordination_events(event_id),
  payload jsonb not null default '{}'::jsonb,
  reference_data jsonb not null default '{}'::jsonb,
  record_time timestamptz not null default clock_timestamp()
);
comment on table public.brigit_coordination_events is 'Append-only operational coordination ledger for Brigit branches/workstreams. This is not identity memory, relationship memory, or authority over live consent and correction.';
create index brigit_coordination_ack_idx on public.brigit_coordination_events(acknowledges_event_id) where acknowledges_event_id is not null;
create index brigit_coordination_branch_idx on public.brigit_coordination_events(source_branch,target_branch,event_sequence desc);
create unique index brigit_coordination_one_successor_idx on public.brigit_coordination_events(supersedes_event_id) where supersedes_event_id is not null;
create index brigit_coordination_status_idx on public.brigit_coordination_events(status,event_sequence desc);
create index brigit_coordination_thread_sequence_idx on public.brigit_coordination_events(thread_key,event_sequence desc);

create or replace function public.assign_brigit_coordination_record_time()
returns trigger language plpgsql security definer set search_path='pg_catalog','public' as $$
begin new.record_time:=clock_timestamp(); return new; end; $$;
create or replace function public.block_brigit_coordination_mutation()
returns trigger language plpgsql security definer set search_path='pg_catalog' as $$
begin raise exception 'brigit_coordination_events is append-only; updates and deletes are not permitted'; end; $$;
create trigger brigit_coordination_assign_record_time before insert on public.brigit_coordination_events for each row execute function public.assign_brigit_coordination_record_time();
create trigger brigit_coordination_block_update before update on public.brigit_coordination_events for each row execute function public.block_brigit_coordination_mutation();
create trigger brigit_coordination_block_delete before delete on public.brigit_coordination_events for each row execute function public.block_brigit_coordination_mutation();

create view public.brigit_coordination_latest with (security_invoker=true) as
select distinct on(thread_key) * from public.brigit_coordination_events order by thread_key,event_sequence desc;
create view public.brigit_coordination_open_issues with (security_invoker=true) as
select * from public.brigit_coordination_latest where status in ('BLOCKED','DEGRADED','CHANGES_REQUESTED');

alter table public.brigit_coordination_events enable row level security;
create policy brigit_coordination_no_client_access on public.brigit_coordination_events for all to anon,authenticated using(false) with check(false);
revoke all on public.brigit_coordination_events from anon,authenticated;
grant select,insert on public.brigit_coordination_events to service_role;
grant usage,select on sequence public.brigit_coordination_events_event_sequence_seq to service_role;
revoke all on public.brigit_coordination_latest,public.brigit_coordination_open_issues from anon,authenticated;
grant select on public.brigit_coordination_latest,public.brigit_coordination_open_issues to service_role;